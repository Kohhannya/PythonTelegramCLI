from .base import BaseState, command
from .unauthenticated import UnauthenticatedState

class MainMenuState(BaseState):
    def __init__(self, cli):
        super().__init__(cli)

    async def enter(self):
        print("=== Главное меню ===")
        print("[*] Для вывода списка доступных команд введите /help")

    @command("/list", description="Показать список чатов (по умолчанию первые 10).\n "
                                  "Добавьте параметры a, b через пробел для вывода диапазона чатов по номеру с a по b")
    async def cmd_list(self, command):
        parts = command.split()
        try:
            if len(parts) == 1:
                self.cli.dialogs_cache = await self.facade.get_dialogs_list()
                print("[*] Список чатов обновлён.")
                self.dialogs = self.cli.dialogs_cache[:10]
            else:
                a = int(parts[1]) if len(parts) > 1 else 1
                b = int(parts[2]) if len(parts) > 2 else a + 9
                if a < 1 or b < a:
                    raise ValueError
                self.dialogs = self.cli.dialogs_cache[a - 1:b]

            if not self.dialogs:
                print("[*] Нет чатов в этом диапазоне.")
            else:
                for i, d in enumerate(self.dialogs, start=1):
                    print(f"{i}: {d.name}")
        except ValueError:
            print("[!] Неверный формат.")
        except Exception as e:
            print(f"[!] Ошибка при получении чатов: {e}")

    @command("/enter", description="Войти в чат по номеру из списка")
    async def cmd_enter(self, command):
        from .chat import ChatState
        parts = command.split()
        try:
            index = int(parts[1]) - 1
            dialog = self.dialogs[index]
            await self.cli.change_state(ChatState, dialog)
        except (IndexError, ValueError, AttributeError):
            print("[!] Неверный индекс. Используйте list сначала.")

    @command("/enter_name", description="Войти в чат по названию чата или его части")
    async def cmd_enter_name(self, command):
        from .chat import ChatState
        name_query = command[len("/enter_name "):].strip().lower()

        matches = [
            d for d in self.cli.dialogs_cache
            if name_query in d.name.lower()
        ]
        self.dialogs = matches

        if not self.dialogs:
            print("[!] Чат с таким именем не найден.")
        elif len(self.dialogs) == 1:
            await self.cli.change_state(ChatState, self.dialogs[0])
        else:
            print("[*] Найдено несколько чатов:")
            for i, d in enumerate(self.dialogs):
                print(f"  {i + 1}: {d.name}")
            print("Уточните название.")

    @command("/enter_phone", description="Войти в чат по номеру телефона")
    async def cmd_enter_phone(self, command):
        from .chat import ChatState
        fragment = command[len("/enter_phone "):].strip().replace(" ", "").lstrip('+')

        try:
            matches = []
            for d in self.cli.dialogs_cache:
                if hasattr(d.entity, 'phone') and d.entity.phone:
                    if fragment in d.entity.phone:
                        matches.append(d)
            self.dialogs = matches

            if not self.dialogs:
                print("[!] Пользователи с таким номером не найдены.")
            elif len(self.dialogs) == 1:
                await self.cli.change_state(ChatState, self.dialogs[0])
            else:
                print("[*] Найдено несколько пользователей:")
                for i, d in enumerate(self.dialogs):
                    print(f"  {i + 1}: {d.name} (+{d.entity.phone})")
                print("Пожалуйста, уточните номер.")
        except Exception as e:
            print(f"[!] Ошибка при поиске: {e}")

    @command("/logout", description="Выйти из аккаунта Telegram")
    async def cmd_logout(self, _):
        await self.facade.logout()
        await self.cli.change_state(UnauthenticatedState)