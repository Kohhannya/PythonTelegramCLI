from .base import BaseState

class UnauthenticatedState(BaseState):
    async def enter(self):
        print("=== Авторизация Telegram ===")
        connected = await self.facade.connect()
        if connected:
            print(f"[*] Авторизованы как: {self.facade.get_me().first_name}")
            self.cli.dialogs_cache = await self.facade.get_dialogs_list()
            from .main_menu import MainMenuState
            await self.cli.change_state(MainMenuState)
            return

        while True:
            phone = input("[?] Введите номер телефона: ").strip()
            if not phone:
                print("[!] Номер не может быть пустым.")
                continue
            success = await self.facade.login(phone)
            if success:
                print(f"[*] Авторизованы как: {self.facade.get_me().first_name}")
                self.cli.dialogs_cache = await self.facade.get_dialogs_list()
                from .main_menu import MainMenuState
                await self.cli.change_state(MainMenuState)
                break

    async def handle_command(self, command: str):
        print("[!] Сначала авторизуйтесь.")
