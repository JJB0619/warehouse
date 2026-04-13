import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'warehouse_secret_key'

# 初始化库存数据
def init_data():
    try:
        pd.read_excel('inventory.xlsx')
    except:
        df = pd.DataFrame(columns=['编号', '名称', '规格', '数量', '库位', '录入时间'])
        df.to_excel('inventory.xlsx', index=False)
    
    try:
        pd.read_excel('records.xlsx')
    except:
        df = pd.DataFrame(columns=['时间', '操作', '物品编号', '物品名称', '规格', '数量', '操作人', '原库位', '目标库位'])
        df.to_excel('records.xlsx', index=False)

# 用户列表
users = {
    'admin': 'admin123',
    'user1': 'user123',
    'user2': 'user223'
}

# 登录页
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            return redirect(url_for('index'))
        else:
            return render_template('login.html', msg='账号或密码错误')
    return render_template('login.html')

# 首页
@app.route('/index')
def index():
    df = pd.read_excel('inventory.xlsx')
    items = df.to_dict('records')
    hall = df[df['库位'] == '大厅'].shape[0]
    floor2 = df[df['库位'] == '二楼'].shape[0]
    floor3 = df[df['库位'] == '三楼'].shape[0]
    return render_template('index.html', items=items, hall=hall, floor2=floor2, floor3=floor3)

# 入库
@app.route('/in', methods=['POST'])
def stock_in():
    no = request.form['no']
    name = request.form['name']
    spec = request.form['spec']
    count = int(request.form['count'])
    loc = request.form['location']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    df = pd.read_excel('inventory.xlsx')
    exist = df[df['编号'] == no]
    
    if not exist.empty:
        idx = exist.index[0]
        df.at[idx, '数量'] += count
        df.at[idx, '录入时间'] = now
    else:
        new_row = {'编号':no,'名称':name,'规格':spec,'数量':count,'库位':loc,'录入时间':now}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    df.to_excel('inventory.xlsx', index=False)
    
    rec = pd.read_excel('records.xlsx')
    rec = pd.concat([rec, pd.DataFrame([{
        '时间':now,'操作':'入库','物品编号':no,'物品名称':name,
        '规格':spec,'数量':count,'操作人':'admin','原库位':'','目标库位':loc
    }])], ignore_index=True)
    rec.to_excel('records.xlsx', index=False)
    
    return redirect(url_for('index'))

# 出库
@app.route('/out', methods=['POST'])
def stock_out():
    no = request.form['no']
    count = int(request.form['count'])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    df = pd.read_excel('inventory.xlsx')
    exist = df[df['编号'] == no]
    
    if exist.empty:
        return redirect(url_for('index'))
    
    idx = exist.index[0]
    if df.at[idx,'数量'] < count:
        return redirect(url_for('index'))
    
    name = df.at[idx,'名称']
    spec = df.at[idx,'规格']
    loc = df.at[idx,'库位']
    
    df.at[idx,'数量'] -= count
    if df.at[idx,'数量'] == 0:
        df = df.drop(idx)
    
    df.to_excel('inventory.xlsx', index=False)
    
    rec = pd.read_excel('records.xlsx')
    rec = pd.concat([rec, pd.DataFrame([{
        '时间':now,'操作':'出库','物品编号':no,'物品名称':name,
        '规格':spec,'数量':count,'操作人':'admin','原库位':loc,'目标库位':''
    }])], ignore_index=True)
    rec.to_excel('records.xlsx', index=False)
    
    return redirect(url_for('index'))

# 调拨
@app.route('/transfer', methods=['GET','POST'])
def transfer():
    if request.method == 'POST':
        no = request.form['no']
        src = request.form['src']
        dst = request.form['dst']
        count = int(request.form['count'])
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.read_excel('inventory.xlsx')
        item = df[(df['编号']==no) & (df['库位']==src)]
        
        if item.empty or item.iloc[0]['数量'] < count:
            return redirect(url_for('transfer'))
        
        idx = item.index[0]
        name = item.iloc[0]['名称']
        spec = item.iloc[0]['规格']
        
        df.at[idx,'数量'] -= count
        if df.at[idx,'数量'] == 0:
            df = df.drop(idx)
        
        target = df[(df['编号']==no) & (df['库位']==dst)]
        if not target.empty:
            df.at[target.index[0],'数量'] += count
        else:
            new_row = {'编号':no,'名称':name,'规格':spec,'数量':count,'库位':dst,'录入时间':now}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        df.to_excel('inventory.xlsx', index=False)
        
        rec = pd.read_excel('records.xlsx')
        rec = pd.concat([rec, pd.DataFrame([{
            '时间':now,'操作':'调拨','物品编号':no,'物品名称':name,
            '规格':spec,'数量':count,'操作人':'admin','原库位':src,'目标库位':dst
        }])], ignore_index=True)
        rec.to_excel('records.xlsx', index=False)
        
        return redirect(url_for('index'))
    
    return render_template('transfer.html')

# 记录
@app.route('/records')
def records():
    rec = pd.read_excel('records.xlsx')
    records = rec.to_dict('records')
    return render_template('records.html', records=records)

# 导出报表
@app.route('/export')
def export():
    return send_file('inventory.xlsx', as_attachment=True)

# 用户管理
@app.route('/user')
def user():
    return render_template('user.html', users=users)

# 退出
@app.route('/logout')
def logout():
    return redirect(url_for('login'))

# 适配 Railway 端口（关键！）
if __name__ == "__main__":
    init_data()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)