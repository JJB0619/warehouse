from flask import Flask, render_template, request, redirect, flash, session, send_file
import sqlite3
import datetime
import hashlib
import pandas as pd

app = Flask(__name__)
app.secret_key = "warehouse_full_2025"

# ------------------------------
# 初始化数据库
# ------------------------------
def init_db():
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()

    # 用户表（权限）
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT,
                 role TEXT,
                 allow_hall INTEGER,
                 allow_f2 INTEGER,
                 allow_f3 INTEGER)''')

    # 商品表
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT, model TEXT, remark TEXT)''')

    # 分库库存
    c.execute('''CREATE TABLE IF NOT EXISTS stock
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 product_id INTEGER,
                 hall INTEGER DEFAULT 0,
                 f2 INTEGER DEFAULT 0,
                 f3 INTEGER DEFAULT 0)''')

    # 出入库 & 调拨记录
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 type TEXT,
                 product_id INTEGER,
                 location TEXT,
                 num INTEGER,
                 operator TEXT,
                 time TEXT,
                 remark TEXT)''')

    # 默认超级管理员 admin / admin123
    try:
        c.execute("INSERT INTO users (username,password,role,allow_hall,allow_f2,allow_f3) VALUES (?,?,?,?,?,?)",
                  ("admin", hashlib.md5("admin123".encode()).hexdigest(), "admin", 1,1,1))
    except:
        pass

    conn.commit()
    conn.close()

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()

# ------------------------------
# 登录
# ------------------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = md5(request.form['password'])
        conn = sqlite3.connect('warehouse.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = username
            session['role'] = user[2]
            session['hall'] = user[3]
            session['f2'] = user[4]
            session['f3'] = user[5]
            return redirect('/')
        else:
            flash("账号或密码错误")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ------------------------------
# 主页（库存总览）
# ------------------------------
@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()

    stock = {}
    for p in products:
        c.execute("SELECT hall,f2,f3 FROM stock WHERE product_id=?", (p[0],))
        res = c.fetchone()
        stock[p[0]] = res if res else (0, 0, 0)

    # 自动统计
    total_hall = sum([s[0] for s in stock.values()])
    total_f2 = sum([s[1] for s in stock.values()])
    total_f3 = sum([s[2] for s in stock.values()])
    total_all = total_hall + total_f2 + total_f3

    conn.close()
    return render_template('index.html',
                           products=products,
                           stock=stock,
                           total_hall=total_hall,
                           total_f2=total_f2,
                           total_f3=total_f3,
                           total_all=total_all)

# ------------------------------
# 添加商品
# ------------------------------
@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name']
    model = request.form['model']
    remark = request.form['remark']
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute("INSERT INTO products (name,model,remark) VALUES (?,?,?)",
              (name, model, remark))
    pid = c.lastrowid
    c.execute("INSERT INTO stock (product_id) VALUES (?)", (pid,))
    conn.commit()
    conn.close()
    return redirect('/')

# ------------------------------
# 入库
# ------------------------------
@app.route('/stock_in', methods=['POST'])
def stock_in():
    pid = request.form['pid']
    loc = request.form['loc']
    num = int(request.form['num'])
    remark = request.form['remark']
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute(f"UPDATE stock SET {loc} = {loc} + ? WHERE product_id=?", (num, pid))
    c.execute('INSERT INTO records (type,product_id,location,num,operator,time,remark) VALUES (?,?,?,?,?,?,?)',
              ("入库", pid, loc, num, session['user'], t, remark))
    conn.commit()
    conn.close()
    return redirect('/')

# ------------------------------
# 出库
# ------------------------------
@app.route('/stock_out', methods=['POST'])
def stock_out():
    pid = request.form['pid']
    loc = request.form['loc']
    num = int(request.form['num'])
    remark = request.form['remark']
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute(f"SELECT {loc} FROM stock WHERE product_id=?", (pid,))
    current = c.fetchone()[0]

    if current < num:
        flash("库存不足！")
        return redirect('/')

    c.execute(f"UPDATE stock SET {loc} = {loc} - ? WHERE product_id=?", (num, pid))
    c.execute('INSERT INTO records (type,product_id,location,num,operator,time,remark) VALUES (?,?,?,?,?,?,?)',
              ("出库", pid, loc, -num, session['user'], t, remark))
    conn.commit()
    conn.close()
    return redirect('/')

# ------------------------------
# 调拨
# ------------------------------
@app.route('/transfer', methods=['GET','POST'])
def transfer():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        pid = request.form['pid']
        f = request.form['from_loc']
        t = request.form['to_loc']
        num = int(request.form['num'])
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect('warehouse.db')
        c = conn.cursor()
        c.execute(f"SELECT {f} FROM stock WHERE product_id=?", (pid,))
        current = c.fetchone()[0]
        if current < num:
            flash("库存不足")
            return redirect('/transfer')

        c.execute(f"UPDATE stock SET {f} = {f} - ? WHERE product_id=?", (num, pid))
        c.execute(f"UPDATE stock SET {t} = {t} + ? WHERE product_id=?", (num, pid))
        c.execute('INSERT INTO records (type,product_id,location,num,operator,time,remark) VALUES (?,?,?,?,?,?,?)',
                  (f"调拨{f}→{t}", pid, f"{f}→{t}", num, session['user'], time_now, ""))
        conn.commit()
        conn.close()
        return redirect('/transfer')

    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template('transfer.html', products=products)

# ------------------------------
# 记录 & 日期统计
# ------------------------------
@app.route('/records')
def records():
    if 'user' not in session:
        return redirect('/login')
    date = request.args.get('date', '')
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    if date:
        c.execute('''SELECT r.*,p.name,p.model
                     FROM records r
                     LEFT JOIN products p ON r.product_id=p.id
                     WHERE r.time LIKE ?
                     ORDER BY r.id DESC''', (date + '%',))
    else:
        c.execute('''SELECT r.*,p.name,p.model
                     FROM records r
                     LEFT JOIN products p ON r.product_id=p.id
                     ORDER BY r.id DESC''')
    records = c.fetchall()
    conn.close()
    return render_template('records.html', records=records, date=date)

# ------------------------------
# 库存报表（可打印、可导出）
# ------------------------------
@app.route('/report')
def report():
    if 'user' not in session:
        return redirect('/login')
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute('''SELECT p.id,p.name,p.model,s.hall,s.f2,s.f3
                 FROM products p
                 LEFT JOIN stock s ON p.id=s.product_id
                 ORDER BY p.id''')
    data = c.fetchall()

    total_hall = sum([d[3] for d in data])
    total_f2 = sum([d[4] for d in data])
    total_f3 = sum([d[5] for d in data])
    total_all = total_hall + total_f2 + total_f3

    conn.close()
    return render_template('report.html',
                           data=data,
                           total_hall=total_hall,
                           total_f2=total_f2,
                           total_f3=total_f3,
                           total_all=total_all)

# ------------------------------
# 导出 Excel
# ------------------------------
@app.route('/export_excel')
def export_excel():
    if 'user' not in session:
        return redirect('/login')
    conn = sqlite3.connect('warehouse.db')
    df = pd.read_sql('''
        SELECT p.id AS 商品ID,
               p.name AS 商品名称,
               p.model AS 型号,
               s.hall AS 大厅库存,
               s.f2 AS 二楼库存,
               s.f3 AS 三楼库存,
               (s.hall+s.f2+s.f3) AS 总库存
        FROM products p
        LEFT JOIN stock s ON p.id = s.product_id
    ''', conn)
    conn.close()
    file = '库存报表.xlsx'
    df.to_excel(file, index=False)
    return send_file(file, as_attachment=True)

# ------------------------------
# 用户管理（子管理员+权限）
# ------------------------------
@app.route('/user')
def user():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return render_template('user.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    password = md5(request.form['password'])
    hall = request.form.get('hall', 0)
    f2 = request.form.get('f2', 0)
    f3 = request.form.get('f3', 0)
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username,password,role,allow_hall,allow_f2,allow_f3) VALUES (?,?,?,?,?,?)",
              (username, password, "user", hall, f2, f3))
    conn.commit()
    conn.close()
    return redirect('/user')

# ------------------------------
# 启动
# ------------------------------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)