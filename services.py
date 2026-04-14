from models import db, User, Warehouse, Product, StockIn, StockOut, Transfer
from flask_login import current_user
from openpyxl import Workbook
from datetime import datetime
import os

def init_system():
    warehouses = ['后厨', '吧台', '二楼', '三楼']
    for name in warehouses:
        if not Warehouse.query.filter_by(name=name).first():
            db.session.add(Warehouse(name=name))

    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', is_admin=True)
        admin.set_password('123456')
        db.session.add(admin)

    db.session.commit()

def is_admin_user():
    return current_user.is_authenticated and current_user.is_admin

def get_stock_warning():
    from config import Config
    warnings = []
    for p in Product.query.all():
        if p.stock < Config.STOCK_WARNING_THRESHOLD:
            wh = Warehouse.query.get(p.warehouse_id)
            warnings.append({
                "name": p.name,
                "warehouse": wh.name if wh else "未知",
                "stock": p.stock,
                "threshold": Config.STOCK_WARNING_THRESHOLD
            })
    return warnings

def stock_in_op(pid, wid, qty, operator):
    p = Product.query.get(pid)
    p.stock += qty
    rec = StockIn(product_id=pid, warehouse_id=wid, quantity=qty, operator=operator)
    db.session.add(rec)
    db.session.commit()

def stock_out_op(pid, wid, qty, operator):
    p = Product.query.get(pid)
    if p.stock < qty:
        return False
    p.stock -= qty
    rec = StockOut(product_id=pid, warehouse_id=wid, quantity=qty, operator=operator)
    db.session.add(rec)
    db.session.commit()
    return True

def transfer_op(pid, from_wid, to_wid, qty, operator):
    fp = Product.query.filter_by(id=pid, warehouse_id=from_wid).first()
    if not fp or fp.stock < qty:
        return False

    fp.stock -= qty

    tp = Product.query.filter_by(name=fp.name, warehouse_id=to_wid).first()
    if tp:
        tp.stock += qty
    else:
        newp = Product(name=fp.name, spec=fp.spec, stock=qty, warehouse_id=to_wid)
        db.session.add(newp)

    tr = Transfer(
        product_id=pid,
        from_warehouse_id=from_wid,
        to_warehouse_id=to_wid,
        quantity=qty,
        operator=operator
    )
    db.session.add(tr)
    db.session.commit()
    return True

def export_all_reports():
    wb = Workbook()
    ws = wb.active
    ws.title = "库存"
    ws.append(["ID","商品","规格","仓库","库存","时间"])

    for p in Product.query.all():
        wh = Warehouse.query.get(p.warehouse_id)
        ws.append([p.id, p.name, p.spec, wh.name if wh else "未知", p.stock, p.create_time])

    ws2 = wb.create_sheet("入库")
    ws2.append(["ID","商品","仓库","数量","操作人","时间"])
    for r in StockIn.query.all():
        p = Product.query.get(r.product_id)
        wh = Warehouse.query.get(r.warehouse_id)
        ws2.append([r.id, p.name if p else "未知", wh.name if wh else "未知", r.quantity, r.operator, r.create_time])

    ws3 = wb.create_sheet("出库")
    ws3.append(["ID","商品","仓库","数量","操作人","时间"])
    for r in StockOut.query.all():
        p = Product.query.get(r.product_id)
        wh = Warehouse.query.get(r.warehouse_id)
        ws3.append([r.id, p.name if p else "未知", wh.name if wh else "未知", r.quantity, r.operator, r.create_time])

    ws4 = wb.create_sheet("调拨")
    ws4.append(["ID","商品","调出","调入","数量","操作人","时间"])
    for t in Transfer.query.all():
        p = Product.query.get(t.product_id)
        f = Warehouse.query.get(t.from_warehouse_id)
        to = Warehouse.query.get(t.to_warehouse_id)
        ws4.append([t.id, p.name if p else "未知", f.name if f else "未知", to.name if to else "未知", t.quantity, t.operator, t.create_time])

    os.makedirs("static/reports", exist_ok=True)
    fn = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    path = f"static/reports/{fn}"
    wb.save(path)
    return path
