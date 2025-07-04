# telegram_analyzer

## Опис проєкту

**telegram_analyzer** — це інструмент для автоматичного аналізу історії чатів у Telegram. Проєкт дозволяє:
- отримувати історію чатів менеджера з клієнтами,
- знаходити потенційні обіцянки менеджера,
- перевіряти виконання обіцянок у зазначені терміни,
- формувати звіти про невиконані обіцянки,
- зберігати результати аналізу у базу даних.

## Основні можливості

- Підключення до Telegram через Telethon.
- Завантаження історії чатів за обраний період.
- Фільтрація та попередня обробка повідомлень.
- Виявлення обіцянок менеджера (на основі ключових слів і часових згадок).
- Перевірка виконання обіцянок.
- Збереження результатів у SQLite базу.
- Формування текстових звітів.

## Структура проєкту

## Опис основних модулів

- **main.py**  
  Запускає аналіз, керує підключенням до Telegram, обробкою повідомлень, пошуком обіцянок, формуванням звітів.

- **config/settings.py**  
  Завантажує налаштування з `.env` (API ID, API HASH, номер телефону).

- **src/telegram_client.py**  
  Клас `TelegramAnalyzer` — підключення до Telegram, отримання списку чатів, історії повідомлень.

- **src/message_analyzer.py**  
  Клас `MessageProcessor` — фільтрація, групування, пошук обіцянок, підготовка даних для AI.

- **src/ai_analyzer.py**  
  (Опціонально) Клас для аналізу розмови через OpenAI API.

- **src/database.py**  
  Клас `Database` — створення таблиць, збереження результатів аналізу.

## Як обробляються дані

1. **Підключення до Telegram**  
   Через Telethon, використовуючи ваші API ID, HASH та номер телефону.

2. **Завантаження історії чатів**  
   Отримання останніх чатів та повідомлень за обраний період.

3. **Обробка повідомлень**  
   - Фільтрація спаму, системних і неінформативних повідомлень.
   - Групування за контекстом.
   - Пошук ключових слів, що вказують на обіцянки та часові рамки.

4. **Аналіз обіцянок**  
   - Виявлення потенційних обіцянок менеджера.
   - Перевірка виконання обіцянок (чи є повідомлення про виконання, чи прострочено).

5. **Збереження та звіти**  
   - Збереження результатів у базу даних.
   - Формування текстових звітів у консоль та лог-файл.


**Проєкт призначений для автоматизації контролю виконання обіцянок менеджерів у Telegram-чатах з клієнтами.**