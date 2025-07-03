from models import db, Card, CardStatus, SHANGHAI_TZ
from datetime import datetime
import os
import logging
import pytz

logger = logging.getLogger(__name__)

def export_unused_cards(prefix_filter=''):
    """导出未使用卡密为TXT文件"""
    try:
        # 构建查询
        query = Card.query.filter(Card.status == CardStatus.UNUSED)
        
        if prefix_filter:
            query = query.filter(Card.prefix == prefix_filter)
        
        # 按创建时间排序
        cards = query.order_by(Card.created_at.desc()).all()
        
        if not cards:
            return None
        
        # 生成文件名
        current_time = datetime.now(SHANGHAI_TZ)
        timestamp = current_time.strftime('%Y%m%d_%H%M%S')
        if prefix_filter:
            filename = f"unused_cards_{prefix_filter}_{timestamp}.txt"
        else:
            filename = f"unused_cards_{timestamp}.txt"
        
        # 确保导出目录存在
        export_dir = 'exports'
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        filepath = os.path.join(export_dir, filename)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# 未使用卡密导出\n")
            f.write(f"# 导出时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (上海时区)\n")
            if prefix_filter:
                f.write(f"# 前缀筛选: {prefix_filter}\n")
            f.write(f"# 总计: {len(cards)} 个\n")
            f.write(f"# 格式: 卡密代码\n")
            f.write("# " + "="*50 + "\n\n")
            
            for card in cards:
                f.write(f"{card.full_code}\n")
        
        logger.info(f"导出未使用卡密: {filepath}, 数量: {len(cards)}")
        return filepath
        
    except Exception as e:
        logger.error(f"导出卡密时发生错误: {str(e)}")
        return None

def generate_cards_batch(prefix, count, code_length=10):
    """批量生成卡密"""
    try:
        success_count = 0
        failed_count = 0
        
        for i in range(count):
            try:
                card = Card.create_card(prefix, code_length)
                db.session.add(card)
                success_count += 1
                
                # 每100个提交一次
                if success_count % 100 == 0:
                    db.session.commit()
                    logger.info(f"已生成 {success_count}/{count} 个卡密")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"生成卡密失败: {str(e)}")
                
                # 如果失败太多，停止生成
                if failed_count > 10:
                    logger.error("生成失败次数过多，停止生成")
                    break
        
        # 最终提交
        if success_count > 0:
            db.session.commit()
            logger.info(f"批量生成完成: 成功={success_count}, 失败={failed_count}")
        
        return success_count
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量生成卡密时发生错误: {str(e)}")
        return 0

def clean_expired_cards():
    """清理过期卡密状态"""
    try:
        # 查找所有活跃状态的卡密
        active_cards = Card.query.filter(Card.status == CardStatus.ACTIVE).all()
        
        updated_count = 0
        for card in active_cards:
            if card.check_and_update_status():
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            logger.info(f"清理过期卡密: {updated_count} 个")
        
        return updated_count
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"清理过期卡密时发生错误: {str(e)}")
        return 0

def get_statistics():
    """获取系统统计信息"""
    try:
        stats = {
            'total': Card.query.count(),
            'unused': Card.query.filter(Card.status == CardStatus.UNUSED).count(),
            'active': Card.query.filter(Card.status == CardStatus.ACTIVE).count(),
            'expired': Card.query.filter(Card.status == CardStatus.EXPIRED).count(),
            'prefixes': db.session.query(Card.prefix).distinct().count()
        }
        return stats
    except Exception as e:
        logger.error(f"获取统计信息时发生错误: {str(e)}")
        return {
            'total': 0,
            'unused': 0,
            'active': 0,
            'expired': 0,
            'prefixes': 0
        }
