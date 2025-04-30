from telethon import TelegramClient

# Замените на свои значения
api_id = 22860037
api_hash = '8193514b26a562bfa6fe6026ae243119'
phone_number = '+79169947500'

# Название сессии (файл сохранится как session_name.session)
client = TelegramClient('session_test', api_id, api_hash)

async def main():
    # Подключение и авторизация (если нужно)
    await client.start(phone=phone_number)

    # Вывод списка диалогов
    dialogs = await client.get_dialogs(limit=10)
    for i, dialog in enumerate(dialogs):
        print(f"[{i}] {dialog.name}")

    index = int(input("Выберите чат по номеру: "))
    selected_chat = dialogs[index].entity

    print("\nПоследние 5 сообщений:\n")
    async for message in client.iter_messages(selected_chat, limit=5):
        print(f"{message.sender_id}: {message.text}")

with client:
    client.loop.run_until_complete(main())
