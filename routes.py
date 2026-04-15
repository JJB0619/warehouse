from flask import Blueprint, request, jsonify, send_file, render_template, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User, Warehouse, Product, Category
from services import *

bp = Blueprint('routes', __name__)

@bp.route('/')
def home():
    return redirect(url_for('routes.login_page'))

@bp.route('/login')
def login_page():
    return render_template('login.html')

@bp.route('/api/login', methods=['POST'])
def login_api():
    d = request.json
    u = User.query.filter_by(username=d.get('username')).first()
    if u and u.check_password(d.get('password')):
        login_user(u)
        return jsonify({"code":200,"msg":"成功"})
    return jsonify({"code":400,"msg":"账号或密码错误"})

@bp.route('/api/logout')
@login_required
def logout_api():
    logout_user()
    return redirect(url_for('routes.login_page'))

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
        return "无权限",403
    return render_template('users.html')

# ================== 分类 ==================
@bp.route('/api/category/list')
@login_required
def cat_list():
    cs = [{"id":c.id,"name":c.name} for c in Category.query.all()]
    return jsonify(code=200,data=cs)

@bp.route('/api/category/add', methods=['POST'])
@login_required
def cat_add():
    if not is_admin_user():
        return jsonify(code=403,msg="无权限")
    d=request.json
    if Category.query.filter_by(name=d['name']).first():
        return jsonify(code=400,msg="已存在")
    c=Category(name=d['name'])
    db.session.add(c)
    db.session.commit()
    return jsonify(code=200,msg="成功")

# ================== 商品 ==================
@bp.route('/api/product/add', methods=['POST'])
@login_required
def product_add():
    d=request.json
    p=Product(
        name=d['name'],
        spec=d.get('spec',''),
        price=float(d.get('price',0)),
        note=d.get('note',''),
        category_id=d.get('category_id'),
        warehouse_id=d['warehouse_id']
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(code=200,msg="成功")

@bp.route('/api/product/list')
@login_required
def product_list():
    cid=request.args.get('category_id')
    q=Product.query
    if cid:
        q=q.filter_by(category_id=cid)
    ps=[]
    for p in q.all():
        wh=Warehouse.query.get(p.warehouse_id)
        cat=Category.query.get(p.category_id) if p.category_id else None
        ps.append({
            "id":p.id,"name":p.name,"spec":p.spec,
            "category_name":cat.name if cat else "无分类",
            "warehouse_name":wh.name if wh else "未知",
            "stock":p.stock,"price":p.price,"total_price":p.total_price,"note":p.note
        })
    return jsonify(code=200,data=ps)

# ================== 仓库 ==================
@bp.route('/api/warehouse/list')
@login_required
def wh_list():
    ws=[{"id":w.id,"name":w.name} for w in Warehouse.query.all()]
    return jsonify(code=200,data=ws)

# ================== 出入库 ==================
@bp.route('/api/stock/in', methods=['POST'])
@login_required
def stock_in():
    d=request.json
    p=Product.query.get(d['product_id'])
    stock_in_op(p.id,p.warehouse_id,d['quantity'],current_user.username)
    return jsonify(code=200,msg="成功")

@bp.route('/api/stock/out', methods=['POST'])
@login_required
def stock_out():
    d=request.json
    p=Product.query.get(d['product_id'])
    ok=stock_out_op(p.id,p.warehouse_id,d['quantity'],current_user.username)
    return jsonify(code=200 if ok else 400,msg="成功" if ok else "库存不足")

@bp.route('/api/transfer', methods=['POST'])
@login_required
def transfer():
    d=request.json
    ok=transfer_op(d['product_id'],d['from_wh_id'],d['to_wh_id'],d['quantity'],current_user.username)
    return jsonify(code=200 if ok else 400,msg="成功" if ok else "库存不足")

# ================== 预警 & 导出 ==================
@bp.route('/api/stock/warning')
@login_required
def warning():
    return jsonify(code=200,data=get_stock_warning())

@bp.route('/api/export/report')
@login_required
def export_report():
    path=export_all_reports()
    return send_file(path,as_attachment=True)

# ================== 用户 ==================
@bp.route('/api/admin/user/add', methods=['POST'])
@login_required
def add_user():
    if not is_admin_user():return jsonify(code=403,msg="无权限")
    d=request.json
    if User.query.filter_by(username=d['username']).first():return jsonify(code=400,msg="已存在")
    u=User(username=d['username'],is_admin=d.get('is_admin',False))
    u.set_password(d['password'])
    db.session.add(u)
    db.session.commit()
    return jsonify(code=200,msg="成功")

@bp.route('/api/admin/user/list')
@login_required
def user_list():
    if not is_admin_user():return jsonify(code=403,msg="无权限")
    us=[]
    for u in User.query.all():
        us.append({"id":u.id,"username":u.username,"is_admin":u.is_admin,"role":"管理员" if u.is_admin else "普通用户"})
    return jsonify(code=200,data=us)
