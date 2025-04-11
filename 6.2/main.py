from web3 import AsyncWeb3, AsyncHTTPProvider
import asyncio
from datetime import datetime


rpc_uri = 'https://eth.drpc.org'
w3 = AsyncWeb3(AsyncHTTPProvider(rpc_uri))

while True:
    try:
        block_number = int(input('Введите номер блока: '))
        break
    except ValueError as e:
        print('Нужно ввести целое число')


async def is_connected() -> None:
    """ Функция проверки подключения к сети Ethereum Mainnet """
    if await w3.is_connected():
        pass
    else:
        print('Не удалось подключиться к сети Ethereum Mainnet. Проверьте введённый rpc_uri')
        await w3.provider.disconnect()
        exit()


async def get_block_info() -> None:
    """ Функция по номеру блока получает и выводит в консоль хэш блока, время создания и количество транзакций """
    block = await w3.eth.get_block(block_number)
    block_hash = block.hash.hex()
    create_time = datetime.fromtimestamp(block.timestamp)
    tx_count =  await w3.eth.get_block_transaction_count(block_number)
    print(f'Хэш блока: 0x{block_hash}')
    print(f'Время создания блока: {create_time}')
    print(f'Количество транзакций в блоке: {tx_count}')


async def main():
    await is_connected()
    await get_block_info()


try:
    asyncio.run(main())
except Exception as e:
    print(f'Непредвиденная ошибка: {str(e)}')



