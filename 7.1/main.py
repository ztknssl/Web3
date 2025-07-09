import asyncio
from logger import logger
import sys
from client import Client


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


while True:
    PRIVATE_KEY = input('Введите приватный ключ отправителя: ')
    stripped_pk = PRIVATE_KEY.strip().replace('0x', '')
    if len(stripped_pk) == 64:
        break
    else:
        logger.error('Неверный формат приватного ключа отправителя')

client = Client(PRIVATE_KEY)

# while True:
#     sender_address = input('Введите адрес отправителя: ')
#     if client.w3.is_address(sender_address):
#         sender_address = client.w3.to_checksum_address(sender_address)
#         break
#     else:
#         logger.error('Неверный формат адреса кошелька отправителя')

while True:
    recipient_address = input('Введите адрес получателя: ')
    if client.w3.is_address(recipient_address):
        # recipient_address = client.w3.to_checksum_address(recipient_address)
        break
    else:
        logger.error('Неверный формат адреса кошелька получателя')


while True:
    try:
        value = float(input('Введите количество для отправки (ETH): '))
        break
    except TypeError as err:
        logger.error('Нужно ввести число!')

async def main() -> None:
    
    try:
        sender_address = client.address
        rec_address = client.w3.to_checksum_address(recipient_address)
        eth_balance = client.w3.from_wei(await client.w3.eth.get_balance(sender_address), 'ether')
        recv_eth_balance = client.w3.from_wei(await client.w3.eth.get_balance(rec_address), 'ether')
        print(f'Адрес отправителя: {sender_address}')              
        print(f'Баланс отправителя до: {eth_balance:.6f}')
        print(f'Баланс получателя до: {recv_eth_balance:.6f}')

        print('##################################################')
        
        transaction = await client.prepare_tx(rec_address, value)
        print(transaction)
        tx_hash_hex = await client.sign_and_send_tx(transaction)
        print(tx_hash_hex)

        await client.wait_tx(tx_hash=tx_hash_hex)

        eth_balance = client.w3.from_wei(await client.w3.eth.get_balance(sender_address), 'ether')
        recv_eth_balance = client.w3.from_wei(await client.w3.eth.get_balance(rec_address), 'ether')

        print(f'Баланс отправителя после: {eth_balance:.6f}')
        print(f'Баланс получателя после: {recv_eth_balance:.6f}')        


    except ConnectionError:
        logger.error('Ошибка подключения к сети Arbitrum')
    except ValueError as e:
        logger.error(f'Ошибка в формате данных: {str(e)}')
    except Exception as e:
        logger.error(f'Непредвиденная ошибка: {str(e)}')        
    finally:
        await client.w3.provider.disconnect()


try:
    asyncio.run(main())
except Exception as e:
    print(f'Непредвиденная ошибка: {str(e)}')