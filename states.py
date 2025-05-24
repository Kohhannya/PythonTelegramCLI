from abc import ABC, abstractmethod

from utils import command
from telethon.errors import SessionPasswordNeededError
from telethon.tl.custom.dialog import Dialog
from telethon import events


class BaseState(ABC):
    def __init__(self, cli):
        self.cli = cli
        self.facade = cli.client_facade
        self.commands = {
            "/help": "Показать список команд"
        }
        # self.command_descriptions = {}

        # Автоматическая регистрация команд
        # for attr in dir(self):
        #     method = getattr(self, attr)
        #     if callable(method) and hasattr(method, "_command_name"):
        #         name = method._command_name
        #         desc = getattr(method, "_command_description", "")
        #         self.commands[name] = method
        #         self.command_descriptions[name] = desc

    # async def handle_command(self, command: str):
    #     name = command.split()[0]
    #     handler = self.commands.get(name)
    #     if handler:
    #         await handler(command)
    #     else:
    #         print(f"[!] Неизвестная команда: {name}")
    @abstractmethod
    async def handle_command(self, command: str):
        pass

    @abstractmethod
    async def enter(self):
        pass


class UnauthenticatedState(BaseState):
    async def enter(self):
        print("=== Авторизация Telegram ===")
        connected = await self.facade.connect()
        if connected:
            print(f"[*] Авторизованы как: {self.facade.get_me().first_name}")
            self.cli.dialogs_cache = await self.facade.list_dialogs()
            await self.cli.change_state(MainMenuState)
            return

        while True:
            phone = input("[?] Введите номер телефона (в международном формате, например +79161234567): ").strip()
            success = await self.facade.login(phone)
            if success:
                print(f"[*] Авторизованы как: {self.facade.get_me().first_name}")
                self.cli.dialogs_cache = await self.facade.list_dialogs()
                await self.cli.change_state(MainMenuState)
                break

    async def handle_command(self, command: str):
        print("[!] Сначала авторизуйтесь.")


class MainMenuState(BaseState):
    def __init__(self, cli):
        super().__init__(cli)
        self.dialogs = self.cli.dialogs_cache

        self.commands = {
            "/help": "Показать список команд",
            "/list": "показать первые 10 чатов",
            "/list a b": "показать чаты с индекса a по b",
            "/enter ": "войти в чат по номеру из списка",
            "/enter_name ": "Войти в чат по части имени",
            "/enter_phone ": "Войти в чат по части номера телефона",
            "/logout": "Выйти из аккаунта Telegram",
            "/exit": "Завершить работу клиента"
        }

    async def enter(self):
        print("=== Главное меню ===")
        print("[*] Для просмотра доступных команд введите /help")

    # @command("/help", description="Вывести список команд")
    # async def cmd_help(self, _):
    #     print("[*] Команды:")
    #     for name, desc in self.command_descriptions.items():
    #         print(f"  {name:<10} — {desc}")

    async def handle_command(self, command: str):
        if command.startswith("/help"):
            print("[*] Команды:")
            for name, desc in self.commands.items():
                print(f"  {name:<10} — {desc}")
        elif command.startswith("/list"):
            parts = command.split()

            try:
                # list без параметров → обновление списка
                if len(parts) == 1:
                    self.cli.dialogs_cache = await self.facade.list_dialogs()
                    print("[*] Список чатов обновлён.")

                dialogs = self.cli.dialogs_cache
                if not dialogs:
                    print("[!] Выполните '/list' для обновления списка диалогов.")
                    return

                a = int(parts[1]) if len(parts) > 1 else 1
                b = int(parts[2]) if len(parts) > 2 else a + 9
                if a < 1 or b < a:
                    raise ValueError

                slice_ = dialogs[a - 1:b]
                self.dialogs = dialogs

                if not slice_:
                    print("[*] Нет чатов в этом диапазоне.")
                else:
                    for idx, d in enumerate(slice_, start=a):
                        print(f"{idx}: {d.name}")

            except ValueError:
                print("[!] Неверный формат. Используй: list или list a b")
            except Exception as e:
                print(f"[!] Ошибка при получении чатов: {e}")

        elif command.startswith("/enter "):
            try:
                index = int(command.split()[1]) - 1
                dialog = self.dialogs[index]
                await self.cli.change_state(ChatState, dialog)
            except (IndexError, ValueError, AttributeError):
                print("[!] Неверный индекс чата. Сначала выполните list.")

        elif command.startswith("/enter_name "):
            name_query = command[len("enter_name "):].strip().lower()

            matching = [
                d for d in self.cli.dialogs_cache
                if name_query in d.name.lower()
            ]

            if not matching:
                print("[!] Чат с таким именем не найден.")
            elif len(matching) == 1:
                await self.cli.change_state(ChatState, matching[0])
            else:
                print("[*] Найдено несколько чатов:")
                for i, d in enumerate(matching):
                    print(f"  {i + 1}: {d.name}")
                print("Уточните название.")

        elif command.startswith("/enter_phone "):
            fragment = command[len("/enter_phone "):].strip().replace(" ", "").lstrip('+')

            try:
                matches = []
                for d in self.cli.dialogs_cache:
                    if hasattr(d.entity, 'phone') and d.entity.phone:
                        if fragment in d.entity.phone:
                            matches.append(d)

                if not matches:
                    print("[!] Пользователи с таким номером не найдены.")
                elif len(matches) == 1:
                    await self.cli.change_state(ChatState, matches[0])
                else:
                    print("[*] Найдено несколько пользователей:")
                    for i, d in enumerate(matches):
                        print(f"  {i + 1}: {d.name} (+{d.entity.phone})")
                    print("Пожалуйста, уточните номер.")
            except Exception as e:
                print(f"[!] Ошибка при поиске: {e}")

        elif command == "/logout":
            await self.facade.logout()
            await self.cli.change_state(UnauthenticatedState)

        elif command == "/exit":
            raise SystemExit

        else:
            print("[?] Неизвестная команда. Используйте: list, enter, logout, exit")


class ChatState(BaseState):
    def __init__(self, cli, dialog: Dialog):
        super().__init__(cli)
        self.dialog = dialog
        self.handler = None

    commands = {
        "/send ": "Отправить сообщение",
        "/back ": "Вернуться в главное меню",
        "/exit ": "Выйти из клиента",
        "/help ": "Показать команды чата"
    }

    async def enter(self):
        print(f"=== Чат: {self.dialog.name} ===")
        print("Команды: /send <сообщение>, /back, /exit")

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
        if command.startswith("/send "):
            msg = command[len("send "):]
            await self.facade.send_message(self.dialog.entity, msg)

        elif command == "/back":
            self.facade.client.remove_event_handler(self.handler)
            await self.cli.change_state(MainMenuState)

        elif command == "/exit":
            self.facade.client.remove_event_handler(self.handler)
            raise SystemExit

        else:
            print("[?] Команды: /send <текст>, /back, /exit")