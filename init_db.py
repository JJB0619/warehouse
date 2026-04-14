from app import app
from models import db, User
from werkzeug.security import generate_password_hash
import os

# 关键：只在第一次部署时创建表，后续部署保留数据
def init_database():
    with app.app_context():
        print("🔍 检查数据库结构...")
        
        # 尝试查询User表，如果不存在则自动创建
        try:
            User.query.limit(1).first()
            print("✅ 数据表已存在，跳过重建")
        except Exception as e:
            print(f"❌ 未检测到表结构: {e}")
            print("🔧 正在创建新表...")
            db.create_all()
            print("✅ 表创建完成")

        # 创建管理员（如果不存在）
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            print("👤 创建初始管理员...")
            admin = User(
                username="admin",
                password=generate_password_hash("123456"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ 管理员创建完成：admin / 123456")
        else:
            print("✅ 管理员已存在")

if __name__ == "__main__":
    init_database()