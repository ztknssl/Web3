from web3 import AsyncWeb3, AsyncHTTPProvider
from config import rpc_uri, wallets_list
import asyncio
from logger import logger
import sys


if sys.platform:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


w3 = AsyncWeb3(AsyncHTTPProvider(endpoint_uri=rpc_uri))


""" Функция display_balance получает на вход адрес кошелька, преобразует его в checksum и выводит баланс в консоль """
async def display_balance(wallet: str) -> None:
    try:
        balance = await w3.eth.get_balance(w3.to_checksum_address(wallet))
        eth_balance = w3.from_wei(balance, 'ether')
        logger.info(f'Адрес: {wallet}, Баланс: {eth_balance} ETH')
    except ValueError as e:
        logger.error(f'Неверный адрес кошелька {wallet}: {str(e)}')
    except Exception as e:
        logger.error(f'Ошибка при получении баланса для {wallet}: {str(e)}')


async def main():
    try:
        await asyncio.gather(*(display_balance(wallet) for wallet in wallets_list))
    except ConnectionError:
        logger.error('Ошибка подключения к сети Ethereum Mainnet')
    except ValueError as e:
        logger.error(f'Ошибка в формате данных: {str(e)}')
    except Exception as e:
        logger.error(f'Непредвиденная ошибка: {str(e)}')
    finally:
        await w3.provider.disconnect()


if __name__ == "__main__":
    asyncio.run(main())






