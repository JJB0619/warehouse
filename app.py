from flask import Flask
from config import Config
from models import db, User
from routes import bp
from services import init_system
from flask_login import LoginManager
import os

# 初始化Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 初始化登录管理
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'routes.health_check'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 注册路由
app.register_blueprint(bp)

# 系统初始化：自动创建管理员+仓库
with app.app_context():
    db.create_all()
    init_system()

# Railway生产环境入口
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
