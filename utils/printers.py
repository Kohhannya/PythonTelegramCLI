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