import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 密钥
    SECRET_KEY = os.getenv('SECRET_KEY', 'catering-warehouse-secure-key')
    # 数据库：Railway自动使用PostgreSQL，本地使用SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///catering.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 库存预警阈值
    STOCK_WARNING_THRESHOLD = 10