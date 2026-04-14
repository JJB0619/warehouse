import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 密钥（Railway环境变量优先，本地自动生成安全密钥）
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    
    # 数据库配置（Railway PostgreSQL自动适配，本地SQLite）
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///catering.db')
    # 修复Railway PostgreSQL连接字符串前缀问题
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql+psycopg2://", 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 库存预警阈值（可自定义）
    STOCK_WARNING_THRESHOLD = 10