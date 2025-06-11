import asyncio
from src.telegram_client import TelegramAnalyzer
from config.settings import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE

def print_chat_history(recent_chats):
    if not recent_chats:
        print("Історія чатів порожня.")
        return

    print("Історія останніх чатів:")
    for chat in recent_chats:
        print(f"Чат: {chat['name']} (ID: {chat['id']})")

def print_messages(messages):
    if not messages:
        print("Повідомлення відсутні.")
        return

    print("Повідомлення:")
    for message in messages:
        date = message['date'].strftime('%Y-%m-%d %H:%M:%S')
        sender = "Ви" if message['from_me'] else "Інший користувач"
        print(f"{date} - {sender}: {message['text']}")

async def main():
    telegram = TelegramAnalyzer(TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE)

    try:
        # Підключення до Telegram
        await telegram.connect()
        
        # Отримання останніх чатів
        print("Отримання останніх чатів...")
        recent_chats = await telegram.get_recent_chats(limit=3)

        for chat in recent_chats:
            print(f"Аналіз чату з {chat['name']}...")

            # Отримання історії повідомлень за день
            messages = await telegram.get_chat_history(chat['id'], days_back=1)
            
            if not messages:
                continue

        print_chat_history(recent_chats)
        print_messages(messages)
        print("Аналіз завершено.")

    except Exception as e:
        print(f"Помилка: {e}")

    finally:
        await telegram.client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())




