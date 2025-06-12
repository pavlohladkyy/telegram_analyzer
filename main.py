import asyncio
from src.telegram_client import TelegramAnalyzer
from src.message_analyzer import MessageProcessor
from config.settings import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
from src.database import Database
import json
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
        date = message.date.strftime('%Y-%m-%d %H:%M:%S')
        sender = "Менеджер" if message.from_me else "Клієнт"
        print(f"{date} - {sender}: {message.text}")

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

def print_potential_promises(potential_promises):
    """Виведення потенційних обіцянок"""
    if not potential_promises:
        print("✅ Потенційних обіцянок не виявлено.")
        return
    
    print(f"\n⚠️ Виявлено {len(potential_promises)} потенційних обіцянок:")
    
    for i, promise in enumerate(potential_promises, 1):
        print(f"\n🔸 Обіцянка #{i} (Скор: {promise['total_score']}):")
        print(f"   📅 Дата: {promise['message'].date.strftime('%Y-%m-%d %H:%M')}")
        print(f"   💬 Повідомлення: {promise['message'].text[:100]}...")
        
        if promise['extracted_promises']:
            print(f"   📋 Знайдено обіцянки:")
            for p in promise['extracted_promises']:
                print(f"      - {p}")
        
        if promise['extracted_times']:
            print(f"   ⏰ Часові згадки:")
            for t in promise['extracted_times']:
                print(f"      - {t['keyword']}: {t['context']}")

def print_message_groups(message_groups):
    """Виведення груп повідомлень за контекстом"""
    if not message_groups:
        return
    
    print(f"\n📱 Розмова розділена на {len(message_groups)} блоків:")
    
    for i, group in enumerate(message_groups, 1):
        duration = group['duration_minutes']
        print(f"   Блок #{i}: {group['start_time'].strftime('%H:%M')} - {group['end_time'].strftime('%H:%M')} "
              f"({duration:.0f} хв, {group['total_messages']} повідомлень)")

def check_promise_fulfillment(potential_promises, conversation):
    """Простий алгоритм перевірки виконання обіцянок"""
    unfulfilled_promises = []
    
    for promise_data in potential_promises:
        promise_msg = promise_data['message']
        promise_time = promise_msg.date
        
        # Ключові слова що можуть вказувати на виконання
        fulfillment_keywords = [
            'надіслав', 'відправив', 'скинув', 'готово', 'зроблено',
            'виконано', 'прикріпив', 'ось', 'тримай', 'дивись'
        ]
        
        # Шукаємо повідомлення після обіцянки що можуть вказувати на виконання
        fulfilled = False
        for msg in conversation.messages:
            if (msg.from_me and 
                msg.date > promise_time and 
                (msg.date - promise_time).days <= 7):  # В межах тижня
                
                msg_lower = msg.text.lower()
                if any(keyword in msg_lower for keyword in fulfillment_keywords):
                    fulfilled = True
                    break
        
        if not fulfilled:
            # Визначаємо приблизний термін на основі тексту обіцянки
            deadline = estimate_deadline(promise_msg.text, promise_time)
            
            unfulfilled_promises.append({
                'message': promise_msg,
                'extracted_promises': promise_data['extracted_promises'],
                'estimated_deadline': deadline,
                'days_overdue': (datetime.now() - deadline).days if deadline < datetime.now() else 0,
                'total_score': promise_data['total_score']
            })
    
    return unfulfilled_promises

def estimate_deadline(promise_text, promise_date):
    """Оцінка терміну виконання обіцянки на основі тексту"""
    text_lower = promise_text.lower()
    
    # Конкретні терміни
    if any(word in text_lower for word in ['сьогодні', 'до кінця дня']):
        return promise_date.replace(hour=18, minute=0, second=0)
    elif 'завтра' in text_lower:
        return promise_date + timedelta(days=1)
    elif any(word in text_lower for word in ['до п\'ятниці', 'до кінця тижня']):
        days_to_friday = (4 - promise_date.weekday()) % 7
        return promise_date + timedelta(days=days_to_friday)
    elif 'наступного тижня' in text_lower:
        return promise_date + timedelta(days=7)
    elif any(word in text_lower for word in ['через годину', 'за годину']):
        return promise_date + timedelta(hours=1)
    elif 'через день' in text_lower:
        return promise_date + timedelta(days=1)
    else:
        # За замовчуванням - 3 дні
        return promise_date + timedelta(days=3)

def print_unfulfilled_promises(unfulfilled_promises, chat_name):
    """Виведення невиконаних обіцянок"""
    if not unfulfilled_promises:
        print(f"✅ У чаті з {chat_name}: невиконаних обіцянок не знайдено!")
        return
    
    print(f"\n⚠️ У чаті з {chat_name} знайдено {len(unfulfilled_promises)} невиконаних обіцянок:")
    
    for i, promise in enumerate(unfulfilled_promises, 1):
        print(f"\n🔸 Невиконана обіцянка #{i}:")
        print(f"   📅 Дата обіцянки: {promise['message'].date.strftime('%Y-%m-%d %H:%M')}")
        print(f"   ⏰ Очікуваний термін: {promise['estimated_deadline'].strftime('%Y-%m-%d %H:%M')}")
        
        if promise['days_overdue'] > 0:
            print(f"   🚨 Прострочено на {promise['days_overdue']} днів")
        
        print(f"   💬 Повідомлення: {promise['message'].text}")
        
        if promise['extracted_promises']:
            print(f"   📋 Конкретні обіцянки:")
            for p in promise['extracted_promises']:
                print(f"      - {p}")

async def main():
    telegram = TelegramAnalyzer(TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE)
    db = Database()
    message_processor = MessageProcessor()
    
    all_unfulfilled_promises = []
    
    try:
        # Підключення до Telegram
        await telegram.connect()
        
        # Отримання останніх чатів
        print("Отримання останніх чатів...")
        recent_chats = await telegram.get_recent_chats(limit=5)
        print_chat_history(recent_chats)

        for chat in recent_chats:
            print(f"\n{'='*60}")
            print(f"🔍 Аналіз чату з {chat['name']}...")
            print(f"{'='*60}")

            # Отримання історії повідомлень за тиждень
            raw_messages = await telegram.get_chat_history(chat['id'], days_back=7)
            
            if not raw_messages:
                print("Повідомлення відсутні у цьому чаті.")
                continue
            
            # Обробка повідомлень через MessageProcessor
            conversation = message_processor.process_messages(raw_messages)
            conversation.chat_name = chat['name']
            
            # Виведення базової інформації
            print(f"📥 Отримано {len(raw_messages)} сирих повідомлень")
            print(f"✅ Після фільтрації залишилось {conversation.total_messages} повідомлень")
            
            if conversation.total_messages == 0:
                print("Після фільтрації повідомлень не залишилось.")
                continue
            
            # Аналіз розмови
            print_conversation_analysis(conversation)
            
            # Пошук потенційних обіцянок
            potential_promises = message_processor.find_potential_promises(conversation)
            print_potential_promises(potential_promises)
            
            # Групування повідомлень
            message_groups = message_processor.group_messages_by_context(conversation)
            print_message_groups(message_groups)
            
            # Перевірка виконання обіцянок
            unfulfilled = check_promise_fulfillment(potential_promises, conversation)
            print_unfulfilled_promises(unfulfilled, chat['name'])
            
            # Збереження в базу даних
            try:
                db.save_analysis(chat['id'], chat['name'])
                
                # Логування
                with open("logs/logs.txt", "a", encoding="utf-8") as log_file:
                    log_file.write(f"Чат: {chat['name']} (ID: {chat['id']}) - "
                                 f"Повідомлень: {conversation.total_messages}, "
                                 f"Потенційних обіцянок: {len(potential_promises)}, "
                                 f"Невиконаних: {len(unfulfilled)}\n")
            
            except Exception as e:
                print(f"Помилка збереження в БД: {e}")
            
            # Додавання до загального списку
            if unfulfilled:
                all_unfulfilled_promises.extend([{
                    'chat_name': chat['name'],
                    'chat_id': chat['id'],
                    'promises': unfulfilled
                }])

        # Підсумковий звіт
        print_final_report(all_unfulfilled_promises)

    except Exception as e:
        print(f"Помилка: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await telegram.client.disconnect()

def print_final_report(all_unfulfilled_promises):
    """Виведення підсумкового звіту"""
    print(f"\n{'='*80}")
    print("📊 ПІДСУМКОВИЙ ЗВІТ")
    print(f"{'='*80}")
    
    if not all_unfulfilled_promises:
        print("🎉 Чудові новини! Невиконаних обіцянок не знайдено в жодному чаті!")
        return
    
    total_unfulfilled = sum(len(chat['promises']) for chat in all_unfulfilled_promises)
    
    print(f"⚠️  Загалом знайдено {total_unfulfilled} невиконаних обіцянок у {len(all_unfulfilled_promises)} чатах:")
    
    for chat_data in all_unfulfilled_promises:
        print(f"\n🔸 {chat_data['chat_name']}: {len(chat_data['promises'])} невиконаних обіцянок")
        
        # Найкритичніші (найбільш прострочені)
        overdue_promises = [p for p in chat_data['promises'] if p['days_overdue'] > 0]
        if overdue_promises:
            max_overdue = max(overdue_promises, key=lambda x: x['days_overdue'])
            print(f"   🚨 Найбільше прострочено: {max_overdue['days_overdue']} днів")
    
    print(f"\n💡 Рекомендації:")
    print("1. Зв'яжіться з клієнтами для уточнення статусу обіцянок")
    print("2. Встановіть нагадування для майбутніх обіцянок")
    print("3. Розгляньте можливість автоматизації процесів")

if __name__ == "__main__":
    asyncio.run(main())