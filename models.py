# models.py - 只定义模型，不创建db实例
from flask_sqlalchemy import SQLAlchemy

# 全局db实例，只创建一次
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='sub_admin')

    def __repr__(self):
        return f'<User {self.username}>'