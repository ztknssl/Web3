from web3 import AsyncWeb3, AsyncHTTPProvider
from config import rpc_uri
import asyncio
from logger import logger
import sys


if sys.platform:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# Тут, конечно, нужна регулярка для проверки прокси, а лучше отдельная функция валидации всех пользовательских вводов,
# но в данном случае решил упростить проверку
while True:
    wallet = input('Введите Ethereum-адрес: ')
    if len(wallet) == 42 and wallet.startswith('0x'):
        break
    else:
        logger.error('Неверный формат адреса кошелька')

while True:
    proxy = input('Введите URL прокси-сервера: ')
    if proxy.startswith('http://'):
        break
    else:
        logger.error('Неверный формат URL прокси-сервера')


# Устанавливаем параметры для подключения
request_kwargs = {
    'proxy': proxy,
    'timeout': 10
}

w3 = AsyncWeb3(AsyncHTTPProvider(endpoint_uri=rpc_uri, request_kwargs=request_kwargs))


async def display_balance(address: str) -> None:
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
        await display_balance(wallet)
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

