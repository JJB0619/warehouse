from app import app, db
from werkzeug.security import generate_password_hash

# 必须加上下文
with app.app_context():
    # 彻底删除旧数据库，重建新表
    db.drop_all()
    db.create_all()
    
    # 导入模型
    from models import User
    
    # 创建管理员
    admin = User(
        username="admin",
        password=generate_password_hash("123456"),
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()
    
    print("✅ 数据库重建完成，管理员账号：admin / 123456")