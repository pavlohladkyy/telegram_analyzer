import asyncio
from src.ai_analyzer import AiAnalizer
from config.settings import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, API_KEY
from src.telegram_client import TelegramAnalyzer
from src.message_analyzer import MessageProcessor
from src.database import Database
from datetime import datetime, timedelta

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
        sender = "Менеджер" if message['from_me'] else "Клієнт"
        print(f"{date} - {sender}: {message['text']}")

def print_conversation_analysis(conversation):
    """Виведення базової статистики розмови"""
    print(f"\n📊 Аналіз розмови:")
    print(f"   Загальна кількість повідомлень: {conversation.total_messages}")
    print(f"   Повідомлення менеджера: {conversation.manager_messages}")
    print(f"   Повідомлення клієнта: {conversation.client_messages}")
    print(f"   Період розмови: {conversation.start_date.strftime('%Y-%m-%d')} - {conversation.end_date.strftime('%Y-%m-%d')}")
    
    if conversation.total_messages > 0:
        manager_ratio = (conversation.manager_messages / conversation.total_messages) * 100
        print(f"   Активність менеджера: {manager_ratio:.1f}%")

def print_ai_analysis(ai_result):
    """Виведення результатів аналізу AI"""
    if not ai_result:
        print("AI аналіз не виконано або сталася помилка.")
        return
    
    print("\n=== AI Аналіз розмови ===")
    print(f"Виявлено обіцянки: {ai_result.get('promises_found')}")
    print(f"Кількість невиконаних обіцянок: {ai_result.get('unfulfilled_count')}")
    print(f"Висновок: {ai_result.get('analysis_summary')}")
    
    if ai_result.get('promises'):
        print("\nОбіцянки:")
        for p in ai_result['promises']:
            print(f"- {p.get('promise_text')} | Термін: {p.get('deadline')} | Виконано: {p.get('fulfilled')} | Причина: {p.get('reason')}")

async def main():
    telegram = TelegramAnalyzer(TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE)
    ai_analyzer = AiAnalizer(API_KEY)
    db = Database()
    processor = MessageProcessor()

    await telegram.connect()
    recent_chats = await telegram.get_recent_chats(limit=3)
    print_chat_history(recent_chats)

    for chat in recent_chats:
        print(f"\n--- Аналіз чату: {chat['name']} (ID: {chat['id']}) ---")
        messages = await telegram.get_chat_history(chat['id'], days_back=1)
        if not messages:
            print("Немає повідомлень для аналізу.")
            continue

        print_messages(messages)

        # Підготовка даних для AI через MessageProcessor
        conversation = processor.process_messages(messages)
        conversation.chat_name = chat['name']
        print_conversation_analysis(conversation)

        # Підготовка повідомлень для AI (як список словників)
        messages_for_ai = []
        for msg in conversation.messages:
            messages_for_ai.append({
                "from_me": msg.from_me,
                "date": msg.date,
                "text": msg.text
            })

        # AI аналіз розмови
        try:
            ai_result = ai_analyzer.analyze_conversation(messages_for_ai)
            if not isinstance(ai_result, dict):
                print("AI аналіз не повернув коректний результат.")
                ai_result = None
        except Exception as e:
            print(f"Помилка AI аналізу: {e}")
            ai_result = None

        print_ai_analysis(ai_result)

        # Запис результату AI аналізу в базу даних
        if ai_result:
            db.save_analysis(
                chat_id=chat['id'],
                chat_name=chat['name'],
                analysis_result=str(ai_result),
                unfulfilled_count=ai_result.get('unfulfilled_count', 0)
            )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())