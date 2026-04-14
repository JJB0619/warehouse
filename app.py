from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os

# 初始化 Flask
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-1234567890')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///warehouse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='sub_admin')

    def __repr__(self):
        return f'<User {self.username}>'

# 权限装饰器
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = User.query.get(session.get('user_id'))
        if not user or user.role != 'admin':
            flash('无权限访问')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('账号或密码错误')
    
    return render_template('login.html')

# 登出路由
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 首页路由
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# 管理员-用户管理路由
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# 添加子管理员路由
@app.route('/admin/user/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if User.query.filter_by(username=username).first():
        flash('用户名已存在')
        return redirect(url_for('admin_users'))
    
    new_user = User(
        username=username,
        password=generate_password_hash(password),
        role='sub_admin'
    )
    db.session.add(new_user)
    db.session.commit()
    flash('添加成功')
    return redirect(url_for('admin_users'))

# 删除用户路由
@app.route('/admin/user/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('不能删除主管理员')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('删除成功')
    return redirect(url_for('admin_users'))

# 初始化数据库（启动时自动执行）
with app.app_context():
    db.create_all()
    # 创建默认管理员
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('123456'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ 默认管理员创建成功：admin / 123456")

# 启动服务
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)