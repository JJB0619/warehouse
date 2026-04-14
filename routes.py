from flask import Blueprint, request, jsonify, send_file, render_template, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User, Warehouse, Product
from services import *

bp = Blueprint('routes', __name__)

# 根路径自动跳转到登录页
@bp.route('/')
def home():
    return redirect(url_for('routes.login_page'))

# 登录页路由
@bp.route('/login')
def login_page():
    return render_template('login.html')

# 登录API
@bp.route('/api/login', methods=['POST'])
def login_api():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({"code": 200, "msg": "登录成功"})
    return jsonify({"code": 400, "msg": "账号或密码错误"}), 400

# 退出登录
@bp.route('/api/logout')
@login_required
def logout_api():
    logout_user()
    return redirect(url_for('routes.login_page'))

# ================== 页面路由 ==================
@bp.route('/index')
@login_required
def index_page():
    return render_template('index.html')

@bp.route('/products')
@login_required
def products_page():
    return render_template('products.html')

@bp.route('/stock')
@login_required
def stock_page():
    return render_template('stock.html')

@bp.route('/transfer')
@login_required
def transfer_page():
    return render_template('transfer.html')

@bp.route('/warning')
@login_required
def warning_page():
    return render_template('warning.html')

@bp.route('/report')
@login_required
def report_page():
    return render_template('report.html')

@bp.route('/users')
@login_required
def users_page():
    if not is_admin_user():
        return "无权限访问", 403
    return render_template('users.html')

# ================== API接口 ==================
# 用户管理
@bp.route('/api/admin/user/add', methods=['POST'])
@login_required
def add_user():
    if not is_admin_user():
        return jsonify({"code": 403, "msg": "无管理员权限"}), 403
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"code": 400, "msg": "用户名已存在"}), 400
    user = User(username=data['username'], is_admin=data.get('is_admin', False))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"code": 200, "msg": "用户创建成功"})

@bp.route('/api/admin/user/list', methods=['GET'])
@login_required
def user_list():
    if not is_admin_user():
        return jsonify({"code": 403, "msg": "无管理员权限"}), 403
    users = User.query.all()
    data = []
    for u in users:
        data.append({
            "id": u.id,
            "username": u.username,
            "is_admin": u.is_admin,
            "role": "管理员" if u.is_admin else "普通用户"
        })
    return jsonify({"code": 200, "data": data})

# 仓库列表
@bp.route('/api/warehouse/list', methods=['GET'])
@login_required
def warehouse_list():
    warehouses = Warehouse.query.all()
    data = [{"id": w.id, "name": w.name} for w in warehouses]
    return jsonify({"code": 200, "data": data})

# 商品管理
@bp.route('/api/product/add', methods=['POST'])
@login_required
def add_product():
    data = request.get_json()
    product = Product(
        name=data['name'],
        spec=data.get('spec', ''),
        warehouse_id=data['warehouse_id']
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"code": 200, "msg": "商品添加成功"})

@bp.route('/api/product/list', methods=['GET'])
@login_required
def product_list():
    products = Product.query.all()
    data = []
    for p in products:
        wh = Warehouse.query.get(p.warehouse_id)
        data.append({
            "id": p.id,
            "name": p.name,
            "spec": p.spec,
            "warehouse_name": wh.name if wh else "未知",
            "stock": p.stock
        })
    return jsonify({"code": 200, "data": data})

# 出入库
@bp.route('/api/stock/in', methods=['POST'])
@login_required
def stock_in():
    data = request.get_json()
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({"code": 400, "msg": "商品不存在"}), 400
    stock_in_op(data['product_id'], product.warehouse_id, data['quantity'], current_user.username)
    return jsonify({"code": 200, "msg": "入库成功"})

@bp.route('/api/stock/out', methods=['POST'])
@login_required
def stock_out():
    data = request.get_json()
    success = stock_out_op(data['product_id'], Product.query.get(data['product_id']).warehouse_id, data['quantity'], current_user.username)
    return jsonify({"code": 200 if success else 400, "msg": "出库成功" if success else "库存不足"})

# 调拨
@bp.route('/api/transfer', methods=['POST'])
@login_required
def transfer():
    data = request.get_json()
    success = transfer_op(data['product_id'], data['from_wh_id'], data['to_wh_id'], data['quantity'], current_user.username)
    return jsonify({"code": 200 if success else 400, "msg": "调拨成功" if success else "库存不足"})

# 库存预警
@bp.route('/api/stock/warning', methods=['GET'])
@login_required
def stock_warning():
    return jsonify({"code": 200, "data": get_stock_warning()})

# 报表导出
@bp.route('/api/export/report', methods=['GET'])
@login_required
def export_report():
    file_path = export_all_reports()
    return send_file(file_path, as_attachment=True, download_name=file_path.split('/')[-1])

# 健康检查
@bp.route('/api/health')
def health_check():
    return jsonify({"code": 200, "msg": "餐饮仓库管理系统运行正常"})
