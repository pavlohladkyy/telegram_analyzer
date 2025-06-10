from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel
from datetime import datetime, timedelta
import asyncio

class TelegramAnalyzer:
    def __init__(self, api_id, api_hash, phone):
        self.client = TelegramClient('session', api_id, api_hash)
        self.phone = phone
    
    async def connect(self):
        await self.client.start(phone=self.phone)
        print("Підключено до Telegram")
    
    async def get_recent_chats(self, limit=10):
        """Отримати останні чати"""
        dialogs = []
        async for dialog in self.client.iter_dialogs(limit=limit):
            if isinstance(dialog.entity, User): 
                dialogs.append({
                    'id': dialog.entity.id,
                    'name': dialog.entity.first_name or dialog.entity.username,
                    'username': dialog.entity.username,
                    'dialog': dialog
                })
        return dialogs
    
    async def get_chat_history(self, chat_id, days_back=30):
        """Отримати історію чату за останній місяць"""
        start_date = datetime.now() - timedelta(days=days_back)
        messages = []
        
        async for message in self.client.iter_messages(
            chat_id, 
            offset_date=start_date,
            reverse=True
        ):
            if message.text:
                messages.append({
                    'id': message.id,
                    'date': message.date,
                    'text': message.text,
                    'from_me': message.out,
                    'chat_id': chat_id
                })
        return messages