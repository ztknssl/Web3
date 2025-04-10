# web3==7.10.0

from web3 import AsyncWeb3, AsyncHTTPProvider
import asyncio
import sys


if sys.platform:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


rpc_uri = 'https://linea.drpc.org'
w3 = AsyncWeb3(AsyncHTTPProvider(rpc_uri))

# Получение адреса кошелька и проверка правильности ввода
while True:
    address = input('Введите адрес кошелька: ')
    if len(address) == 42 and address.startswith('0x'):
        break
    else:
        print('Неверный формат адреса')


# Приведение введенного адреса к правильному виду
checksum_addr = w3.to_checksum_address(address)


async def is_connected() -> None:
    """ Функция проверки подключения к сети Linea """
    if await w3.is_connected():
        print('Подключение к сети Linea установлено')
    else:
        print('Не удалось подключиться к сети Linea. Проверьте введённый rpc_uri')

        # Не уверен, что так надо, но вылезала ошибка Unclosed client session, поэтому сначала закрываю сессию
        await w3.provider.disconnect()
        exit()


async def get_account_info()-> None:
    """ Функция получения количества транзакций и баланса кошелька """
    balance = await w3.eth.get_balance(checksum_addr)
    ether_balance = w3.from_wei(balance, 'ether')
    nonce = await w3.eth.get_transaction_count(checksum_addr)
    print(f'Количество транзакций на кошельке: {nonce} txs')
    print(f'Баланс кошелька: {ether_balance} ETH')


async def main()-> None:
    await is_connected()
    await get_account_info()


try:
    asyncio.run(main())
except Exception as e:
    print(f'Непредвиденная ошибка: {str(e)}')
