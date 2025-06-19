from openai import OpenAI
import json
from datetime import datetime

class AiAnalizer:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def analyze_conversation(self, messages):
        conversation_text = self._prepare_conversation_text(messages)

        prompt = f"""
        Проаналізуй наступну розмову між менеджером та клієнтом.

        Розмова:
        {conversation_text}

        Завдання:
        1. Знайди всі обіцянки менеджера щодо термінів виконання (до кінця дня, завтра, через годину тощо)
        2. Перевір, чи були ці обіцянки виконані в зазначені терміни
        3. Визнач, чи є невиконані обіцянки
        4. Підготуй короткий висновок щодо виконання обіцянок
        5 Кількість невиконаних обіцянок
        6.Кількість обіцянок, які були виконані вчасно
        7. Кількість обіцянок, які були виконані із запізненням
        8. Кількість обіцянок, які не були виконані
        10.Кількість повідолень 
        11. Кількість повідомлень, в яких були обіцянки
        12. Кількість повідомлень, в яких не було обіцянок

        Поверни результат у JSON форматі:
        {{
            "promises_found": true/false,
            "promises": [
                {{
                    "promise_text": "текст обіцянки",
                    "deadline": "термін виконання",
                    "date_promised": "дата обіцянки",
                    "fulfilled": true/false,
                    "reason": "причина чому не виконано"
                }}
            ],
            "unfulfilled_count": число_невиконаних_обіцянок,
            "analysis_summary": "короткий висновок"
        }}
        """

        try:
            completion = self.client.chat.completions.create(
                model="deepseek/deepseek-r1-0528:free",
                messages=[
                    {"role": "system", "content": "Ти експерт з аналізу ділових розмов. Аналізуй українською мовою."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            response = completion.choices[0].message.content
            print("AI відповідь:", response)  # Діагностика

            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                print("Помилка: AI повернув невалідний JSON.")
                return None

        except Exception as e:
            print(f"Помилка AI аналізу: {e}")
            return None


    def _prepare_conversation_text(self, messages):
        """Підготовка тексту розмови"""
        conversation = []
        for msg in messages:
            sender = "Менеджер" if msg['from_me'] else "Клієнт"
            date_str = msg['date'].strftime("%Y-%m-%d %H:%M")
            conversation.append(f"[{date_str}] {sender}: {msg['text']}")
        return "\n".join(conversation)