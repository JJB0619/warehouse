# init_db.py - 数据库初始化脚本
from app import app
from models import db, User
from werkzeug.security import generate_password_hash

# 必须在应用上下文中执行
with app.app_context():
    print("开始初始化数据库...")
    # 1. 先删除所有旧表（彻底解决表结构问题）
    db.drop_all()
    print("旧表已删除")
    # 2. 重建所有表
    db.create_all()
    print("新表创建完成")
    
    # 3. 检查admin用户是否存在
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        # 4. 创建主管理员
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ 管理员账号创建成功：admin / 123456")
    else:
        print("✅ admin账号已存在")