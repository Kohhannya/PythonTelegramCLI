from abc import ABC, abstractmethod

from telethon import events
from telethon.tl.custom.dialog import Dialog
from telethon.errors import SessionPasswordNeededError


class BaseState(ABC):
    def __init__(self, cli):
        self.cli = cli
        self.facade = cli.client_facade

    @abstractmethod
    async def enter(self):
        pass

    @abstractmethod
    async def handle_command(self, command: str):
        pass


class UnauthenticatedState(BaseState):
    async def enter(self):
        print("=== Авторизация Telegram ===")
        connected = await self.facade.connect()
        if connected:
            print(f"[*] Авторизованы как: {self.facade.get_me().first_name}")
            await self.cli.change_state(MainMenuState)
            return

        while True:
            phone = input("[?] Введите номер телефона (в международном формате, например +79161234567): ").strip()
            success = await self.facade.login(phone)
            if success:
                print(f"[*] Авторизованы как: {self.facade.get_me().first_name}")
                await self.cli.change_state(MainMenuState)
                break

    async def handle_command(self, command: str):
        print("[!] Сначала авторизуйтесь.")


class MainMenuState(BaseState):
    def __init__(self, cli):
        super().__init__(cli)
        self.dialogs = None

    async def enter(self):
        print("=== Главное меню ===")
        print("Доступные команды: list, enter <номер>, logout, exit")

    async def handle_command(self, command: str):
        if command.startswith("list"):
            parts = command.split()

            try:
                a = int(parts[1]) if len(parts) > 1 else 1
                b = int(parts[2]) if len(parts) > 2 else a + 9
                if a < 1 or b < a:
                    raise ValueError

                all_dialogs = await self.facade.list_dialogs()
                slice_ = all_dialogs[a - 1:b]
                self.dialogs = slice_

                if not slice_:
                    print("[*] Нет чатов в этом диапазоне.")
                else:
                    for idx, d in enumerate(slice_, start=a):
                        print(f"{idx}: {d.name}")

            except ValueError:
                print("[!] Неверный формат. Используй: list или list a b")
            except Exception as e:
                print(f"[!] Ошибка при получении чатов: {e}")

        elif command.startswith("enter "):
            try:
                index = int(command.split()[1])
                dialog = self.dialogs[index]
                await self.cli.change_state(ChatState, dialog)
            except (IndexError, ValueError, AttributeError):
                print("[!] Неверный индекс чата. Сначала выполните list.")

        elif command == "logout":
            await self.facade.logout()
            await self.cli.change_state(UnauthenticatedState)

        elif command == "exit":
            raise SystemExit

        else:
            print("[?] Неизвестная команда. Используйте: list, enter, logout, exit")


class ChatState(BaseState):
    def __init__(self, cli, dialog: Dialog):
        super().__init__(cli)
        self.dialog = dialog
        self.handler = None

    async def enter(self):
        print(f"=== Чат: {self.dialog.name} ===")
        print("Команды: send <сообщение>, back, exit")

        # Показ последних сообщений
        messages = await self.facade.get_messages(self.dialog.entity, limit=10)
        for m in reversed(messages):
            print(f"[{m.sender_id}] {m.text}")

        # Установим обработчик новых сообщений
        self.handler = self._create_handler()
        self.facade.client.add_event_handler(self.handler)

    def _create_handler(self):
        @events.register(events.NewMessage(chats=self.dialog.entity))
        async def handler(event):
            sender = await event.get_sender()
            name = sender.first_name if sender else "?"
            print(f"\n[new] {name}: {event.message.message}")
        return handler

    async def handle_command(self, command: str):
        if command.startswith("send "):
            msg = command[len("send "):]
            await self.facade.send_message(self.dialog.entity, msg)

        elif command == "back":
            self.facade.client.remove_event_handler(self.handler)
            await self.cli.change_state(MainMenuState)

        elif command == "exit":
            self.facade.client.remove_event_handler(self.handler)
            raise SystemExit

        else:
            print("[?] Команды: send <текст>, back, exit")