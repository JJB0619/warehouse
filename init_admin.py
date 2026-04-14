from app import app, db
from werkzeug.security import generate_password_hash

with app.app_context():
    # 先删除所有旧表，再重建（彻底解决字段不匹配问题）
    db.drop_all()
    db.create_all()

    from models import User
    admin = User.query.filter_by(username="admin").first()

    if not admin:
        hashed_pw = generate_password_hash("123456")
        new_admin = User(username="admin", password=hashed_pw, role="admin")
        db.session.add(new_admin)
        db.session.commit()
        print("✅ 数据库重置完成，管理员账号创建成功：admin / 123456")