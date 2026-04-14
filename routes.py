from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User, Warehouse, Product, StockIn, StockOut, Transfer
from services import *

bp = Blueprint('routes', __name__)

# 登录
@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if user and user.check_password(data.get('password')):
        login_user(user)
        return jsonify({'code': 200, 'msg': '登录成功'})
    return jsonify({'code': 400, 'msg': '账号或密码错误'})

# 退出
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))

# 首页
@bp.route('/')
def index():
    return jsonify({'msg': '餐饮仓库管理系统运行正常'})

# ============= 管理员接口 =============
@bp.route('/admin/user/add', methods=['POST'])
@login_required
def add_user():
    if not is_admin_user():
        return jsonify({'code': 403, 'msg': '无管理员权限'})
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'code': 400, 'msg': '用户已存在'})
    user = User(username=data['username'], is_admin=data.get('is_admin', False))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建用户成功'})

# ============= 仓库管理 =============
@bp.route('/warehouse/list')
@login_required
def warehouse_list():
    list = [{'id': w.id, 'name': w.name} for w in Warehouse.query.all()]
    return jsonify({'code': 200, 'data': list})

# ============= 商品管理 =============
@bp.route('/product/add', methods=['POST'])
@login_required
def product_add():
    data = request.json
    p = Product(name=data['name'], spec=data.get('spec', ''), warehouse_id=data['warehouse_id'])
    db.session.add(p)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '添加成功'})

@bp.route('/product/list')
@login_required
def product_list():
    products = Product.query.all()
    res = []
    for p in products:
        wh = Warehouse.query.get(p.warehouse_id)
        res.append({
            'id': p.id, 'name': p.name, 'spec': p.spec,
            'warehouse': wh.name if wh else '未知', 'stock': p.stock
        })
    return jsonify({'code': 200, 'data': res})

# ============= 入库/出库/调拨 =============
@bp.route('/stock/in', methods=['POST'])
@login_required
def stock_in():
    d = request.json
    stock_in_op(d['product_id'], d['warehouse_id'], d['quantity'], current_user.username)
    return jsonify({'code': 200, 'msg': '入库成功'})

@bp.route('/stock/out', methods=['POST'])
@login_required
def stock_out():
    d = request.json
    ok = stock_out_op(d['product_id'], d['warehouse_id'], d['quantity'], current_user.username)
    return jsonify({'code': 200 if ok else 400, 'msg': '出库成功' if ok else '库存不足'})

@bp.route('/transfer', methods=['POST'])
@login_required
def transfer():
    d = request.json
    ok = transfer_op(d['product_id'], d['from_wh'], d['to_wh'], d['quantity'], current_user.username)
    return jsonify({'code': 200 if ok else 400, 'msg': '调拨成功' if ok else '库存不足'})

# ============= 库存预警 =============
@bp.route('/stock/warning')
@login_required
def stock_warning():
    return jsonify({'code': 200, 'data': get_stock_warning()})

# ============= Excel导出 =============
@bp.route('/export/report')
@login_required
def export_report():
    path = export_all_reports()
    return send_file(path, as_attachment=True)