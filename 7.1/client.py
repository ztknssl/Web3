import asyncio
import aiohttp
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import TransactionNotFound
import os
from dotenv import load_dotenv
import config
from logger import logger

from web3.providers.rpc.utils import (
    REQUEST_RETRY_ALLOWLIST,
    ExceptionRetryConfiguration,
)

load_dotenv()


class Client:
    def __init__(self, private_key):
        self.private_key = private_key
        
        request_kwargs = {'proxy': f'http://{os.getenv("PROXY")}'}

        RPC_URI = config.RPC_URI
        if not RPC_URI:
            raise ValueError('RPC_URI не задан в config.py')

        self.rpc_url = RPC_URI

        EXPLORER_URL = config.EXPLORER_URL
        if not EXPLORER_URL:
            raise ValueError('EXPLORER_URL не задан в config.py')
        
        self.explorer_url = EXPLORER_URL
        self.eip_1559 = True

        self.w3 = AsyncWeb3(AsyncHTTPProvider(
            endpoint_uri=self.rpc_url,
            request_kwargs=request_kwargs,
            exception_retry_configuration=ExceptionRetryConfiguration(
                errors=(aiohttp.ClientError, asyncio.TimeoutError),
                retries=5,
                backoff_factor=0.125,
                method_allowlist=REQUEST_RETRY_ALLOWLIST,
            ),
        ))

        try:
            self.address = self.w3.to_checksum_address(
                self.w3.eth.account.from_key(self.private_key).address
            )
        except Exception as e:
            logger.exception("Ошибка при получении адреса из приватного ключа")
            raise

    def to_wei_custom(self, number: int | float, decimals: int):
        unit_name = {
            6: 'mwei',
            9: 'gwei',
            18: 'ether'
        }.get(decimals)

        if not unit_name:
            raise RuntimeError(f'Can not find unit with decimals: {decimals}')

        return self.w3.to_wei(number=number, unit=unit_name)

    async def get_priority_fee(self) -> int:
        try:
            fee_history = await self.w3.eth.fee_history(
                block_count=5, 
                newest_block='latest', 
                reward_percentiles=[80.0]
            )
            non_empty_block_priority_fees = [fee[0] for fee in fee_history['reward'] if fee[0] != 0]
            divisor_priority = max(len(non_empty_block_priority_fees), 1)
            priority_fee = int(round(sum(non_empty_block_priority_fees) / divisor_priority))
            return priority_fee
        except Exception as e:
            logger.exception("Ошибка при получении приоритетной комиссии")
            raise

    async def prepare_tx(self, address: str, value: int | float = 0):
        try:
            transaction = {
                'chainId': await self.w3.eth.chain_id,
                'nonce': await self.w3.eth.get_transaction_count(self.address, block_identifier='pending'),
                'from': self.address,
                'to': self.w3.to_checksum_address(address),
                'value': self.w3.to_wei(value, unit='ether'),
                'gasPrice': int((await self.w3.eth.gas_price) * 1.25)
            }

            if self.eip_1559:
                del transaction['gasPrice']

                base_fee = await self.w3.eth.gas_price
                max_priority_fee_per_gas = await self.get_priority_fee()
                if max_priority_fee_per_gas == 0:
                    max_priority_fee_per_gas = base_fee
                max_fee_per_gas = int(base_fee * 1.25 + max_priority_fee_per_gas)
                transaction['maxPriorityFeePerGas'] = max_priority_fee_per_gas
                transaction['maxFeePerGas'] = max_fee_per_gas
                transaction['type'] = '0x2'

            return transaction
        except Exception as e:
            logger.exception("Ошибка при подготовке транзакции")
            raise

    async def sign_and_send_tx(self, transaction):
        try:
            transaction['gas'] = int((await self.w3.eth.estimate_gas(transaction=transaction, block_identifier='pending')) * 1.5)
            logger.debug(f"Расчёт газа: {transaction['gas']}")

            signed_raw_tx = self.w3.eth.account.sign_transaction(transaction, self.private_key).raw_transaction
            logger.info("Транзакция подписана")

            tx_hash_bytes = await self.w3.eth.send_raw_transaction(signed_raw_tx)
            logger.info("Транзакция отправлена")

            return self.w3.to_hex(tx_hash_bytes)
        except Exception as e:
            logger.exception("Ошибка при подписании и отправке транзакции")
            raise

    async def wait_tx(self, tx_hash):
        total_time = 0
        timeout = 120
        poll_latency = 10
        try:
            while True:
                try:
                    receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
                    status = receipt.get('status')
                    if status == 1:
                        logger.success(f'✅ Успешно: {self.explorer_url}tx/{tx_hash}')
                        return True
                    elif status is None:
                        await asyncio.sleep(poll_latency)
                    else:
                        logger.warning(f'❌ Неуспешно: {self.explorer_url}tx/{tx_hash}')
                        return False
                except TransactionNotFound:
                    if total_time > timeout:
                        logger.warning(f'⏱ Транзакция не найдена через {timeout} сек.')
                        return False
                    total_time += poll_latency
                    await asyncio.sleep(poll_latency)
        except Exception as e:
            logger.exception("Ошибка при ожидании подтверждения транзакции")
            return False
