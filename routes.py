from flask import Blueprint, request, jsonify, send_file
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User, Warehouse, Product
from services import (
    is_admin_user, get_stock_warning,
    stock_in_op, stock_out_op, transfer_op,
    export_all_reports
)

bp = Blueprint('routes', __name__)

# 登录接口
@bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({
            'code': 200,
            'msg': '登录成功',
            'data': {
                'username': user.username,
                'is_admin': user.is_admin
            }
        })
    return jsonify({'code': 400, 'msg': '账号或密码错误'}), 400

# 退出登录
@bp.route('/api/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({'code': 200, 'msg': '退出成功'})

# 系统状态检查
@bp.route('/')
def health_check():
    return jsonify({'code': 200, 'msg': '餐饮仓库管理系统运行正常'})

# ====================== 用户管理（仅管理员） ======================
@bp.route('/api/admin/user/add', methods=['POST'])
@login_required
def add_user():
    if not is_admin_user():
        return jsonify({'code': 403, 'msg': '无管理员权限'}), 403
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)

    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'msg': '用户名已存在'}), 400

    new_user = User(username=username, is_admin=is_admin)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '用户创建成功'})

# ====================== 仓库管理 ======================
@bp.route('/api/warehouse/list', methods=['GET'])
@login_required
def warehouse_list():
    warehouses = Warehouse.query.all()
    data = [{'id': w.id, 'name': w.name} for w in warehouses]
    return jsonify({'code': 200, 'data': data})

# ====================== 商品管理 ======================
@bp.route('/api/product/add', methods=['POST'])
@login_required
def product_add():
    data = request.get_json()
    new_product = Product(
        name=data.get('name'),
        spec=data.get('spec', ''),
        warehouse_id=data.get('warehouse_id')
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '商品添加成功'})

@bp.route('/api/product/list', methods=['GET'])
@login_required
def product_list():
    products = Product.query.all()
    data = []
    for p in products:
        wh = Warehouse.query.get(p.warehouse_id)
        data.append({
            'id': p.id,
            'name': p.name,
            'spec': p.spec,
            'warehouse_id': p.warehouse_id,
            'warehouse_name': wh.name if wh else '未知',
            'stock': p.stock
        })
    return jsonify({'code': 200, 'data': data})

# ====================== 出入库/调拨 ======================
@bp.route('/api/stock/in', methods=['POST'])
@login_required
def stock_in():
    data = request.get_json()
    stock_in_op(
        product_id=data.get('product_id'),
        warehouse_id=data.get('warehouse_id'),
        quantity=data.get('quantity'),
        operator=current_user.username
    )
    return jsonify({'code': 200, 'msg': '入库成功'})

@bp.route('/api/stock/out', methods=['POST'])
@login_required
def stock_out():
    data = request.get_json()
    success = stock_out_op(
        product_id=data.get('product_id'),
        warehouse_id=data.get('warehouse_id'),
        quantity=data.get('quantity'),
        operator=current_user.username
    )
    if success:
        return jsonify({'code': 200, 'msg': '出库成功'})
    return jsonify({'code': 400, 'msg': '库存不足，出库失败'}), 400

@bp.route('/api/transfer', methods=['POST'])
@login_required
def transfer():
    data = request.get_json()
    success = transfer_op(
        product_id=data.get('product_id'),
        from_wh_id=data.get('from_wh_id'),
        to_wh_id=data.get('to_wh_id'),
        quantity=data.get('quantity'),
        operator=current_user.username
    )
    if success:
        return jsonify({'code': 200, 'msg': '调拨成功'})
    return jsonify({'code': 400, 'msg': '库存不足，调拨失败'}), 400

# ====================== 库存预警 ======================
@bp.route('/api/stock/warning', methods=['GET'])
@login_required
def stock_warning():
    data = get_stock_warning()
    return jsonify({'code': 200, 'data': data})

# ====================== Excel报表导出 ======================
@bp.route('/api/export/report', methods=['GET'])
@login_required
def export_report():
    file_path = export_all_reports()
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_path.split('/')[-1]
    )
# ===================== 前端页面路由 =====================
@bp.route('/login')
def login_page():
    return render_template('login.html')

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