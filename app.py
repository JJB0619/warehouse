# ==============================================
# 仓库管理系统 - 完整主程序 app.py
# 直接复制替换原有文件即可
# ==============================================
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os

# 初始化 Flask
app = Flask(__name__)

# 配置密钥与数据库
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123456')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///warehouse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 导入用户模型
from models import User

# ==============================================
# 登录权限装饰器
# ==============================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================
# 主管理员权限装饰器
# ==============================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = User.query.get(session.get('user_id'))
        if not user or user.role != 'admin':
            flash('无权限访问')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================
# 登录页面
# ==============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        flash('账号或密码错误')
        return redirect(url_for('login'))

    session['user_id'] = user.id
    return redirect(url_for('index'))

# ==============================================
# 退出登录
# ==============================================
@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==============================================
# 首页
# ==============================================
@app.route('/')
@login_required
def index():
    user = User.query.get(session['user_id'])
    return render_template('index.html', user=user)

# ==============================================
# 主管理员 - 账号管理后台
# ==============================================
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# ==============================================
# 添加子管理员
# ==============================================
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
    flash('子管理员添加成功')
    return redirect(url_for('admin_users'))

# ==============================================
# 删除账号（禁止删除主管理员）
# ==============================================
@app.route('/admin/user/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('主管理员不能删除')
        return redirect(url_for('admin_users'))

    db.session.delete(user)
    db.session.commit()
    flash('账号已删除')
    return redirect(url_for('admin_users'))

# ==============================================
# 子管理员权限示例：禁止删除
# ==============================================
@app.route('/delete/demo')
@login_required
def delete_demo():
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        flash('子管理员无删除权限')
        return redirect(url_for('index'))

    flash('删除成功（演示）')
    return redirect(url_for('index'))

# ==============================================
# Railway 生产环境启动
# ==============================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)