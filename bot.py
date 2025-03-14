import logging

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import sqlite3
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
import re
is_task_running = False
async def empty_task(chat_id, message):
    while is_task_running:
        print("getting balances")
        balances = await get_balance(chat_id)
        for balance in balances:
            print(balance)
            try:
                if float(balance[2])<10:
                    print("ТРЕВОГА")
                    await bot.send_message(chat_id=chat_id,text = "ТРЕВОГА, кошелек "+str(balance[0])+" ("+str(balance[1])+"), опустился ценой ниже 10 долларов, а именнно "+str(balance[2]))
                else:
                    print(float(balance[2]))
            except:
                print("Ошибка")
        print("sleep")
        await asyncio.sleep(1800)  # 1800 секунд = 30 минут
        logging.info(f"Выполнена фоновая задача для chat_id: {chat_id}")

def get_tron_balance_in_usd(wallet_address):
    # Шаг 1: Получаем баланс TRX через Trongrid API
    tron_api_url = f"https://api.trongrid.io/v1/accounts/{wallet_address}"
    response = requests.get(tron_api_url)

    if response.status_code != 200:
        return f"Ошибка: Не удалось получить данные для адреса {wallet_address}"

    data = response.json()
    if not data.get("data") or not data["data"][0].get("balance"):
        return f"Ошибка: Баланс не найден для адреса {wallet_address}"

    # Баланс в SUN (1 TRX = 1_000_000 SUN)
    balance_sun = int(data["data"][0]["balance"])
    balance_trx = balance_sun / 1_000_000  # Конвертируем SUN в TRX

    # Шаг 2: Получаем текущую цену TRX в USD через CoinGecko API
    coingecko_url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "tron",
        "vs_currencies": "usd"
    }
    response = requests.get(coingecko_url, params=params)

    if response.status_code != 200:
        return "Ошибка: Не удалось получить цену TRX"

    price_data = response.json()
    trx_price_usd = price_data.get("tron", {}).get("usd")
    if not trx_price_usd:
        return "Ошибка: Цена TRX не найдена"

    # Шаг 3: Рассчитываем баланс в USD
    balance_usd = balance_trx * trx_price_usd
    return balance_usd


def extract_all_values(text):
  """Извлекает все значения после $ до первого пробела."""
  matches = re.findall(r'\$(\S+)(?=\s)', text)
  return matches

# def get_ether_balance_in_usd(address):
#     """
#     Выводит весь текст страницы и подсчитывает количество знаков доллара.
#
#     Args:
#         url (str): URL веб-страницы.
#         driver_path (str): Путь к веб-драйверу.
#     """
#
#     # Настройка опций Firefox
#     options = Options()
#     #options.add_argument("--headless")  # Включаем headless-режим
#     url = f"https://etherscan.io/address/{address}"
#     try:
#         driver = webdriver.Firefox(options=options)
#         driver.get(url)
#
#         time.sleep(3)  # Ждем 3 секунды
#
#         page_text = driver.find_element(By.TAG_NAME, 'body').text # Получаем весь текст из тега body
#         balance = extract_all_values(page_text)
#         print(balance)
#         if balance[1]=='1':
#             balance=balance[2]
#         else:
#             balance=balance[1]
#         print(balance)
#         return balance
#     except Exception as e:
#         print(f"Произошла ошибка: {e}")
#     finally:
#         if 'driver' in locals():
#             driver.quit()
def get_ether_balance_in_usd(address):
    """
    Возвращает баланс Ethereum в долларах США для заданного адреса.

    Args:
        address (str): Адрес кошелька Ethereum.

    Returns:
        float: Баланс Ethereum в долларах США, или None в случае ошибки.
    """
    try:
        # Получаем баланс ETH с Etherscan API
        etherscan_api_key = "3CV9ABZV7W48F8WQCP93DUXY1YJMFN5IU4" #Замените на ваш Etherscan API key
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={etherscan_api_key}"
        response = requests.get(url)
        response.raise_for_status()  # Проверяем на ошибки HTTP
        data = response.json()

        if data["status"] == "1":
            wei_balance = int(data["result"])
            eth_balance = wei_balance / 10**18

            # Получаем текущую цену ETH в USD с CoinGecko API
            coingecko_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
            response = requests.get(coingecko_url)
            response.raise_for_status()
            price_data = response.json()
            eth_price_usd = price_data["ethereum"]["usd"]

            # Рассчитываем баланс в USD
            balance_usd = eth_balance * eth_price_usd
            return balance_usd
        else:
            print(f"Ошибка Etherscan API: {data['message']}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Ошибка HTTP запроса: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Ошибка обработки данных: {e}")
        return None

async def get_balance(user_id):
    user_id = user_id
    conn = sqlite3.connect("wallets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, address, network FROM wallets WHERE user_id = ?", (user_id,))
    wallets = cursor.fetchall()
    conn.close()

    if not wallets:
        return None
    balances=[]
    for name, address, network in wallets:
        if network == "Ethereum":
            balance = get_ether_balance_in_usd(address)
        elif network == "Tron":
            balance = get_tron_balance_in_usd(address)
        balances.append([name, network, balance])
    return balances



# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен вашего бота
TOKEN = "7951763968:AAGpuhRjkNH1j3XeC5wswBZIpq49mJEco8w"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Состояния для FSM
class WalletStates(StatesGroup):
    INPUT_ADDRESS = State()
    INPUT_NAME = State()
    CHOOSE_NETWORK = State()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("wallets.db")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS wallets (user_id INTEGER, name TEXT, address TEXT, network TEXT)"
    )
    conn.commit()
    conn.close()

# Сохранение кошелька в базу данных
def save_wallet(user_id, name, address, network):
    conn = sqlite3.connect("wallets.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO wallets VALUES (?, ?, ?, ?)",
        (user_id, name, address, network),
    )
    conn.commit()
    conn.close()

# Клавиатура для выбора сети
def choose_network_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Ethereum"))
    builder.add(KeyboardButton(text="Tron"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Используй /new, чтобы добавить новый кошелек.")

#Команда /start_task
@dp.message(Command("start_task"))
async def start_periodic_task(message: types.Message):
    global is_task_running
    try:
        print(is_task_running)
    except:
        is_task_running = False
    if not is_task_running:
        is_task_running = True
        chat_id = message.chat.id
        asyncio.create_task(empty_task(chat_id, message))  # Запуск фоновой задачи
        await message.reply("Фоновая задача запущена.")
    else:
        await message.reply("Фоновая задача уже выполняется.")

#Команда /stop
@dp.message(Command("stop"))
async def stop_periodic_task(message: types.Message):
    global is_task_running

    if is_task_running:
        is_task_running = False
        await message.reply("Фоновая задача остановлена.")
    else:
        await message.reply("Фоновая задача уже остановлена.")

# Команда /new
@dp.message(Command("new"))
async def cmd_new(message: types.Message, state: FSMContext):
    await message.answer("Введите адрес кошелька:")
    await state.set_state(WalletStates.INPUT_ADDRESS)

# Обработчик ввода адреса
@dp.message(WalletStates.INPUT_ADDRESS)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("Введите имя для кошелька:")
    await state.set_state(WalletStates.INPUT_NAME)

# Обработчик ввода имени
@dp.message(WalletStates.INPUT_NAME)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Выберите сеть:", reply_markup=choose_network_keyboard())
    await state.set_state(WalletStates.CHOOSE_NETWORK)

# Обработчик выбора сети
@dp.message(WalletStates.CHOOSE_NETWORK)
async def process_network(message: types.Message, state: FSMContext):
    if message.text not in ["Ethereum", "Tron"]:
        await message.answer("Пожалуйста, выберите сеть из предложенных вариантов.")
        return

    data = await state.get_data()
    user_id = message.from_user.id
    save_wallet(user_id, data["name"], data["address"], message.text)

    await message.answer(
        f"Кошелек добавлен!\n\n"
        f"Имя: {data['name']}\n"
        f"Адрес: {data['address']}\n"
        f"Сеть: {message.text}",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.clear()

# Команда /wallets
@dp.message(Command("wallets"))
async def cmd_wallets(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("wallets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, address, network FROM wallets WHERE user_id = ?", (user_id,))
    wallets = cursor.fetchall()
    conn.close()

    if wallets:
        response = "Ваши кошельки:\n\n"
        for name, address, network in wallets:
            response += f"Имя: {name}\nАдрес: {address}\nСеть: {network}\n\n"
    else:
        response = "У вас пока нет кошельков."

    await message.answer(response)

# Команда /balance
@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    balances = await get_balance(user_id=message.from_user.id)

    if not balances:
        await message.answer("У вас пока нет кошельков.")
        return

    for name, network, balance in balances:
        await message.answer(
            f"Баланс кошелька {name} ({network}): {float(balance):.2f} USD"
        )

# Команда /delete
@dp.message(Command("delete"))
async def cmd_delete(message: types.Message):
    user_id = message.from_user.id
    wallet_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

    if not wallet_name:
        await message.answer("Пожалуйста, укажите имя кошелька для удаления. Пример: /delete ИмяКошелька")
        return

    conn = sqlite3.connect("wallets.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wallets WHERE user_id = ? AND name = ?", (user_id, wallet_name))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted:
        await message.answer(f"Кошелек '{wallet_name}' успешно удален.")
    else:
        await message.answer(f"Кошелек с именем '{wallet_name}' не найден.")

# Запуск бота
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())