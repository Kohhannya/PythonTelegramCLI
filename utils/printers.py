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