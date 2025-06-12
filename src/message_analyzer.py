# src/message_analyzer.py

"""
Модуль для попередньої обробки та аналізу повідомлень перед передачею до AI.
Виконує фільтрацію, групування та підготовку даних для більш ефективного AI аналізу.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Структура для зберігання інформації про повідомлення"""
    id: int
    date: datetime
    text: str
    from_me: bool
    chat_id: int
    reply_to: Optional[int] = None
    forwarded_from: Optional[str] = None


@dataclass
class Conversation:
    """Структура для зберігання діалогу"""
    chat_id: int
    chat_name: str
    messages: List[Message]
    start_date: datetime
    end_date: datetime
    total_messages: int
    manager_messages: int
    client_messages: int


class MessageProcessor:
    """
    Клас для обробки та аналізу повідомлень перед AI аналізом.
    
    Основні функції:
    1. Фільтрація повідомлень (видалення спаму, системних повідомлень)
    2. Групування повідомлень за датами
    3. Пошук ключових слів що вказують на обіцянки
    4. Визначення контексту розмови
    5. Підготовка даних для AI
    """
    
    def __init__(self):
        self.promise_keywords = self._load_promise_keywords()
        self.time_keywords = self._load_time_keywords()
        self.business_keywords = self._load_business_keywords()
    
    def _load_promise_keywords(self) -> List[str]:
        """Ключові слова що вказують на обіцянки менеджера"""
        return [
            # Прямі обіцянки
            'зроблю', 'підготую', 'надішлю', 'скину', 'відправлю',
            'прорахую', 'розрахую', 'перевірю', 'уточню', 'дізнаюся',
            'зателефоную', 'подзвоню', 'напишу', 'повідомлю',
            
            # Зобов'язання
            'обов\'язково', 'точно', 'гарантую', 'обіцяю',
            'без проблем', 'звичайно', 'так, зроблю',
            
            # Дії з документами
            'підготую договір', 'надішлю пропозицію', 'скину прайс',
            'відправлю кошторис', 'зроблю розрахунок',
            
            # Зустрічі та дзвінки  
            'зустрінемося', 'домовимося', 'призначу зустріч',
            'зателефоную', 'передзвоню'
        ]
    
    def _load_time_keywords(self) -> List[str]:
        """Ключові слова що вказують на часові рамки"""
        return [
            # Конкретний час
            'до кінця дня', 'до кінця робочого дня', 'сьогодні до вечора',
            'завтра', 'післязавтра', 'до п\'ятниці', 'до понеділка',
            'на наступному тижні', 'до обіду', 'після обіду',
            
            # Відносний час
            'через годину', 'через пару годин', 'через день',
            'за годину', 'за пару хвилин', 'незабаром', 'скоро',
            
            # Конкретний час
            'о 15:00', 'до 18:00', 'вранці', 'ввечері',
            'до закриття', 'до обідньої перерви'
        ]
    
    def _load_business_keywords(self) -> List[str]:
        """Ключові слова ділового контексту"""
        return [
            'прайс', 'кошторис', 'договір', 'рахунок', 'пропозиція',
            'презентація', 'зустріч', 'переговори', 'угода',
            'замовлення', 'послуга', 'товар', 'доставка',
            'оплата', 'розрахунок', 'вартість', 'ціна'
        ]
    
    def process_messages(self, raw_messages: List[Dict]) -> Conversation:
        """
        Основна функція обробки повідомлень.
        
        Args:
            raw_messages: Список сирих повідомлень з Telegram API
            
        Returns:
            Оброблений об'єкт Conversation
        """
        # Конвертація в структуровані повідомлення
        messages = self._convert_to_messages(raw_messages)
        
        # Фільтрація непотрібних повідомлень
        filtered_messages = self._filter_messages(messages)
        
        # Сортування за датою
        filtered_messages.sort(key=lambda x: x.date)
        
        # Створення об'єкта розмови
        if filtered_messages:
            conversation = Conversation(
                chat_id=filtered_messages[0].chat_id,
                chat_name="",  # Буде встановлено пізніше
                messages=filtered_messages,
                start_date=filtered_messages[0].date,
                end_date=filtered_messages[-1].date,
                total_messages=len(filtered_messages),
                manager_messages=len([m for m in filtered_messages if m.from_me]),
                client_messages=len([m for m in filtered_messages if not m.from_me])
            )
        else:
            conversation = Conversation(
                chat_id=raw_messages[0]['chat_id'] if raw_messages else 0,
                chat_name="",
                messages=[],
                start_date=datetime.now(),
                end_date=datetime.now(),
                total_messages=0,
                manager_messages=0,
                client_messages=0
            )
        
        return conversation
    
    def _convert_to_messages(self, raw_messages: List[Dict]) -> List[Message]:
        """Конвертація сирих повідомлень у структуровані об'єкти"""
        messages = []
        
        for msg in raw_messages:
            try:
                message = Message(
                    id=msg.get('id', 0),
                    date=msg.get('date', datetime.now()),
                    text=msg.get('text', ''),
                    from_me=msg.get('from_me', False),
                    chat_id=msg.get('chat_id', 0),
                    reply_to=msg.get('reply_to'),
                    forwarded_from=msg.get('forwarded_from')
                )
                messages.append(message)
            except Exception as e:
                logger.warning(f"Помилка обробки повідомлення: {e}")
                continue
        
        return messages
    
    def _filter_messages(self, messages: List[Message]) -> List[Message]:
        """
        Фільтрація повідомлень від спаму та непотрібного контенту.
        
        Видаляє:
        - Системні повідомлення
        - Дуже короткі повідомлення (менше 3 символів)
        - Повідомлення тільки з emoji
        - Пересланні повідомлення (опціонально)
        - Технічні повідомлення
        """
        filtered = []
        
        for msg in messages:
            # Пропуск порожніх повідомлень
            if not msg.text or len(msg.text.strip()) < 3:
                continue
            
            # Пропуск повідомлень тільки з emoji
            if self._is_only_emoji(msg.text):
                continue
            
            # Пропуск системних повідомлень
            if self._is_system_message(msg.text):
                continue
            
            # Пропуск спам повідомлень
            if self._is_spam_message(msg.text):
                continue
            
            filtered.append(msg)
        
        return filtered
    
    def _is_only_emoji(self, text: str) -> bool:
        """Перевірка чи містить текст тільки emoji"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002500-\U00002BEF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"
            "\u3030"
            "\s"  # пробіли
            "]+"
        )
        
        cleaned_text = emoji_pattern.sub('', text).strip()
        return len(cleaned_text) == 0
    
    def _is_system_message(self, text: str) -> bool:
        """Перевірка системних повідомлень"""
        system_patterns = [
            r'приєднався до групи',
            r'залишив групу',
            r'змінив назву групи',
            r'встановив фото групи',
            r'видалив фото групи'
        ]
        
        for pattern in system_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _is_spam_message(self, text: str) -> bool:
        """Перевірка спам повідомлень"""
        spam_indicators = [
            len(text) > 1000,  # Дуже довгі повідомлення
            text.count('http') > 3,  # Багато посилань
            len(re.findall(r'[A-Z]', text)) / len(text) > 0.7 if text else False,  # Багато великих літер
        ]
        
        return any(spam_indicators)
    
    def find_potential_promises(self, conversation: Conversation) -> List[Dict]:
        """
        Пошук потенційних обіцянок менеджера.
        
        Returns:
            Список повідомлень з потенційними обіцянками
        """
        potential_promises = []
        
        for msg in conversation.messages:
            if not msg.from_me:  # Тільки повідомлення менеджера
                continue
            
            # Пошук ключових слів обіцянок
            promise_score = self._calculate_promise_score(msg.text)
            time_score = self._calculate_time_score(msg.text)
            business_score = self._calculate_business_score(msg.text)
            
            total_score = promise_score + time_score + business_score
            
            if total_score > 2:  # Поріг для потенційної обіцянки
                potential_promises.append({
                    'message': msg,
                    'promise_score': promise_score,
                    'time_score': time_score,
                    'business_score': business_score,
                    'total_score': total_score,
                    'extracted_promises': self._extract_promise_text(msg.text),
                    'extracted_times': self._extract_time_mentions(msg.text)
                })
        
        # Сортування за загальним скором
        potential_promises.sort(key=lambda x: x['total_score'], reverse=True)
        
        return potential_promises
    
    def _calculate_promise_score(self, text: str) -> int:
        """Розрахунок скору обіцянок у тексті"""
        score = 0
        text_lower = text.lower()
        
        for keyword in self.promise_keywords:
            if keyword in text_lower:
                score += 1
        
        return score
    
    def _calculate_time_score(self, text: str) -> int:
        """Розрахунок скору часових згадок"""
        score = 0
        text_lower = text.lower()
        
        for keyword in self.time_keywords:
            if keyword in text_lower:
                score += 2  # Часові згадки більш важливі
        
        return score
    
    def _calculate_business_score(self, text: str) -> int:
        """Розрахунок скору ділового контексту"""
        score = 0
        text_lower = text.lower()
        
        for keyword in self.business_keywords:
            if keyword in text_lower:
                score += 1
        
        return score
    
    def _extract_promise_text(self, text: str) -> List[str]:
        """Витягування тексту обіцянок"""
        promises = []
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # Перевірка чи містить речення ключові слова обіцянок
            if any(keyword in sentence.lower() for keyword in self.promise_keywords):
                promises.append(sentence)
        
        return promises
    
    def _extract_time_mentions(self, text: str) -> List[Dict]:
        """Витягування згадок часу"""
        time_mentions = []
        
        for keyword in self.time_keywords:
            if keyword in text.lower():
                # Знаходимо позицію ключового слова
                start_pos = text.lower().find(keyword)
                if start_pos != -1:
                    time_mentions.append({
                        'keyword': keyword,
                        'context': text[max(0, start_pos-20):start_pos+len(keyword)+20],
                        'position': start_pos
                    })
        
        return time_mentions
    
    def group_messages_by_context(self, conversation: Conversation) -> List[Dict]:
        """
        Групування повідомлень за контекстом розмови.
        
        Створює логічні блоки розмови на основі часових проміжків
        та зміни тем.
        """
        if not conversation.messages:
            return []
        
        groups = []
        current_group = []
        last_message_time = None
        
        for msg in conversation.messages:
            # Новий блок якщо пройшло більше 2 годин з останнього повідомлення
            if (last_message_time and 
                (msg.date - last_message_time).total_seconds() > 7200):  # 2 години
                
                if current_group:
                    groups.append(self._create_message_group(current_group))
                    current_group = []
            
            current_group.append(msg)
            last_message_time = msg.date
        
        # Додаємо останню групу
        if current_group:
            groups.append(self._create_message_group(current_group))
        
        return groups
    
    def _create_message_group(self, messages: List[Message]) -> Dict:
        """Створення групи повідомлень"""
        return {
            'start_time': messages[0].date,
            'end_time': messages[-1].date,
            'messages': messages,
            'duration_minutes': (messages[-1].date - messages[0].date).total_seconds() / 60,
            'manager_messages': len([m for m in messages if m.from_me]),
            'client_messages': len([m for m in messages if not m.from_me]),
            'total_messages': len(messages)
        }
    
    def prepare_for_ai_analysis(self, conversation: Conversation) -> Dict:
        """
        Підготовка даних для передачі до AI аналізатора.
        
        Створює структурований опис розмови з виділенням
        найважливіших елементів для аналізу.
        """
        # Пошук потенційних обіцянок
        potential_promises = self.find_potential_promises(conversation)
        
        # Групування за контекстом
        message_groups = self.group_messages_by_context(conversation)
        
        # Підготовка структурованого тексту
        formatted_conversation = self._format_conversation_for_ai(conversation)
        
        return {
            'conversation_text': formatted_conversation,
            'metadata': {
                'chat_id': conversation.chat_id,
                'total_messages': conversation.total_messages,
                'manager_messages': conversation.manager_messages,
                'client_messages': conversation.client_messages,
                'conversation_duration_days': (conversation.end_date - conversation.start_date).days,
                'start_date': conversation.start_date.isoformat(),
                'end_date': conversation.end_date.isoformat()
            },
            'potential_promises': potential_promises,
            'message_groups': message_groups,
            'analysis_hints': self._generate_analysis_hints(potential_promises)
        }
    
    def _format_conversation_for_ai(self, conversation: Conversation) -> str:
        """Форматування розмови для AI"""
        formatted_lines = []
        
        for msg in conversation.messages:
            sender = "Менеджер" if msg.from_me else "Клієнт"
            timestamp = msg.date.strftime("%Y-%m-%d %H:%M")
            
            formatted_lines.append(f"[{timestamp}] {sender}: {msg.text}")
        
        return "\n".join(formatted_lines)
    
    def _generate_analysis_hints(self, potential_promises: List[Dict]) -> List[str]:
        """Генерація підказок для AI аналізу"""
        hints = []
        
        if potential_promises:
            hints.append("У розмові виявлено потенційні обіцянки менеджера")
            
            for promise in potential_promises[:3]:  # Топ 3 обіцянки
                hints.append(f"Перевір виконання: {promise['extracted_promises']}")
        
        return hints