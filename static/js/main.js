function login(){
    let u = document.getElementById('username').value;
    let p = document.getElementById('password').value;
    fetch('/api/login',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({username:u,password:p})
    }).then(res=>res.json()).then(data=>{
        if(data.code===200){ location.href='/index'; }
        else{ document.getElementById('msg').innerText=data.msg; }
    })
}

function logout(){
    fetch('/api/logout').then(()=>location.href='/login');
}

function loadWarehouses(selId){
    fetch('/api/warehouse/list').then(res=>res.json()).then(data=>{
        let sel = document.getElementById(selId);
        data.data.forEach(w=>{ sel.innerHTML+=`<option value="${w.id}">${w.name}</option>`; })
    })
}

function loadProducts(selId){
    fetch('/api/product/list').then(res=>res.json()).then(data=>{
        let sel = document.getElementById(selId);
        data.data.forEach(p=>{ sel.innerHTML+=`<option value="${p.id}">${p.warehouse_name} | ${p.name}</option>`; })
    })
}

function addProduct(){
    let name = document.getElementById('pname').value;
    let spec = document.getElementById('pspec').value;
    let wid = document.getElementById('warehouse_id').value;
    fetch('/api/product/add',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({name,spec,warehouse_id:wid})
    }).then(()=>location.reload())
}

function loadProductTable(){
    fetch('/api/product/list').then(res=>res.json()).then(data=>{
        let html='<tr><th>ID</th><th>商品名</th><th>规格</th><th>仓库</th><th>库存</th></tr>';
        data.data.forEach(p=>{
            html+=`<tr><td>${p.id}</td><td>${p.name}</td><td>${p.spec}</td><td>${p.warehouse_name}</td><td>${p.stock}</td></tr>`;
        });
        document.getElementById('productTable').innerHTML=html;
    })
}

function stockIn(){
    let pid = document.getElementById('in_pid').value;
    let qty = document.getElementById('in_qty').value;
    fetch('/api/stock/in',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:pid,quantity:qty})})
    .then(()=>alert('入库成功'));
}

function stockOut(){
    let pid = document.getElementById('out_pid').value;
    let qty = document.getElementById('out_qty').value;
    fetch('/api/stock/out',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:pid,quantity:qty})})
    .then(res=>res.json()).then(d=>alert(d.msg));
}

function doTransfer(){
    let pid = document.getElementById('t_pid').value;
    let f = document.getElementById('from_wh').value;
    let t = document.getElementById('to_wh').value;
    let qty = document.getElementById('t_qty').value;
    fetch('/api/transfer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:pid,from_wh_id:f,to_wh_id:t,quantity:qty})})
    .then(res=>res.json()).then(d=>alert(d.msg));
}

function loadWarning(){
    fetch('/api/stock/warning').then(res=>res.json()).then(data=>{
        let html='<tr><th>商品</th><th>仓库</th><th>库存</th><th>预警线</th></tr>';
        data.data.forEach(w=>{
            html+=`<tr><td>${w.name}</td><td>${w.warehouse}</td><td>${w.stock}</td><td>${w.threshold}</td></tr>`;
        });
        document.getElementById('warnTable').innerHTML=html;
    })
}

function exportReport(){
    window.open('/api/export/report');
}

window.onload = function(){
    let path = location.pathname;
    if(path === '/index'){}
    if(path === '/products'){ loadWarehouses('warehouse_id'); loadProductTable(); }
    if(path === '/stock'){ loadProducts('in_pid'); loadProducts('out_pid'); }
    if(path === '/transfer'){ loadProducts('t_pid'); loadWarehouses('from_wh'); loadWarehouses('to_wh'); }
    if(path === '/warning'){ loadWarning(); }
}