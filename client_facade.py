import os
from telethon import TelegramClient
import pandas as pd
from telethon.tl.types import User, Chat, Channel

from config import API_ID, API_HASH
from telethon.errors import (
    PhoneNumberInvalidError,
    PhoneNumberFloodError,
    PhoneNumberBannedError
)

SESSION_FILE = 'test.session'

# Класс-фасад для работы с API telegram

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
        if not phone or not isinstance(phone, str) or phone.strip() == "": # Проверка правильности ввода
            print("[!] Номер телефона не может быть пустым.")
            return False

        try:
            await self.client.send_code_request(phone) # Запрос на отправку кода подтверждения
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

    async def get_dialogs_list(self):
        return await self.client.get_dialogs()

    async def get_messages(self, chat_entity, limit=20):
        return await self.client.get_messages(chat_entity, limit=limit)

    async def send_message(self, chat_entity, text):
        await self.client.send_message(chat_entity, text)

    async def get_user_by_id(self, user_id):
        try:
            return await self.client.get_entity(user_id)
        except Exception:
            return None

    async def get_dialogs_df(self):
        dialogs = await self.client.get_dialogs()
        data = []

        for d in dialogs:
            entity = d.entity
            if d.is_user:
                dialog_type = "Private"
                name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                participants = None
            elif d.is_group:
                dialog_type = "Chat"
                name = entity.title
                participants = getattr(entity, "participants_count", None)
            elif d.is_channel:
                dialog_type = "Channel"
                name = entity.title
                participants = getattr(entity, "participants_count", None)
            else:
                continue

            data.append({
                "ID": entity.id,
                "Name": name,
                "Type": dialog_type,
                "Participants": participants,
                "Dialog": d
            })

        return pd.DataFrame(data)
