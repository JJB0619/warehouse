function login(){
  const u = document.getElementById('username').value
  const p = document.getElementById('password').value
  fetch('/api/login',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({username:u,password:p})
  }).then(r=>r.json()).then(d=>{
    if(d.code===200)location.href='/index'
    else document.getElementById('msg').innerText=d.msg
  })
}

function logout(){
  fetch('/api/logout').then(()=>location.href='/login')
}

function loadWarehouses(id){
  fetch('/api/warehouse/list').then(r=>r.json()).then(d=>{
    const sel = document.getElementById(id)
    d.data.forEach(w=>sel.innerHTML+=`<option value="${w.id}">${w.name}</option>`)
  })
}

function loadProducts(id){
  fetch('/api/product/list').then(r=>r.json()).then(d=>{
    const sel = document.getElementById(id)
    d.data.forEach(p=>sel.innerHTML+=`<option value="${p.id}">${p.warehouse_name} | ${p.name}</option>`)
  })
}

function addProduct(){
  const name = document.getElementById('pname').value
  const spec = document.getElementById('pspec').value
  const wid = document.getElementById('warehouse_id').value
  fetch('/api/product/add',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name,spec,warehouse_id:wid})
  }).then(()=>location.reload())
}

function loadProductTable(){
  fetch('/api/product/list').then(r=>r.json()).then(d=>{
    let html='<tr><th>ID</th><th>商品</th><th>规格</th><th>仓库</th><th>库存</th></tr>'
    d.data.forEach(p=>{
      html+=`<tr><td>${p.id}</td><td>${p.name}</td><td>${p.spec}</td><td>${p.warehouse_name}</td><td>${p.stock}</td></tr>`
    })
    document.getElementById('productTable').innerHTML=html
  })
}

function stockIn(){
  const pid = document.getElementById('in_pid').value
  const qty = document.getElementById('in_qty').value
  fetch('/api/stock/in',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({product_id:pid,quantity:qty,warehouse_id:0})
  }).then(()=>alert('成功'))
}

function stockOut(){
  const pid = document.getElementById('out_pid').value
  const qty = document.getElementById('out_qty').value
  fetch('/api/stock/out',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({product_id:pid,quantity:qty,warehouse_id:0})
  }).then(r=>r.json()).then(d=>alert(d.msg))
}

function doTransfer(){
  const pid = document.getElementById('t_pid').value
  const f = document.getElementById('from_wh').value
  const t = document.getElementById('to_wh').value
  const qty = document.getElementById('t_qty').value
  fetch('/api/transfer',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({product_id:pid,from_wh_id:f,to_wh_id:t,quantity:qty})
  }).then(r=>r.json()).then(d=>alert(d.msg))
}

function loadWarning(){
  fetch('/api/stock/warning').then(r=>r.json()).then(d=>{
    let html='<tr><th>商品</th><th>仓库</th><th>库存</th><th>预警线</th></tr>'
    d.data.forEach(w=>{
      html+=`<tr><td>${w.name}</td><td>${w.warehouse}</td><td>${w.stock}</td><td>${w.threshold}</td></tr>`
    })
    document.getElementById('warnTable').innerHTML=html
  })
}

function exportReport(){
  window.open('/api/export/report')
}

function addUser(){
  const user = document.getElementById('new_username').value
  const pwd = document.getElementById('new_password').value
  const admin = document.getElementById('is_admin').value==='true'
  fetch('/api/admin/user/add',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({username:user,password:pwd,is_admin:admin})
  }).then(r=>r.json()).then(d=>{alert(d.msg);if(d.code===200)location.reload()})
}

function loadUserTable(){
  fetch('/api/admin/user/list').then(r=>r.json()).then(d=>{
    let html='<tr><th>ID</th><th>账号</th><th>角色</th></tr>'
    d.data.forEach(u=>{
      html+=`<tr><td>${u.id}</td><td>${u.username}</td><td>${u.role}</td></tr>`
    })
    document.getElementById('userTable').innerHTML=html
  })
}

window.onload=function(){
  const p = location.pathname
  if(p==='/products'){loadWarehouses('warehouse_id');loadProductTable()}
  if(p==='/stock'){loadProducts('in_pid');loadProducts('out_pid')}
  if(p==='/transfer'){loadProducts('t_pid');loadWarehouses('from_wh');loadWarehouses('to_wh')}
  if(p==='/warning'){loadWarning()}
  if(p==='/users'){loadUserTable()}
}