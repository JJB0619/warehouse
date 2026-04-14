# app.py - 完整无冲突版本
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os

# 1. 从models导入统一的db实例和User模型
from models import db, User

# 2. 初始化Flask
app = Flask(__name__)

# 3. 配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123456')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///warehouse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 4. 绑定db到Flask app（关键！解决多实例问题）
db.init_app(app)

# 5. 权限装饰器
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
            flash('无权限访问该功能')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# 6. 路由
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

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

# 7. 启动
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)