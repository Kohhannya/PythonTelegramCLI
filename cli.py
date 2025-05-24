import asyncio
from client_facade import ClientFacade
from states import UnauthenticatedState
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

# Асинхронный CLI

class TelegramCLI:
    def __init__(self):
        self.client_facade = ClientFacade()
        self.state = UnauthenticatedState(self)
        self.dialogs_cache = [] # Кэшированный список диалогов
        self.session = PromptSession()

    async def start(self):
        await self.state.enter()
        while True:
            try:
                # Получаем подсказки от текущего состояния, если есть
                completer = None
                if hasattr(self.state, "commands"):
                    completer = WordCompleter(
                        list(self.state.commands.keys()),
                        ignore_case=True,
                        sentence=True
                    )

                # Считываем команду с автодополнением
                command = await self.session.prompt_async(
                    self.prompt(),
                    completer=completer,
                    complete_while_typing=True
                )
                await self.state.handle_command(command.strip())
            except (EOFError, KeyboardInterrupt):
                print("\n[!] Завершение клиента...")
                break
            except Exception as e:
                print(f"[!] Ошибка: {e}")

    async def change_state(self, new_state_cls, *args, **kwargs):
        self.state = new_state_cls(self, *args, **kwargs)
        await self.state.enter()

    # Промт-подсказка нынешнего состояния клиента
    def prompt(self):
        current = type(self.state).__name__.replace("State", "")
        return f"[{current}]> "
