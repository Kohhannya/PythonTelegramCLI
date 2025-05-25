from abc import ABC

import pandas as pd

from utils.printers import UserPrinter

def command(name, description=None):
    def decorator(func):
        func._command_name = name
        func._command_description = description or ""
        return func
    return decorator

class BaseState(ABC):
    def __init__(self, cli):
        self.cli = cli
        self.facade = cli.client_facade
        self.commands = {}
        self.command_descriptions = {}
        self.dialogs = pd.DataFrame() # Маленький кэш последнего запроса

        for attr in dir(self):
            method = getattr(self, attr)
            if callable(method) and hasattr(method, "_command_name"):
                name = getattr(method, "_command_name")
                desc = getattr(method, "_command_description", "")
                self.commands[name] = method
                self.command_descriptions[name] = desc

    async def handle_command(self, command: str):
        name = command.split()[0]
        handler = self.commands.get(name)
        if handler:
            await handler(command)
        else:
            if hasattr(self, "handle_fallback") and not name.startswith('/'):
                await self.handle_fallback(command)
            else:
                print(f"[!] Неизвестная команда: {name}")

    @command("/help", description="Вывести список команд с описанием")
    async def cmd_help(self, _):
        print("[*] Доступные команды:")
        for name, desc in self.command_descriptions.items():
            print(f"  {name:<15} — {desc}")

    @command("/exit", description="Завершить работу клиента")
    async def cmd_exit(self, _):
        raise SystemExit

    def find_dialogs(self, query):
        df = self.cli.get_dialogs_cache()

        def match(dialog):
            if dialog is None or not hasattr(dialog, 'entity'):
                return False
            entity = dialog.entity
            phone = getattr(entity, 'phone', '') or ''
            first = getattr(entity, 'first_name', '') or ''
            last = getattr(entity, 'last_name', '') or ''
            username = getattr(entity, 'username', '') or ''
            name = f"{first} {last}".strip()
            return query in phone.lower() or query in name.lower() or query in username.lower()
        try:
            return df[df["Dialog"].apply(match)].reset_index(drop=True)
        except Exception as e:
            print(f"[!] Ошибка при поиске: {e}")
            return None

    @command("/info_me", description="Показать информацию о себе")
    async def cmd_info_me(self, _):
        UserPrinter.print_user(self.facade.get_me(), title="Профиль")

    @command("/info_user_by_id", description="Информация о пользователе по ID")
    async def cmd_info_user_by_id(self, command):
        parts = command.split()
        if len(parts) != 2 or not parts[1].isdigit():
            print("[!] Использование: /info_user_by_id <id>")
            return

        user = await self.facade.get_user_by_id(int(parts[1]))
        if user:
            UserPrinter.print_user(user)
        else:
            print("[!] Пользователь не найден.")

    @command("/info_user", description="Вывод информации о пользователе по номеру из списка")
    async def cmd_info_user(self, command):
        parts = command.split()
        try:
            index = int(parts[1]) - 1
            dialog_row = self.dialogs.iloc[index]
            dialog = dialog_row["Dialog"]
            if not dialog.is_user:
                print("[!] Не является пользователем.")
            else:
                UserPrinter.print_user(dialog.entity)
        except (IndexError, ValueError, AttributeError):
            print("[!] Неверный индекс.")