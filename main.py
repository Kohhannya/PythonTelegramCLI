import asyncio
from cli import TelegramCLI

if __name__ == '__main__':
    try:
        asyncio.run(TelegramCLI().start())
    except (KeyboardInterrupt, EOFError):
        print("\n[!] Клиент остановлен.")
