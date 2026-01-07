# telegram_multi_client/core.py - المكتبة الرئيسية

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon import functions, types
import asyncio

# ==================== الإعدادات ====================
class Config:
    """إعدادات الحسابات"""
    API_ID = ""
    API_HASH = ""
    PHONE = ""
    ACCOUNTS = []
    TELEGRAM_ID = ""
    SESSION_PREFIX = "session"

# ==================== حساب واحد ====================
class TelegramUser:
    def __init__(self, account_num=1):
        self.account_num = account_num
        self.client = None
        self.me = None
    
    async def start(self):
        session_name = f"{Config.SESSION_PREFIX}_{self.account_num}"
        self.client = TelegramClient(session_name, int(Config.API_ID), Config.API_HASH)
        await self.client.start(phone=Config.PHONE)
        self.me = await self.client.get_me()
        print(f"✅ {self.me.first_name} جاهز!")
        return self
    
    async def run(self):
        await self.client.run_until_disconnected()

# ==================== اختصارات ====================
TU = TelegramUser

async def quick_run():
    user = TU()
    await user.start()
    await user.run()

# ==================== للاستيراد ====================
__all__ = ['Config', 'TelegramUser', 'TU', 'quick_run']
