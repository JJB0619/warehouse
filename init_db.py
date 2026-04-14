# init_db.py - 数据库初始化脚本
from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # 彻底重建数据库，解决表结构问题
    db.drop_all()
    db.create_all()
    
    # 创建主管理员
    admin = User(
        username="admin",
        password=generate_password_hash("123456"),
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()
    
    print("✅ 数据库初始化完成，管理员账号：admin / 123456")