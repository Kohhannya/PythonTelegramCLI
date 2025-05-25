import pandas as pd

from utils.printers import DialogsPrinter
from .base import BaseState, command
from .unauthenticated import UnauthenticatedState

class MainMenuState(BaseState):
    def __init__(self, cli):
        super().__init__(cli)
        self.dialogs = self.cli.get_dialogs_cache()

    async def enter(self):
        print("=== Главное меню ===")
        print("[*] Для вывода списка доступных команд введите /help")

    @command("/update", description="Обновить список чатов до актуального")
    async def cmd_update(self, _):
        try:
            # Обновляем dataframe диалогов
            self.cli.set_dialogs_cache(await self.facade.get_dialogs_df())
            self.dialogs = self.cli.get_dialogs_cache()
            print("[*] Список чатов обновлён.")
        except Exception as e:
            print(f"[!] Ошибка при получении чатов: {e}")

    @command("/list", description="Показать список чатов (по умолчанию первые 10).\n "
                                  "Добавьте параметры a, b через пробел для вывода диапазона чатов по номеру с a по b")
    async def cmd_list(self, command):
        parts = command.split()
        df = self.cli.get_dialogs_cache()

        if df is None or df.empty:
            print("[!] Список чатов пуст. Перезапустите авторизацию.")
            return
        try:
            if len(parts) == 1:
                df = df.iloc[0:10].reset_index(drop=True)
                title = "Первые 10 чатов"
            else:
                a = int(parts[1]) if len(parts) > 1 else 1
                b = int(parts[2]) if len(parts) > 2 else a + 9
                if a < 1 or b < a:
                    raise ValueError
                df = df.iloc[a - 1:b].reset_index(drop=True)
                title = f"Чаты {a}-{b}"

            self.dialogs = df
            DialogsPrinter.print(df, title=title, show_type=True)
        except (ValueError, IndexError):
            print("[!] Неверный формат. Использование: /list или /list a b")
        except Exception as e:
            print(f"[!] Ошибка при получении чатов: {e}")

    @command("/enter", description="Войти в чат по номеру из списка")
    async def cmd_enter(self, command):
        from .chat import ChatState
        parts = command.split()
        try:
            index = int(parts[1]) - 1
            dialog_row = self.dialogs.iloc[index]
            dialog = dialog_row["Dialog"]
            await self.cli.change_state(ChatState, dialog)
        except (IndexError, ValueError, AttributeError):
            print("[!] Неверный индекс.")

    @command("/enter_name", description="Войти в чат по названию чата или его части")
    async def cmd_enter_name(self, command):
        from .chat import ChatState
        name_query = command[len("/enter_name "):].strip().lower()
        matches = self.find_dialogs(name_query)

        if matches.empty:
            print("[!] Чат с похожим именем не найден.")
        elif len(matches) == 1:
            await self.cli.change_state(ChatState, matches.iloc[0]["Dialog"])
        else:
            DialogsPrinter.print(matches, title=f"Чаты по имени '{name_query}'")
            print("[*] Уточните название или используйте /enter <номер>")
        self.dialogs = matches

    @command("/search", description="Поиск чата по части имени или номеру телефона")
    async def cmd_search(self, command):
        query = command[len("/search "):].strip().lower()

        if not query:
            print("[!] Использование: /search <строка>")
            return
        df = self.cli.get_dialogs_cache()
        matches = self.find_dialogs(query)

        if matches.empty:
            print("[!] Ничего не найдено.")
        else:
            DialogsPrinter.print(matches, title=f"Результаты поиска '{query}'")
            print("[*] Используйте /enter <номер> для входа в чат")
        self.dialogs = matches

    @command("/logout", description="Выйти из аккаунта Telegram")
    async def cmd_logout(self, _):
        await self.facade.logout()
        await self.cli.change_state(UnauthenticatedState)