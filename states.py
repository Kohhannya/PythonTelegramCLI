from abc import ABC, abstractmethod

from utils import command
from telethon.errors import SessionPasswordNeededError
from telethon.tl.custom.dialog import Dialog
from telethon import events


class BaseState(ABC):
    def __init__(self, cli):
        self.cli = cli
        self.facade = cli.client_facade
        self.commands = {}
        self.command_descriptions = {}

        # Автоматическая регистрация команд
        for attr in dir(self):
            method = getattr(self, attr)
            if callable(method) and hasattr(method, "_command_name"):
                name = method._command_name
                desc = getattr(method, "_command_description", "")
                self.commands[name] = method
                self.command_descriptions[name] = desc

    async def handle_command(self, command: str):
        name = command.split()[0]
        handler = self.commands.get(name)
        if handler:
            await handler(command)
        else:
            print(f"[!] Неизвестная команда: {name}")

    @abstractmethod
    async def enter(self):
        pass

    @command("/help", description="Вывести список команд")
    async def cmd_help(self, _):
        print("[*] Доступные команды:")
        for name, desc in self.command_descriptions.items():
            print(f"  {name:<15} — {desc}")

    @command("/exit", description="Завершить работу клиента")
    async def cmd_exit(self, _):
        raise SystemExit


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

    async def enter(self):
        print("=== Главное меню ===")
        print("[*] Для вывода списка доступных команд введите /help")

    @command("/list", description="Показать список чатов (по умолчанию первые 10). "
                                  "Добавьте параметры a, b через пробел для вывода диапазона чатов по номеру с a по b")
    async def cmd_list(self, command):
        parts = command.split()
        try:
            if len(parts) == 1:
                self.cli.dialogs_cache = await self.facade.list_dialogs()
                print("[*] Список чатов обновлён.")
                # self.dialogs = self.cli.dialogs_cache
                dialogs = self.cli.dialogs_cache[:10]
            else:
                a = int(parts[1]) if len(parts) > 1 else 1
                b = int(parts[2]) if len(parts) > 2 else a + 9
                if a < 1 or b < a:
                    raise ValueError
                dialogs = self.cli.dialogs_cache[a - 1:b]

            if not dialogs:
                print("[*] Нет чатов в этом диапазоне.")
            else:
                for i, d in enumerate(dialogs, start=1):
                    print(f"{i}: {d.name}")
        except ValueError:
            print("[!] Неверный формат.")
        except Exception as e:
            print(f"[!] Ошибка при получении чатов: {e}")

    @command("/enter", description="Войти в чат по номеру из списка")
    async def cmd_enter(self, command):
        parts = command.split()
        try:
            index = int(parts[1]) - 1
            dialog = self.dialogs[index]
            await self.cli.change_state(ChatState, dialog)
        except (IndexError, ValueError, AttributeError):
            print("[!] Неверный индекс. Используйте list сначала.")

    @command("/enter_name", description="Войти в чат по названию чата или его части")
    async def cmd_enter_name(self, command):
        name_query = command[len("/enter_name "):].strip().lower()

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

    @command("/enter_phone", description="Войти в чат по номеру телефона")
    async def cmd_enter_phone(self, command):
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

    @command("/logout", description="Выйти из аккаунта Telegram")
    async def cmd_logout(self, _):
        await self.facade.logout()
        await self.cli.change_state(UnauthenticatedState)


class ChatState(BaseState):
    def __init__(self, cli, dialog: Dialog):
        super().__init__(cli)
        self.dialog = dialog
        self.handler = None

    async def enter(self):
        print(f"=== Чат: {self.dialog.name} ===")
        print("[*] Для вывода списка доступных команд введите /help")

        # Показ последних сообщений
        messages = await self.facade.get_messages(self.dialog.entity, limit=10)
        for m in reversed(messages):
            print(f"[{m.sender_id}] {m.text}")

        # Обработчик новых сообщений
        self.handler = self._create_handler()
        self.facade.client.add_event_handler(self.handler)

    def _create_handler(self):
        @events.register(events.NewMessage(chats=self.dialog.entity))
        async def handler(event):
            sender = await event.get_sender()
            name = sender.first_name if sender else "?"
            print(f"\n[new] {name}: {event.message.message}")
        return handler

    @command("/send", description="Отправить сообщение в чат")
    async def cmd_send(self, command):
        text = command[len("/send "):].strip()
        if text:
            await self.facade.send_message(self.dialog.entity, text)

    @command("/back", description="Вернуться в главное меню")
    async def cmd_back(self, _):
        self.facade.client.remove_event_handler(self.handler)
        await self.cli.change_state(MainMenuState)