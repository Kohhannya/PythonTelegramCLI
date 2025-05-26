from .base import BaseState

class UnauthenticatedState(BaseState):
    async def enter(self):
        print("=== Авторизация Telegram ===")
        connected = await self.facade.connect()
        if connected:
            print(f"[*] Авторизованы как: {self.facade.get_me().first_name}")

            # Загружаем кэш диалогов из файла
            # await self.cli.load_dialogs_cache()
            self.cli.set_dialogs_cache(await self.facade.get_dialogs_df())

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

                # Кэшируем актуальный список чатов в виде DataFrame-поле клиента
                self.cli.set_dialogs_cache(await self.facade.get_dialogs_df())
                # Сохраняем его в файл
                # self.cli.save_dialogs_cache()

                from .main_menu import MainMenuState
                await self.cli.change_state(MainMenuState)
                break

    async def handle_command(self, command: str):
        print("[!] Сначала авторизуйтесь.")
