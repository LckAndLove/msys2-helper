from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Card, CardStatus, SHANGHAI_TZ
from utils.export_txt import export_unused_cards, generate_cards_batch
from datetime import datetime
import os
import logging
import pytz

admin = Blueprint('admin', __name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@admin.route('/')
def index():
    """卡密管理列表页"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')
    prefix_filter = request.args.get('prefix', '')
    search_term = request.args.get('search', '')
    
    # 构建查询
    query = Card.query
    
    # 应用过滤器
    if status_filter:
        query = query.filter(Card.status == CardStatus(status_filter))
    
    if prefix_filter:
        query = query.filter(Card.prefix == prefix_filter)
    
    if search_term:
        query = query.filter(Card.full_code.contains(search_term))
    
    # 按创建时间倒序排列
    query = query.order_by(Card.created_at.desc())
    
    # 分页
    cards = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 获取所有前缀用于过滤器
    prefixes = db.session.query(Card.prefix).distinct().all()
    prefixes = [p[0] for p in prefixes]
    
    # 统计信息
    stats = {
        'total': Card.query.count(),
        'unused': Card.query.filter(Card.status == CardStatus.UNUSED).count(),
        'active': Card.query.filter(Card.status == CardStatus.ACTIVE).count(),
        'expired': Card.query.filter(Card.status == CardStatus.EXPIRED).count()
    }
    
    return render_template('index.html', 
                         cards=cards, 
                         prefixes=prefixes,
                         stats=stats,
                         current_filters={
                             'status': status_filter,
                             'prefix': prefix_filter,
                             'search': search_term
                         })

@admin.route('/generate')
def generate_page():
    """批量生成卡密页面"""
    return render_template('generate.html')

@admin.route('/generate', methods=['POST'])
def generate_cards():
    """批量生成卡密"""
    try:
        prefix = request.form.get('prefix', '').strip()
        count = int(request.form.get('count', 0))
        code_length = int(request.form.get('code_length', 10))
        
        if not prefix:
            flash('前缀不能为空', 'error')
            return redirect(url_for('admin.generate_page'))
        
        if count <= 0 or count > 10000:
            flash('数量必须在1-10000之间', 'error')
            return redirect(url_for('admin.generate_page'))
        
        if code_length < 6 or code_length > 32:
            flash('代码长度必须在6-32之间', 'error')
            return redirect(url_for('admin.generate_page'))
        
        # 生成卡密
        success_count = generate_cards_batch(prefix, count, code_length)
        
        if success_count > 0:
            flash(f'成功生成 {success_count} 个卡密', 'success')
            logger.info(f"批量生成卡密: 前缀={prefix}, 数量={success_count}")
        else:
            flash('生成失败，请检查参数', 'error')
        
        return redirect(url_for('admin.index'))
        
    except ValueError as e:
        flash(f'参数错误: {str(e)}', 'error')
        return redirect(url_for('admin.generate_page'))
    except Exception as e:
        logger.error(f"批量生成卡密时发生错误: {str(e)}")
        flash('生成失败，请重试', 'error')
        return redirect(url_for('admin.generate_page'))

@admin.route('/export')
def export_cards():
    """导出未使用卡密"""
    try:
        prefix_filter = request.args.get('prefix', '')
        
        filename = export_unused_cards(prefix_filter)
        
        if filename and os.path.exists(filename):
            logger.info(f"导出卡密: {filename}")
            return send_file(filename, 
                           as_attachment=True, 
                           download_name=os.path.basename(filename),
                           mimetype='text/plain')
        else:
            flash('导出失败，没有找到未使用的卡密', 'error')
            return redirect(url_for('admin.index'))
            
    except Exception as e:
        logger.error(f"导出卡密时发生错误: {str(e)}")
        flash('导出失败，请重试', 'error')
        return redirect(url_for('admin.index'))

@admin.route('/card/<int:card_id>/edit', methods=['GET', 'POST'])
def edit_card(card_id):
    """编辑卡密"""
    card = Card.query.get_or_404(card_id)
    
    if request.method == 'POST':
        try:
            # 更新卡密信息
            card.prefix = request.form.get('prefix', '').strip()
            card.status = CardStatus(request.form.get('status'))
            
            # 重新生成 full_code
            card.full_code = f"{card.prefix}-{card.code}"
            
            db.session.commit()
            flash('卡密更新成功', 'success')
            return redirect(url_for('admin.index'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"编辑卡密时发生错误: {str(e)}")
            flash('更新失败，请重试', 'error')
    
    return render_template('edit_card.html', card=card)

@admin.route('/card/<int:card_id>/delete', methods=['POST'])
def delete_card(card_id):
    """删除卡密"""
    try:
        card = Card.query.get_or_404(card_id)
        db.session.delete(card)
        db.session.commit()
        
        flash('卡密删除成功', 'success')
        logger.info(f"删除卡密: {card.full_code}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除卡密时发生错误: {str(e)}")
        flash('删除失败，请重试', 'error')
    
    return redirect(url_for('admin.index'))

@admin.route('/api/stats')
def api_stats():
    """获取统计信息API"""
    try:
        stats = {
            'total': Card.query.count(),
            'unused': Card.query.filter(Card.status == CardStatus.UNUSED).count(),
            'active': Card.query.filter(Card.status == CardStatus.ACTIVE).count(),
            'expired': Card.query.filter(Card.status == CardStatus.EXPIRED).count()
        }
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"获取统计信息时发生错误: {str(e)}")
        return jsonify({'error': '获取统计信息失败'}), 500

@admin.route('/api/cleanup-expired', methods=['POST'])
def cleanup_expired():
    """清理过期卡密"""
    try:
        # 更新过期状态
        cards = Card.query.filter(Card.status == CardStatus.ACTIVE).all()
        updated_count = 0
        
        for card in cards:
            if card.check_and_update_status():
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            logger.info(f"清理过期卡密: {updated_count} 个")
        
        return jsonify({
            'status': 'success',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"清理过期卡密时发生错误: {str(e)}")
        return jsonify({'status': 'error', 'message': '清理失败'}), 500
