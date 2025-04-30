import os
from telethon import TelegramClient
from config import API_ID, API_HASH
from telethon.errors import (
    PhoneNumberInvalidError,
    PhoneNumberFloodError,
    PhoneNumberBannedError
)

SESSION_FILE = 'test.session'

class ClientFacade:
    def __init__(self):
        self.client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        self.me = None

    def _build_client(self):
        self.client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

    async def connect(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            return False
        self.me = await self.client.get_me()
        return True

    async def disconnect(self):
        await self.client.disconnect()

    async def login(self, phone):
        if not phone or not isinstance(phone, str) or phone.strip() == "":
            print("[!] Номер телефона не может быть пустым.")
            return False

        try:
            await self.client.send_code_request(phone)
            code = input("[?] Введите код подтверждения: ")
            self.me = await self.client.sign_in(phone, code)
        except PhoneNumberInvalidError:
            print("[!] Неверный номер телефона. Попробуйте снова.")
            return False
        except PhoneNumberFloodError:
            print("[!] Слишком много попыток. Подождите и попробуйте позже.")
            return False
        except PhoneNumberBannedError:
            print("[!] Этот номер заблокирован Telegram.")
            return False
        return True

    async def logout(self):
        await self.client.log_out()
        await self.client.disconnect()
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        print("[*] Вы вышли из аккаунта.")
        self._build_client() #Пересоздание клиента после выхода из аккаунта, но не приложения

    def get_me(self):
        return self.me

    async def list_dialogs(self):
        return await self.client.get_dialogs()

    async def get_messages(self, chat_entity, limit=20):
        return await self.client.get_messages(chat_entity, limit=limit)

    async def send_message(self, chat_entity, text):
        await self.client.send_message(chat_entity, text)
