from app import app, db
from werkzeug.security import generate_password_hash

# 必须加 Flask 上下文
with app.app_context():
    # 创建所有数据库表（第一次部署必须执行）
    db.create_all()

    # 从 models 导入 User（放在这里防止循环导入）
    from models import User

    # 查询是否已有 admin
    admin = User.query.filter_by(username="admin").first()

    if not admin:
        # 创建管理员账号
        new_admin = User()
        new_admin.username = "admin"
        new_admin.password = generate_password_hash("123456")
        new_admin.role = "admin"

        db.session.add(new_admin)
        db.session.commit()
        print("✅ 管理员账号创建成功！账号：admin 密码：123456")
    else:
        # 重置密码
        admin.password = generate_password_hash("123456")
        db.session.commit()
        print("✅ 管理员密码已重置为：123456")