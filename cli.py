import asyncio
from client_facade import ClientFacade
from states import UnauthenticatedState

class TelegramCLI:
    def __init__(self):
        self.client_facade = ClientFacade()
        self.state = UnauthenticatedState(self)

    async def start(self):
        await self.state.enter()
        while True:
            try:
                command = await asyncio.get_event_loop().run_in_executor(None, input, self.prompt())
                await self.state.handle_command(command.strip())
            except (EOFError, KeyboardInterrupt):
                print("\n[!] Завершение клиента...")
                break
            except Exception as e:
                print(f"[!] Ошибка: {e}")

    async def change_state(self, new_state_cls, *args, **kwargs):
        self.state = new_state_cls(self, *args, **kwargs)
        await self.state.enter()

    def prompt(self):
        current = type(self.state).__name__.replace("State", "")
        return f"[{current}]> "
