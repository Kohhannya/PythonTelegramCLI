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
                df = df.iloc[0:10]
                title = "Первые 10 чатов"
            else:
                a = int(parts[1]) if len(parts) > 1 else 1
                b = int(parts[2]) if len(parts) > 2 else a + 9
                if a < 1 or b < a:
                    raise ValueError
                df = df.iloc[a - 1:b]
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
        df = self.cli.get_dialogs_cache()

        try:
            matches = df[df["Name"].str.lower().str.contains(name_query, na=False)].reset_index(drop=True)

            if matches.empty:
                print("[!] Чат с похожим именем не найден.")
            elif len(matches) == 1:
                await self.cli.change_state(ChatState, matches.iloc[0]["Dialog"])
            else:
                DialogsPrinter.print(matches, title=f"Чаты по имени '{name_query}'", show_type=True)
                print("[*] Уточните название или используйте /enter <номер>")
            self.dialogs = matches
        except Exception as e:
            print(f"[!] Ошибка при поиске: {e}")

    @command("/enter_phone", description="Войти в чат по номеру телефона")
    async def cmd_enter_phone(self, command):
        from .chat import ChatState
        phone_query = command[len("/enter_phone "):].strip().lstrip('+')
        df = self.cli.get_dialogs_cache()

        def phone_match(dialog):
            entity = dialog.entity
            return hasattr(entity, 'phone') and phone_query in str(entity.phone)

        try:
            matches = df[df["Dialog"].apply(phone_match)].reset_index(drop=True)

            if matches.empty:
                print("[!] Пользователь с таким номером не найден.")
            elif len(matches) == 1:
                await self.cli.change_state(ChatState, matches.iloc[0]["Dialog"])
            else:
                DialogsPrinter.print(matches, title=f"Чаты по номеру '{phone_query}'")
                print("[*] Уточните номер или используйте /enter <номер>")
            self.dialogs = matches
        except Exception as e:
            print(f"[!] Ошибка при поиске: {e}")

    @command("/enter_phone", description="Войти в чат по номеру телефона")
    async def cmd_enter_phone(self, command):
        from .chat import ChatState
        phone_query = command[len("/enter_phone "):].strip().lstrip('+')
        df = self.cli.get_dialogs_cache()

        def phone_match(dialog):
            entity = dialog.entity
            return hasattr(entity, 'phone') and phone_query in str(entity.phone)

        try:
            matches = df[df["Dialog"].apply(phone_match)].reset_index(drop=True)

            if matches.empty:
                print("[!] Пользователь с таким номером не найден.")
            elif len(matches) == 1:
                await self.cli.change_state(ChatState, matches.iloc[0]["Dialog"])
            else:
                DialogsPrinter.print(matches, title=f"Чаты по номеру '{phone_query}'")
                print("[*] Уточните номер или используйте /enter <номер>")
            self.dialogs = matches
        except Exception as e:
            print(f"[!] Ошибка при поиске: {e}")

    @command("/logout", description="Выйти из аккаунта Telegram")
    async def cmd_logout(self, _):
        await self.facade.logout()
        await self.cli.change_state(UnauthenticatedState)