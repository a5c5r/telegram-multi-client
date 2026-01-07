"""
Telegram Multi-Client - مكتبة متعددة الحسابات بأوامر عربية
GitHub: https://github.com/username/telegram-multi-client
"""

from .core import (
    # الإعدادات
    Config,
    
    # الفئات الرئيسية
    TelegramUser,
    MultiAccounts,
    
    # الاختصارات
    TU,
    MA,
    
    # دوال التشغيل
    quick_run,
    run_single,
    run_multi,
    
    # أدوات مساعدة
    parse_telegram_link
)

__version__ = "2.0.0"
__author__ = "Your Name"

print(f"✅ Telegram Multi-Client v{__version__} loaded")