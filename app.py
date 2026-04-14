from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
import pandas as pd
import os
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///warehouse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------------------
# 数据库模型
# ------------------------------

# 用户
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin / user

# 仓库
class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    remark = db.Column(db.String(200))

# 商品
class Goods(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20))
    warn_stock = db.Column(db.Float, default=0)  # 预警库存
    remark = db.Column(db.String(200))
    create_time = db.Column(db.DateTime, default=datetime.now)

# 入库
class InRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'))
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))
    num = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100))
    create_time = db.Column(db.DateTime, default=datetime.now)
    goods = db.relationship('Goods', backref='ins')
    warehouse = db.relationship('Warehouse', backref='ins')

# 出库
class OutRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'))
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))
    num = db.Column(db.Float, nullable=False)
    user = db.Column(db.String(100))
    create_time = db.Column(db.DateTime, default=datetime.now)
    goods = db.relationship('Goods', backref='outs')
    warehouse = db.relationship('Warehouse', backref='outs')

# 调拨
class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'))
    from_wareid = db.Column(db.Integer, db.ForeignKey('warehouse.id'))
    to_wareid = db.Column(db.Integer, db.ForeignKey('warehouse.id'))
    num = db.Column(db.Float, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    goods = db.relationship('Goods', backref='transfers')
    from_ware = db.relationship('Warehouse', foreign_keys=[from_wareid], backref='out_trans')
    to_ware = db.relationship('Warehouse', foreign_keys=[to_wareid], backref='in_trans')

# 创建表
with app.app_context():
    db.create_all()
    # 初始化超级管理员
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='123456', role='admin')
        db.session.add(admin)
        db.session.commit()
    # 初始化仓库
    if not Warehouse.query.first():
        wares = [
            Warehouse(name='后厨仓库'),
            Warehouse(name='吧台仓库'),
            Warehouse(name='二楼仓库'),
            Warehouse(name='三楼仓库')
        ]
        db.session.add_all(wares)
        db.session.commit()

# ------------------------------
# 登录权限装饰器
# ------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('无管理员权限')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper

# ------------------------------
# 登录 / 退出
# ------------------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        u = User.query.filter_by(username=username, password=password).first()
        if u:
            session['user_id'] = u.id
            session['username'] = u.username
            session['role'] = u.role
            return redirect(url_for('index'))
        else:
            flash('账号或密码错误')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------------------
# 首页
# ------------------------------
@app.route('/')
@login_required
def index():
    goods_count = Goods.query.count()
    ware_count = Warehouse.query.count()
    in_total = db.session.query(db.func.sum(InRecord.num)).scalar() or 0
    out_total = db.session.query(db.func.sum(OutRecord.num)).scalar() or 0

    # 预警商品
    warn_goods = []
    for g in Goods.query.all():
        stock = sum(i.num for i in g.ins) - sum(o.num for o in g.outs)
        if stock < g.warn_stock:
            warn_goods.append(g)

    return render_template('index.html',
                           goods_count=goods_count,
                           ware_count=ware_count,
                           in_total=in_total,
                           out_total=out_total,
                           warn_count=len(warn_goods))

# ------------------------------
# 用户管理（仅admin）
# ------------------------------
@app.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/user/add', methods=['POST'])
def user_add():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    if User.query.filter_by(username=username).first():
        flash('用户名已存在')
        return redirect(url_for('users'))
    u = User(username=username, password=password, role=role)
    db.session.add(u)
    db.session.commit()
    return redirect(url_for('users'))

@app.route('/user/del/<int:id>')
def user_del(id):
    u = User.query.get(id)
    if u and u.username != 'admin':
        db.session.delete(u)
        db.session.commit()
    return redirect(url_for('users'))

# ------------------------------
# 仓库管理
# ------------------------------
@app.route('/warehouse')
@login_required
def warehouse():
    wares = Warehouse.query.all()
    return render_template('warehouse.html', wares=wares)

@app.route('/warehouse/add', methods=['POST'])
def warehouse_add():
    name = request.form['name']
    remark = request.form['remark']
    w = Warehouse(name=name, remark=remark)
    db.session.add(w)
    db.session.commit()
    return redirect(url_for('warehouse'))

# ------------------------------
# 商品管理
# ------------------------------
@app.route('/goods')
@login_required
def goods():
    goods = Goods.query.all()
    return render_template('goods.html', goods=goods)

@app.route('/goods/add', methods=['POST'])
def goods_add():
    name = request.form['name']
    unit = request.form['unit']
    warn = float(request.form.get('warn_stock',0))
    remark = request.form['remark']
    g = Goods(name=name, unit=unit, warn_stock=warn, remark=remark)
    db.session.add(g)
    db.session.commit()
    return redirect(url_for('goods'))

@app.route('/goods/del/<int:id>')
def goods_del(id):
    g = Goods.query.get(id)
    db.session.delete(g)
    db.session.commit()
    return redirect(url_for('goods'))

# ------------------------------
# 入库
# ------------------------------
@app.route('/in')
@login_required
def in_list():
    records = InRecord.query.order_by(InRecord.create_time.desc()).all()
    goods = Goods.query.all()
    wares = Warehouse.query.all()
    return render_template('in.html', records=records, goods=goods, wares=wares)

@app.route('/in/add', methods=['POST'])
def in_add():
    goods_id = request.form['goods_id']
    ware_id = request.form['warehouse_id']
    num = float(request.form['num'])
    supplier = request.form['supplier']
    r = InRecord(goods_id=goods_id, warehouse_id=ware_id, num=num, supplier=supplier)
    db.session.add(r)
    db.session.commit()
    return redirect(url_for('in_list'))

# ------------------------------
# 出库
# ------------------------------
@app.route('/out')
@login_required
def out_list():
    records = OutRecord.query.order_by(OutRecord.create_time.desc()).all()
    goods = Goods.query.all()
    wares = Warehouse.query.all()
    return render_template('out.html', records=records, goods=goods, wares=wares)

@app.route('/out/add', methods=['POST'])
def out_add():
    goods_id = request.form['goods_id']
    ware_id = request.form['warehouse_id']
    num = float(request.form['num'])
    user = request.form['user']
    r = OutRecord(goods_id=goods_id, warehouse_id=ware_id, num=num, user=user)
    db.session.add(r)
    db.session.commit()
    return redirect(url_for('out_list'))

# ------------------------------
# 调拨（多仓库核心）
# ------------------------------
@app.route('/transfer')
@login_required
def transfer():
    records = Transfer.query.order_by(Transfer.create_time.desc()).all()
    goods = Goods.query.all()
    wares = Warehouse.query.all()
    return render_template('transfer.html', records=records, goods=goods, wares=wares)

@app.route('/transfer/add', methods=['POST'])
def transfer_add():
    goods_id = request.form['goods_id']
    from_ware = request.form['from_wareid']
    to_ware = request.form['to_wareid']
    num = float(request.form['num'])
    if from_ware == to_ware:
        flash('不能调拨到同一仓库')
        return redirect(url_for('transfer'))
    t = Transfer(goods_id=goods_id, from_wareid=from_ware, to_wareid=to_ware, num=num)
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('transfer'))

# ------------------------------
# 库存查询 + 预警
# ------------------------------
@app.route('/stock')
@login_required
def stock():
    goods = Goods.query.all()
    wares = Warehouse.query.all()
    stock_list = []
    for g in goods:
        in_num = sum(i.num for i in g.ins)
        out_num = sum(o.num for o in g.outs)
        trans_out = sum(t.num for t in g.transfers)
        trans_in = sum(t.num for t in Transfer.query.filter_by(goods_id=g.id).all())
        total = in_num - out_num
        warn = total < g.warn_stock
        stock_list.append({
            'name':g.name,
            'unit':g.unit,
            'in_num':in_num,
            'out_num':out_num,
            'total':total,
            'warn':warn,
            'warn_num':g.warn_stock
        })
    return render_template('stock.html', list=stock_list)

# ------------------------------
# Excel 导出（核心功能）
# ------------------------------
@app.route('/export/stock')
def export_stock():
    goods = Goods.query.all()
    data = []
    for g in goods:
        in_num = sum(i.num for i in g.ins) or 0
        out_num = sum(o.num for o in g.outs) or 0
        total = in_num - out_num
        data.append([g.name, g.unit, in_num, out_num, total, g.warn_stock])
    df = pd.DataFrame(data, columns=['商品','单位','总入库','总出库','库存','预警值'])
    return to_excel(df, '库存报表')

@app.route('/export/in')
def export_in():
    rs = InRecord.query.all()
    data = [[r.goods.name, r.warehouse.name, r.num, r.supplier, r.create_time] for r in rs]
    df = pd.DataFrame(data, columns=['商品','仓库','数量','供应商','时间'])
    return to_excel(df, '入库记录')

@app.route('/export/out')
def export_out():
    rs = OutRecord.query.all()
    data = [[r.goods.name, r.warehouse.name, r.num, r.user, r.create_time] for r in rs]
    df = pd.DataFrame(data, columns=['商品','仓库','数量','领用人','时间'])
    return to_excel(df, '出库记录')

@app.route('/export/transfer')
def export_transfer():
    ts = Transfer.query.all()
    data = [[t.goods.name, t.from_ware.name, t.to_ware.name, t.num, t.create_time] for t in ts]
    df = pd.DataFrame(data, columns=['商品','调出仓库','调入仓库','数量','时间'])
    return to_excel(df, '调拨记录')

def to_excel(df, sheet_name):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    resp = make_response(output.read())
    resp.headers["Content-Type"] = "application/vnd.ms-excel"
    resp.headers["Content-Disposition"] = f"attachment; filename={sheet_name}.xlsx"
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)