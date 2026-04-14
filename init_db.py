from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    print("🔧 初始化数据库...")
    db.create_all()
    print("✅ 表创建完成")
    
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ 管理员创建成功：admin / 123456")
    else:
        print("✅ 管理员已存在")