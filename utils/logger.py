"""
📝 نظام التسجيل (Logging)
=====================================
يوفر نظام تسجيل موحد ومنظم للتطبيق

المسؤوليات:
- تسجيل الأحداث والأخطاء
- حفظ السجلات في ملفات
- عرض السجلات في الواجهة
- إدارة السجلات القديمة

الاستخدام:
    from src.utils.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("رسالة معلومات")
    logger.error("رسالة خطأ")
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Optional

from ..config.settings import settings


class ColoredFormatter(logging.Formatter):
    """
    Formatter مع ألوان للطرفية (Console)
    """
    
    # رموز الألوان ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    # رموز بديلة (emojis) للأنظمة التي تدعمها
    ICONS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }
    
    def format(self, record):
        """تنسيق السجل مع الألوان"""
        # إضافة اللون
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}"
                f"{self.ICONS.get(levelname, '')} {levelname}"
                f"{self.COLORS['RESET']}"
            )
        
        return super().format(record)


class LoggerManager:
    """
    مدير السجلات الرئيسي
    """
    
    _loggers = {}  # Cache للـ loggers
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        log_to_file: bool = True,
        log_to_console: bool = True
    ) -> logging.Logger:
        """
        الحصول على logger
        
        Args:
            name: اسم الـ logger (عادة __name__)
            log_to_file: حفظ في ملف؟
            log_to_console: عرض في الطرفية؟
            
        Returns:
            logging.Logger: الـ logger
        """
        # إذا كان موجوداً، أعده
        if name in cls._loggers:
            return cls._loggers[name]
        
        # إنشاء logger جديد
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        # منع التكرار
        logger.propagate = False
        
        # إزالة handlers القديمة
        logger.handlers.clear()
        
        # ═══════════════════════════════════════════════════
        # 📺 Console Handler
        # ═══════════════════════════════════════════════════
        
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            
            # استخدام formatter ملون
            console_formatter = ColoredFormatter(
                fmt='%(levelname)s %(asctime)s [%(name)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # ═══════════════════════════════════════════════════
        # 📁 File Handler
        # ═══════════════════════════════════════════════════
        
        if log_to_file:
            # التأكد من وجود مجلد السجلات
            settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            
            # ملف السجل اليومي
            log_file = settings.LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
            
            # File handler مع rotation يومي
            file_handler = TimedRotatingFileHandler(
                filename=log_file,
                when='midnight',
                interval=1,
                backupCount=settings.LOG_RETENTION_DAYS,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Formatter عادي للملف
            file_formatter = logging.Formatter(
                fmt=settings.LOG_FORMAT,
                datefmt=settings.LOG_DATE_FORMAT
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # حفظ في الـ cache
        cls._loggers[name] = logger
        
        return logger
    
    @classmethod
    def clean_old_logs(cls, days: Optional[int] = None):
        """
        حذف السجلات القديمة
        
        Args:
            days: عدد الأيام للاحتفاظ بالسجلات
        """
        if days is None:
            days = settings.LOG_RETENTION_DAYS
        
        if not settings.LOGS_DIR.exists():
            return
        
        now = datetime.now()
        deleted_count = 0
        
        for log_file in settings.LOGS_DIR.glob('*.log*'):
            # الحصول على عمر الملف
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            age = (now - file_time).days
            
            if age > days:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"فشل حذف {log_file}: {e}")
        
        if deleted_count > 0:
            print(f"🗑️ تم حذف {deleted_count} ملف سجل قديم")


# ═══════════════════════════════════════════════════════════
# 🎯 الدالة الرئيسية للحصول على logger
# ═══════════════════════════════════════════════════════════

def get_logger(name: str = __name__) -> logging.Logger:
    """
    الحصول على logger (اختصار)
    
    Args:
        name: اسم الـ logger
        
    Returns:
        logging.Logger: الـ logger
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello World")
    """
    return LoggerManager.get_logger(name)

