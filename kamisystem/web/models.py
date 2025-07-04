from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from enum import Enum
import random
import string
import pytz

db = SQLAlchemy()

# 设置上海时区
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

def get_current_time():
    """获取当前上海时间"""
    return datetime.now(SHANGHAI_TZ)

def get_utc_time():
    """获取UTC时间（用于数据库存储）"""
    return datetime.utcnow()

class CardStatus(Enum):
    UNUSED = 'UNUSED'
    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'
    
    @classmethod
    def from_string(cls, value):
        """从字符串创建枚举值"""
        if isinstance(value, str):
            value = value.upper()
            for status in cls:
                if status.value == value:
                    return status
        elif isinstance(value, cls):
            return value
        raise ValueError(f"Invalid status value: {value}")

class Card(db.Model):
    __tablename__ = 'cards'
    
    id = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(16), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    full_code = db.Column(db.String(128), nullable=False, unique=True)
    used_at = db.Column(db.DateTime, default=None)
    expire_at = db.Column(db.DateTime, default=None)
    machine_code = db.Column(db.String(128), default=None)
    status = db.Column(db.Enum(CardStatus), default=CardStatus.UNUSED)
    created_at = db.Column(db.DateTime, default=get_utc_time)
    updated_at = db.Column(db.DateTime, default=get_utc_time, onupdate=get_utc_time)
    
    def __repr__(self):
        return f'<Card {self.full_code}>'
    
    def activate(self, machine_code):
        """激活卡密"""
        try:
            self.status = CardStatus.ACTIVE
            self.machine_code = machine_code
            self.used_at = get_utc_time()
            self.expire_at = get_utc_time() + timedelta(hours=3)
            self.updated_at = get_utc_time()
            return True
        except Exception as e:
            return False
    
    def is_expired(self):
        """检查是否过期"""
        if self.expire_at is None:
            return False
        return get_utc_time() > self.expire_at
    
    def check_and_update_status(self):
        """检查并更新状态"""
        if self.status == CardStatus.ACTIVE and self.is_expired():
            self.status = CardStatus.EXPIRED
            self.updated_at = get_utc_time()
            return True
        return False
    
    def to_dict(self):
        """转换为字典"""
        def to_shanghai_time(dt):
            if dt is None:
                return None
            return dt.replace(tzinfo=pytz.UTC).astimezone(SHANGHAI_TZ).isoformat()
        
        return {
            'id': self.id,
            'prefix': self.prefix,
            'code': self.code,
            'full_code': self.full_code,
            'used_at': to_shanghai_time(self.used_at),
            'expire_at': to_shanghai_time(self.expire_at),
            'machine_code': self.machine_code,
            'status': self.status.value,
            'created_at': to_shanghai_time(self.created_at),
            'updated_at': to_shanghai_time(self.updated_at)
        }
    
    @classmethod
    def generate_random_code(cls, length=10):
        """生成随机代码"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    @classmethod
    def create_card(cls, prefix, code_length=10):
        """创建新卡密"""
        max_attempts = 100
        for _ in range(max_attempts):
            code = cls.generate_random_code(code_length)
            full_code = f"{prefix}-{code}"
            
            # 检查是否重复
            if not cls.query.filter_by(full_code=full_code).first():
                card = cls(
                    prefix=prefix,
                    code=code,
                    full_code=full_code
                )
                return card
        
        raise Exception("无法生成唯一的卡密代码")
    
    @staticmethod
    def get_status_display(status):
        """获取状态显示文本"""
        if isinstance(status, str):
            status = CardStatus.from_string(status)
        
        status_map = {
            CardStatus.UNUSED: '未使用',
            CardStatus.ACTIVE: '已激活',
            CardStatus.EXPIRED: '已过期'
        }
        return status_map.get(status, '未知')
    
    @staticmethod
    def get_status_color(status):
        """获取状态颜色"""
        if isinstance(status, str):
            status = CardStatus.from_string(status)
        
        color_map = {
            CardStatus.UNUSED: 'success',
            CardStatus.ACTIVE: 'primary',
            CardStatus.EXPIRED: 'danger'
        }
        return color_map.get(status, 'secondary')
