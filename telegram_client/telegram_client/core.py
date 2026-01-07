# telegram_client/core.py - المكتبة الرئيسية

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon import functions, types
import asyncio
import json
import os
from typing import List, Dict, Optional

# ==================== الإعدادات ====================
class Config:
    """إعدادات الحسابات - تملأها في السورس"""
    
    # لحساب واحد
    API_ID = ""          # ⬅️ ضع الـ API ID هنا
    API_HASH = ""        # ⬅️ ضع الـ API Hash هنا
    PHONE = ""           # ⬅️ رقم الهاتف
    
    # لحسابات متعددة (اختياري)
    ACCOUNTS = []        # ⬅️ قائمة بالحسابات
    # مثال: 
    # ACCOUNTS = [
    #     {"phone": "+123", "api_id": "123", "api_hash": "abc"},
    #     {"phone": "+456", "api_id": "456", "api_hash": "def"}
    # ]
    
    # إعدادات إضافية
    TELEGRAM_ID = ""     # ⬅️ آيدي المالك
    SESSION_PREFIX = "session"  # ⬅️ بادئة الجلسات

# ==================== الأدوات المساعدة ====================
def parse_telegram_link(link: str) -> Dict:
    """تحليل روابط التليجرام"""
    link = link.strip()
    
    if link.startswith('+'):
        return {'type': 'invite', 'hash': link[1:]}
    elif link.startswith('https://t.me/joinchat/'):
        return {'type': 'invite', 'hash': link.split('/')[-1]}
    elif link.startswith('https://t.me/'):
        username = link[13:].split('?')[0]
        return {'type': 'username', 'username': username}
    elif link.startswith('@'):
        return {'type': 'username', 'username': link[1:]}
    else:
        return {'type': 'text', 'content': link}

# ==================== حساب واحد ====================
class TelegramUser:
    """مستخدم تلجرام واحد مع جميع الأوامر"""
    
    def __init__(self, account_num: int = 1, custom_config: Dict = None):
        self.account_num = account_num
        self.config = custom_config or self._get_config()
        self.client = None
        self.me = None
        self.tasks = {}
        self.tracking = False
        self.errors = {}
        
    def _get_config(self) -> Dict:
        """الحصول على إعدادات الحساب"""
        if Config.ACCOUNTS and len(Config.ACCOUNTS) >= self.account_num:
            return Config.ACCOUNTS[self.account_num - 1]
        else:
            return {
                "phone": Config.PHONE,
                "api_id": Config.API_ID,
                "api_hash": Config.API_HASH
            }
    
    async def start(self, phone: str = None):
        """بدء الاتصال بالحساب"""
        session_name = f"{Config.SESSION_PREFIX}_{self.account_num}"
        
        self.client = TelegramClient(
            session_name,
            int(self.config["api_id"]),
            self.config["api_hash"]
        )
        
        await self.client.start(phone=phone or self.config["phone"])
        self.me = await self.client.get_me()
        
        self._setup_all_handlers()
        print(f"✅ حساب {self.me.first_name} ({self.account_num}) جاهز!")
        return self
    
    def _setup_all_handlers(self):
        """تجهيز جميع الأوامر الأصلية"""
        
        # ========== أوامر النشر التلقائي ==========
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^s (\d+) (\d+)$'))
        async def swing_cmd(event):
            """s [ثواني] [عدد] - النشر التلقائي"""
            if self.errors.get(self.account_num):
                await event.edit(f"❌ الحساب معطل: {self.errors[self.account_num]}")
                return
                
            if event.is_reply:
                geteventText = event.text.split(" ")
                delay = int(geteventText[1])
                count = int(geteventText[2])
                chat_id = event.chat_id
                message = await event.get_reply_message()
                
                self.tasks[self.account_num] = True
                success = 0
                
                for i in range(count):
                    if not self.tasks.get(self.account_num, False):
                        break
                    
                    try:
                        await asyncio.sleep(delay)
                        await self.client.send_message(chat_id, message)
                        success += 1
                        
                        if (i+1) % 5 == 0:
                            await event.edit(f"📤 جاري النشر...\n✅ تم: {success}/{count}")
                            
                    except Exception as e:
                        self.errors[self.account_num] = str(e)
                        await event.edit(f"❌ خطأ: {str(e)[:100]}")
                        break
                
                self.tasks[self.account_num] = False
                await event.edit(f"✅ اكتمل النشر: {success}/{count}")
            else:
                await event.edit("⚠️ رد على رسالة لتكرارها")
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^sa (\d+) (\d+) (.+)$'))
        async def auto_post_specific(event):
            """sa [ثواني] [عدد] [رابط] - نشر في مكان محدد"""
            if self.errors.get(self.account_num):
                await event.edit(f"❌ الحساب معطل: {self.errors[self.account_num]}")
                return
                
            if event.is_reply:
                parts = event.text.split(maxsplit=3)
                if len(parts) < 4:
                    await event.edit("⚠️ صيغة: sa [ثواني] [عدد] [رابط]")
                    return
                    
                delay = int(parts[1])
                count = int(parts[2])
                target = parts[3]
                replied_msg = await event.get_reply_message()
                
                await event.edit(f"⏳ جاري التحضير...")
                
                try:
                    parsed = parse_telegram_link(target)
                    
                    if parsed['type'] == 'invite':
                        entity = await self.client(functions.messages.ImportChatInviteRequest(
                            hash=parsed['hash']
                        ))
                        chat_title = "المجموعة"
                    else:
                        entity = await self.client.get_entity(target)
                        chat_title = getattr(entity, 'title', 'الهدف')
                    
                    self.tasks[self.account_num] = True
                    success = 0
                    
                    for i in range(count):
                        if not self.tasks.get(self.account_num, False):
                            break
                        
                        try:
                            await self.client.send_message(entity, replied_msg)
                            success += 1
                            
                            if (i+1) % 3 == 0:
                                await event.edit(f"📤 ينشر في {chat_title}...\n✅ تم: {success}/{count}")
                            
                            if i < count - 1:
                                await asyncio.sleep(delay)
                                
                        except Exception as e:
                            await event.edit(f"❌ توقف: {str(e)[:100]}")
                            self.errors[self.account_num] = str(e)
                            break
                    
                    self.tasks[self.account_num] = False
                    await event.edit(f"✅ انتهى النشر في {chat_title}\n📊 النجاح: {success}/{count}")
                    
                except Exception as e:
                    await event.edit(f"❌ فشل الوصول: {str(e)[:100]}")
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.ن0$'))
        async def stop_auto_posting(event):
            """إيقاف النشر التلقائي"""
            if self.tasks.get(self.account_num, False):
                self.tasks[self.account_num] = False
                await event.edit("✅ تم إيقاف النشر")
            else:
                await event.edit("⚠️ لا يوجد نشر نشط")
        
        # ========== أوامر التتبع ==========
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.ح([01])$'))
        async def toggle_tracking(event):
            """تفعيل/تعطيل تتبع الردود"""
            state = int(event.pattern_match.group(1))
            self.tracking = bool(state)
            status = "✅ تم تفعيل" if state else "❌ تم تعطيل"
            await event.edit(f"{status} تتبع الردود")
        
        # ========== أوامر المعلومات ==========
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.الحالة$'))
        async def show_status(event):
            """عرض حالة الحساب"""
            status = [
                f"📊 حالة الحساب {self.account_num}:",
                f"👤 الاسم: {self.me.first_name}",
                f"📞 الرقم: {self.me.phone}",
                f"🆔 الآيدي: {self.me.id}",
                f"📈 مهام: {'نشط' if self.tasks.get(self.account_num) else 'متوقف'}",
                f"📍 تتبع: {'✅' if self.tracking else '❌'}",
                f"❌ أخطاء: {'لا' if not self.errors.get(self.account_num) else 'نعم'}"
            ]
            await event.edit('\n'.join(status))
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.جلسة$'))
        async def show_session(event):
            """عرض معلومات الجلسة"""
            session_str = StringSession.save(self.client.session)
            info = [
                f"🔐 جلسة الحساب {self.account_num}:",
                f"",
                f"{session_str[:50]}...",
                f"",
                f"💾 محفوظة تلقائياً"
            ]
            await event.edit('\n'.join(info))
        
        # ========== أوامر المجموعات ==========
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.انضمام (.+)$'))
        async def join_chat(event):
            """الانضمام لمجموعة/قناة"""
            target = event.pattern_match.group(1)
            await event.edit("⏳ جاري الانضمام...")
            
            try:
                parsed = parse_telegram_link(target)
                
                if parsed['type'] == 'invite':
                    await self.client(functions.messages.ImportChatInviteRequest(
                        hash=parsed['hash']
                    ))
                else:
                    entity = await self.client.get_entity(target)
                    await self.client(functions.channels.JoinChannelRequest(entity))
                
                await event.edit("✅ تم الانضمام")
            except Exception as e:
                await event.edit(f"❌ فشل: {str(e)[:80]}")
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.المجموعات$'))
        async def show_groups(event):
            """عرض المجموعات"""
            await event.edit("⏳ جاري الجلب...")
            groups = []
            
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    groups.append(f"• {dialog.title}")
                    if len(groups) >= 20:
                        break
            
            if groups:
                await event.edit("📋 مجموعاتك:\n" + "\n".join(groups[:10]))
            else:
                await event.edit("❌ لم تجد مجموعات")
        
        # ========== أوامر أخرى ==========
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.تحديث$'))
        async def update_profile(event):
            """تحديث الملف الشخصي"""
            self.me = await self.client.get_me()
            await event.edit(f"✅ تم تحديث بيانات: {self.me.first_name}")
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'^\.الاوامر$'))
        async def show_commands(event):
            """عرض جميع الأوامر"""
            commands = [
                "📜 جميع الأوامر الأصلية:",
                "",
                "🎯 النشر التلقائي:",
                "- s [ثواني] [عدد] - تكرار رسالة",
                "- sa [ثواني] [عدد] [رابط] - نشر في مكان محدد",
                "- .ن0 - إيقاف النشر",
                "",
                "🔔 التتبع:",
                "- .ح1 - تفعيل تتبع الردود",
                "- .ح0 - تعطيل تتبع الردود",
                "",
                "📊 المعلومات:",
                "- .الحالة - حالة الحساب",
                "- .جلسة - معلومات الجلسة",
                "- .تحديث - تحديث الملف الشخصي",
                "",
                "👥 المجموعات:",
                "- .انضمام [رابط] - الانضمام لمجموعة",
                "- .المجموعات - عرض مجموعاتك",
                "",
                "ℹ️ أخرى:",
                "- .الاوامر - هذه القائمة"
            ]
            await event.edit('\n'.join(commands))
        
        # ========== تتبع الردود ==========
        
        @self.client.on(events.NewMessage(incoming=True))
        async def track_replies(event):
            """تتبع الردود على رسائلك"""
            if not self.tracking:
                return
                
            if event.is_reply:
                replied_msg = await event.get_reply_message()
                if replied_msg and replied_msg.sender_id == self.me.id:
                    sender = await event.get_sender()
                    sender_name = getattr(sender, 'first_name', 'مستخدم')
                    
                    await self.client.send_message(
                        "me",
                        f"📨 رد جديد من {sender_name}:\n{event.text[:100] if event.text else 'وسائط'}"
                    )
    
    async def run(self):
        """تشغيل العميل"""
        await self.client.run_until_disconnected()
    
    async def disconnect(self):
        """قطع الاتصال"""
        await self.client.disconnect()

# ==================== حسابات متعددة ====================
class MultiAccounts:
    """إدارة حسابات متعددة"""
    
    def __init__(self):
        self.accounts: List[TelegramUser] = []
        self.running = False
        
    async def add_account(self, phone: str, api_id: str, api_hash: str) -> TelegramUser:
        """إضافة حساب جديد"""
        account_num = len(self.accounts) + 1
        user = TelegramUser(account_num, {
            "phone": phone,
            "api_id": api_id,
            "api_hash": api_hash
        })
        
        await user.start(phone)
        self.accounts.append(user)
        return user
    
    async def start_all(self, accounts_list: List[Dict] = None):
        """تشغيل جميع الحسابات"""
        if accounts_list:
            for acc in accounts_list:
                await self.add_account(
                    acc.get("phone", ""),
                    acc.get("api_id", ""),
                    acc.get("api_hash", "")
                )
        elif Config.ACCOUNTS:
            for acc in Config.ACCOUNTS:
                await self.add_account(
                    acc.get("phone", ""),
                    acc.get("api_id", ""),
                    acc.get("api_hash", "")
                )
        else:
            raise ValueError("لا توجد حسابات محددة")
        
        self.running = True
        print(f"✅ تم تشغيل {len(self.accounts)} حساب")
        
    async def stop_all(self):
        """إيقاف جميع الحسابات"""
        for account in self.accounts:
            await account.disconnect()
        self.accounts.clear()
        self.running = False
        print("⏹ توقفت جميع الحسابات")
    
    async def run_all(self):
        """تشغيل جميع الحسابات بالتوازي"""
        if not self.accounts:
            await self.start_all()
        
        tasks = [account.run() for account in self.accounts]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_account(self, account_num: int) -> Optional[TelegramUser]:
        """الحصول على حساب معين"""
        if 1 <= account_num <= len(self.accounts):
            return self.accounts[account_num - 1]
        return None

# ==================== اختصارات سريعة ====================
class TU:
    """اختصار TelegramUser (لحساب واحد)"""
    
    @staticmethod
    def create(num: int = 1):
        """إنشاء مستخدم جديد"""
        return TelegramUser(account_num=num)
    
    @staticmethod
    async def connect(num: int = 1):
        """الاتصال المباشر"""
        user = TelegramUser(account_num=num)
        return await user.start()

class MA:
    """اختصار MultiAccounts (لحسابات متعددة)"""
    
    @staticmethod
    def create():
        """إنشاء مدير حسابات متعددة"""
        return MultiAccounts()
    
    @staticmethod
    async def connect_all():
        """الاتصال بجميع الحسابات"""
        manager = MultiAccounts()
        await manager.start_all()
        return manager

# ==================== دوال التشغيل ====================
async def run_single(account_num: int = 1, phone: str = None):
    """تشغيل حساب واحد"""
    user = TU.create(account_num)
    await user.start(phone)
    await user.run()

async def run_multi():
    """تشغيل حسابات متعددة"""
    manager = MA.create()
    await manager.run_all()

async def quick_run():
    """تشغيل سريع (يتحقق من الإعدادات)"""
    if Config.ACCOUNTS and len(Config.ACCOUNTS) > 0:
        print(f"🚀 تشغيل {len(Config.ACCOUNTS)} حساب...")
        await run_multi()
    elif Config.API_ID and Config.API_HASH:
        print("🚀 تشغيل حساب واحد...")
        await run_single()
    else:
        print("❌ لا توجد إعدادات للحسابات!")