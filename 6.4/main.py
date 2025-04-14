from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.providers.rpc.utils import (
    REQUEST_RETRY_ALLOWLIST,
    ExceptionRetryConfiguration,
)
from config import rpc_uri
import asyncio
import aiohttp
from logger import logger
import sys


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


while True:
    proxy = input('Введите URL прокси-сервера: ')
    if proxy.startswith('http://'):
        break
    else:
        logger.error('Неверный формат URL прокси-сервера')


# Устанавливаем параметры для переподключения
w3 = AsyncWeb3(AsyncHTTPProvider(
    endpoint_uri=rpc_uri,
    request_kwargs={"proxy": proxy},
    exception_retry_configuration=ExceptionRetryConfiguration(
        errors=(aiohttp.ClientError, asyncio.TimeoutError),
        retries=5,
        backoff_factor=0.125,
        method_allowlist=REQUEST_RETRY_ALLOWLIST,
    ),
))


while True:
    wallet = input('Введите Ethereum-адрес: ')
    if w3.is_address(wallet):
        wallet = w3.to_checksum_address(wallet)
        break
    else:
        logger.error('Неверный формат адреса кошелька')


async def display_balance() -> None:
    """ Функция display_balance получает на вход адрес кошелька, преобразует в checksum и выводит баланс в консоль """
    try:
        balance = await w3.eth.get_balance(w3.to_checksum_address(wallet))
        eth_balance = w3.from_wei(balance, 'ether')
        logger.info(f'Баланс адреса {wallet}: {eth_balance:.3f} ETH')
    except ValueError as e:
        logger.error(f'Неверный адрес кошелька {wallet}: {str(e)}')
    except Exception as e:
        logger.error(f'Ошибка при получении баланса для {wallet}: {str(e)}')


async def is_connected() -> None:
    """ Функция проверки подключения к сети Ethereum Mainnet """
    if await w3.is_connected():
        logger.info('Подключение к сети Ethereum Mainnet установлено')
    else:
        logger.error('Не удалось подключиться к сети Ethereum Mainnet. Проверьте введённый rpc_uri')


async def main():
    try:
        await is_connected()
        await display_balance()
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

