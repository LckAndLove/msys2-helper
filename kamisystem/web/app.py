from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from models import db, Card, CardStatus, SHANGHAI_TZ
from routes.api import api
from routes.admin import admin
from utils.export_txt import clean_expired_cards
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging
import atexit
import pytz

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 配置数据库
    database_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:rootpwd@localhost:3306/kamisystem')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # 配置Flask
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(admin, url_prefix='/admin')
    
    # 时间过滤器
    @app.template_filter('shanghai_time')
    def shanghai_time_filter(dt):
        """将UTC时间转换为上海时区时间"""
        if dt is None:
            return None
        try:
            # 假设输入的是UTC时间
            utc_dt = dt.replace(tzinfo=pytz.UTC)
            shanghai_dt = utc_dt.astimezone(SHANGHAI_TZ)
            return shanghai_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None
    
    # 主页路由
    @app.route('/')
    def index():
        return render_template('welcome.html')
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error_code=404, error_message='页面不存在'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html', error_code=500, error_message='服务器内部错误'), 500
    
    # 健康检查
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'kamisystem'}, 200
    
    return app

def setup_scheduler(app):
    """设置定时任务"""
    scheduler = BackgroundScheduler()
    
    # 每小时清理一次过期卡密
    def scheduled_cleanup():
        with app.app_context():
            try:
                count = clean_expired_cards()
                logger.info(f"定时清理过期卡密: {count} 个")
            except Exception as e:
                logger.error(f"定时清理过期卡密失败: {str(e)}")
    
    scheduler.add_job(
        func=scheduled_cleanup,
        trigger="interval",
        hours=1,
        id='cleanup_expired_cards'
    )
    
    scheduler.start()
    logger.info("定时任务已启动")
    
    # 确保在应用关闭时停止调度器
    atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app = create_app()
    
    # 创建数据库表
    with app.app_context():
        try:
            db.create_all()
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {str(e)}")
    
    # 设置定时任务
    setup_scheduler(app)
    
    # 运行应用
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"启动应用: 端口={port}, 调试模式={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)
