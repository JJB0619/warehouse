from models import db, User, Warehouse, Product, StockIn, StockOut, Transfer
from flask_login import current_user
from openpyxl import Workbook
from datetime import datetime
import os

# ====================== 初始化服务：自动创建仓库+管理员 ======================
def init_system():
    # 自动创建4个固定仓库
    warehouse_names = ['后厨', '吧台', '二楼', '三楼']
    for name in warehouse_names:
        if not Warehouse.query.filter_by(name=name).first():
            wh = Warehouse(name=name)
            db.session.add(wh)
    
    # 自动创建管理员账号（默认：admin / 123456）
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', is_admin=True)
        admin.set_password('123456')
        db.session.add(admin)
    
    db.session.commit()

# ====================== 权限校验 ======================
def is_admin_user():
    return current_user.is_authenticated and current_user.is_admin

# ====================== 库存预警 ======================
def get_stock_warning():
    warning_products = []
    from config import Config
    products = Product.query.all()
    for p in products:
        if p.stock < Config.STOCK_WARNING_THRESHOLD:
            wh = Warehouse.query.get(p.warehouse_id)
            warning_products.append({
                'id': p.id,
                'name': p.name,
                'warehouse': wh.name if wh else '未知',
                'stock': p.stock,
                'threshold': Config.STOCK_WARNING_THRESHOLD
            })
    return warning_products

# ====================== 商品出入库/调拨核心逻辑 ======================
def stock_in_op(product_id, warehouse_id, quantity, operator):
    product = Product.query.get(product_id)
    product.stock += quantity
    record = StockIn(product_id=product_id, warehouse_id=warehouse_id, quantity=quantity, operator=operator)
    db.session.add(record)
    db.session.commit()

def stock_out_op(product_id, warehouse_id, quantity, operator):
    product = Product.query.get(product_id)
    if product.stock < quantity:
        return False
    product.stock -= quantity
    record = StockOut(product_id=product_id, warehouse_id=warehouse_id, quantity=quantity, operator=operator)
    db.session.add(record)
    db.session.commit()
    return True

def transfer_op(product_id, from_wh, to_wh, quantity, operator):
    from_p = Product.query.filter_by(id=product_id, warehouse_id=from_wh).first()
    if not from_p or from_p.stock < quantity:
        return False

    # 扣减调出仓库
    from_p.stock -= quantity

    # 增加调入仓库
    to_p = Product.query.filter_by(name=from_p.name, warehouse_id=to_wh).first()
    if to_p:
        to_p.stock += quantity
    else:
        new_p = Product(name=from_p.name, spec=from_p.spec, stock=quantity, warehouse_id=to_wh)
        db.session.add(new_p)

    record = Transfer(product_id=product_id, from_warehouse_id=from_wh, to_warehouse_id=to_wh, quantity=quantity, operator=operator)
    db.session.add(record)
    db.session.commit()
    return True

# ====================== Excel报表导出 ======================
def export_all_reports():
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "商品库存"
    
    # 库存表
    ws1.append(['商品ID', '商品名称', '规格', '仓库', '当前库存', '创建时间'])
    for p in Product.query.all():
        wh = Warehouse.query.get(p.warehouse_id)
        ws1.append([p.id, p.name, p.spec, wh.name if wh else '未知', p.stock, p.create_time])
    
    # 入库表
    ws2 = wb.create_sheet("入库记录")
    ws2.append(['ID', '商品', '仓库', '数量', '操作人', '时间'])
    for r in StockIn.query.all():
        p = Product.query.get(r.product_id)
        wh = Warehouse.query.get(r.warehouse_id)
        ws2.append([r.id, p.name if p else '未知', wh.name if wh else '未知', r.quantity, r.operator, r.create_time])
    
    # 出库表
    ws3 = wb.create_sheet("出库记录")
    ws3.append(['ID', '商品', '仓库', '数量', '操作人', '时间'])
    for r in StockOut.query.all():
        p = Product.query.get(r.product_id)
        wh = Warehouse.query.get(r.warehouse_id)
        ws3.append([r.id, p.name if p else '未知', wh.name if wh else '未知', r.quantity, r.operator, r.create_time])
    
    # 调拨表
    ws4 = wb.create_sheet("调拨记录")
    ws4.append(['ID', '商品', '调出仓库', '调入仓库', '数量', '操作人', '时间'])
    for t in Transfer.query.all():
        p = Product.query.get(t.product_id)
        fwh = Warehouse.query.get(t.from_warehouse_id)
        twh = Warehouse.query.get(t.to_warehouse_id)
        ws4.append([t.id, p.name if p else '未知', fwh.name if fwh else '未知', twh.name if twh else '未知', t.quantity, t.operator, t.create_time])

    # 保存文件
    folder = 'static/reports'
    os.makedirs(folder, exist_ok=True)
    filename = f"餐饮仓库全报表_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    path = f"{folder}/{filename}"
    wb.save(path)
    return path