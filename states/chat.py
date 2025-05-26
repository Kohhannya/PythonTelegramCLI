from utils.printers import MessagesPrinter
from .base import BaseState, command
from .main_menu import MainMenuState
from telethon import events
from telethon.tl.custom.dialog import Dialog

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
        MessagesPrinter.print_last_messages(messages)

        # Обработчик новых сообщений
        self.handler = self._create_handler()
        self.facade.client.add_event_handler(self.handler)

    async def handle_fallback(self, text: str):
        text = text.strip()
        if text:
            await self.facade.send_message(self.dialog.entity, text)

    def _create_handler(self):
        @events.register(events.NewMessage(chats=self.dialog.entity))
        async def handler(event):
            MessagesPrinter.print_new(event.message)
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