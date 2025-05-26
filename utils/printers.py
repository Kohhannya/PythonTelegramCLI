import pandas as pd


class UserPrinter:
    @staticmethod
    def print_user(user, title="Пользователь"):
        if not user:
            print("[!] Данные отсутствуют.")
            return

        print(f"=== {title} ===")
        print(f"ID: {user.id}")
        print(f"Имя: {user.first_name or ''} {user.last_name or ''}".strip())
        print(f"Username: @{user.username}" if user.username else "Username: —")
        print(f"Телефон: +{user.phone}" if user.phone else "Телефон: —")
        print(f"Premium: {'Да' if getattr(user, 'premium', False) else 'Нет'}")
        print(f"Verified: {'Да' if getattr(user, 'verified', False) else 'Нет'}")

class DialogsPrinter:
    @staticmethod
    def print(df: pd.DataFrame, title: str = "Чаты", show_type: bool = False, show_participants: bool = False):
        if df is None:
            print("[!] Список чатов не загружен.")
            return

        if df.empty:
            print("[!] Список чатов пуст.")
            return

        max_name_length = 0
        for i, row in df.iterrows():
            name = row.get("Name", "—")
            max_name_length = max(max_name_length, len(name))

        print(f"=== {title} ===")
        for i, row in df.iterrows():
            index = i + 1  # Индексация с 1
            name = row.get("Name", "—")
            print(f"{index:>3}. {name:<{max_name_length}}", end="")
            if show_type:
                dtype = row.get("Type", "—")
                print(f" [{dtype:^7}]", end="")
            if show_participants:
                participants = row.get("Participants", "—")
                print(f" — участников: {participants if pd.notna(participants) else '—'}", end="")
            print("")

class MessagesPrinter:
    @staticmethod
    def print_last_messages(messages, limit=20, color="\033[96m", name_placeholder=8, ):
        print("\n=== Последние сообщения ===")
        if not messages:
            print("(нет сообщений)")
            return

        for msg in reversed(messages[-limit:]):
            sender = getattr(msg.sender, 'first_name', 'Неизв.') if msg.sender else 'Система'
            name_placeholder = max(name_placeholder, len(sender))

        for msg in reversed(messages[-limit:]):
            MessagesPrinter._print_single(msg, color, name_placeholder)

    @staticmethod
    def print_new(msg, color="\033[96m"):
        print("\n[new]")
        MessagesPrinter._print_single(msg, color)

    @staticmethod
    def _print_single(msg, color="\033[96m", name_placeholder=8):
        sender = getattr(msg.sender, 'first_name', 'Неизв.') if msg.sender else 'Система'
        text = msg.message if getattr(msg, 'message', None) else '[медиа]' if msg.media else '[пусто]'
        print(f"[{msg.date.strftime('%H:%M')}] {sender:^{name_placeholder}}: {color}{text}\033[0m")