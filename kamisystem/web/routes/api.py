from flask import Blueprint, request, jsonify
from models import db, Card, CardStatus, get_utc_time, SHANGHAI_TZ
from datetime import datetime
import logging
import pytz

api = Blueprint('api', __name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@api.route('/validate', methods=['POST'])
def validate_card():
    """卡密验证API"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': '无效的JSON数据'}), 400
        
        code = data.get('code', '').strip()
        machine_code = data.get('machine_code', '').strip()
        
        if not code or not machine_code:
            return jsonify({'status': 'error', 'message': '卡密和机器码不能为空'}), 400
        
        # 查找卡密
        card = Card.query.filter_by(full_code=code).first()
        
        if not card:
            logger.warning(f"卡密不存在: {code}")
            return jsonify({'status': 'error', 'message': '卡密不存在'}), 404
        
        # 检查并更新过期状态
        card.check_and_update_status()
        
        # 验证卡密状态
        if card.status == CardStatus.UNUSED:
            # 首次使用，激活卡密
            if card.activate(machine_code):
                db.session.commit()
                logger.info(f"卡密首次激活: {code} -> 机器码: {machine_code}")
                
                # 转换时间到上海时区
                expire_at_shanghai = card.expire_at.replace(tzinfo=pytz.UTC).astimezone(SHANGHAI_TZ)
                
                return jsonify({
                    'status': 'success',
                    'message': '授权成功',
                    'expire_at': expire_at_shanghai.isoformat(),
                    'remaining_hours': 3
                }), 200
            else:
                db.session.rollback()
                return jsonify({'status': 'error', 'message': '卡密激活失败'}), 500
                
        elif card.status == CardStatus.ACTIVE:
            # 检查机器码是否匹配
            if card.machine_code != machine_code:
                logger.warning(f"机器码不匹配: {code} -> 期望: {card.machine_code}, 实际: {machine_code}")
                return jsonify({'status': 'error', 'message': '机器码不匹配'}), 403
            
            # 检查是否过期
            if card.is_expired():
                card.status = CardStatus.EXPIRED
                db.session.commit()
                logger.info(f"卡密已过期: {code}")
                return jsonify({'status': 'error', 'message': '卡密已过期'}), 403
            
            # 计算剩余时间
            remaining_time = card.expire_at - get_utc_time()
            remaining_hours = remaining_time.total_seconds() / 3600
            
            # 转换时间到上海时区
            expire_at_shanghai = card.expire_at.replace(tzinfo=pytz.UTC).astimezone(SHANGHAI_TZ)
            
            logger.info(f"卡密验证成功: {code} -> 剩余时间: {remaining_hours:.2f}小时")
            return jsonify({
                'status': 'success',
                'message': '授权成功',
                'expire_at': expire_at_shanghai.isoformat(),
                'remaining_hours': round(remaining_hours, 2)
            }), 200
            
        elif card.status == CardStatus.EXPIRED:
            logger.warning(f"卡密已过期: {code}")
            return jsonify({'status': 'error', 'message': '卡密已过期'}), 403
        
        else:
            return jsonify({'status': 'error', 'message': '未知的卡密状态'}), 500
            
    except Exception as e:
        logger.error(f"验证卡密时发生错误: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500

@api.route('/status/<code>', methods=['GET'])
def get_card_status(code):
    """获取卡密状态"""
    try:
        card = Card.query.filter_by(full_code=code).first()
        
        if not card:
            return jsonify({'status': 'error', 'message': '卡密不存在'}), 404
        
        # 检查并更新过期状态
        card.check_and_update_status()
        db.session.commit()
        
        # 转换时间到上海时区
        def to_shanghai_time(dt):
            if dt is None:
                return None
            return dt.replace(tzinfo=pytz.UTC).astimezone(SHANGHAI_TZ).isoformat()
        
        result = {
            'status': 'success',
            'data': {
                'full_code': card.full_code,
                'status': card.status.value,
                'created_at': to_shanghai_time(card.created_at),
                'used_at': to_shanghai_time(card.used_at),
                'expire_at': to_shanghai_time(card.expire_at),
                'machine_code': card.machine_code
            }
        }
        
        # 如果是活跃状态，添加剩余时间信息
        if card.status == CardStatus.ACTIVE and card.expire_at:
            remaining_time = card.expire_at - get_utc_time()
            result['data']['remaining_hours'] = round(remaining_time.total_seconds() / 3600, 2)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"获取卡密状态时发生错误: {str(e)}")
        return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500

@api.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    current_time = datetime.now(SHANGHAI_TZ)
    return jsonify({
        'status': 'ok',
        'timestamp': current_time.isoformat(),
        'service': 'kamisystem'
    }), 200
