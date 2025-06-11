import openai
import json 
from datetime import datetime, timedelta 

class AiAnalizer:
    def __init__(self, api_key):
        openai.api_key = api_key
    
    def analyze_conversation(self, messages):
        """
        Аналізує розмову за допомогою OpenAI API.
        """
        # Підготовка тексту для аналізу
        conversation_text = self._prepare_conversation_text(messages)
        
        prompt = f"""
        Проаналізуй наступну розмову між менеджером та клієнтом.
        
        Розмова:
        {conversation_text}
        
        Завдання:
        1. Знайди всі обіцянки менеджера щодо термінів виконання (до кінця дня, завтра, через годину тощо)
        2. Перевір, чи були ці обіцянки виконані в зазначені терміни
        3. Визнач, чи є невиконані обіцянки
        
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
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ти експерт з аналізу ділових розмов. Аналізуй українською мовою."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
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