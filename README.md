# \# 餐饮仓库管理系统（Railway生产级）

# 一套适用于餐饮行业的多仓库库存管理系统，支持管理员/普通用户权限、密码加密、多仓库管理、出入库调拨、库存预警、Excel全报表导出，100%适配Railway一键部署。

# 

# \## ✅ 核心功能

# \- 🔐 密码不可逆加密存储，保障账号安全

# \- 👤 管理员 + 普通用户双角色权限隔离

# \- 📦 多仓库管理：后厨 / 吧台 / 二楼 / 三楼（自动创建）

# \- 📊 商品管理、入库、出库、仓库间调拨全流程

# \- ⚠️ 自动库存预警，低于阈值实时提醒

# \- 📑 一键导出所有业务数据Excel报表

# \- 🚀 系统启动自动创建管理员账号，开箱即用

# \- ☁️ 100% 适配 Railway 一键部署，无任何配置

# 

# \## 🚀 Railway 一键部署步骤

# 1\. Fork 本项目到你的GitHub账号

# 2\. 登录 \[Railway](sslocal://flow/file\_open?url=https%3A%2F%2Frailway.app%2F\&flow\_extra=eyJsaW5rX3R5cGUiOiJjb2RlX2ludGVycHJldGVyIn0=)，新建项目 → 选择「Deploy from GitHub repo」

# 3\. 选择你Fork的仓库，Railway会自动识别依赖并部署

# 4\. 部署完成后，访问Railway分配的域名即可使用

# 

# \## 🔑 默认管理员账号

# \- 账号：`admin`

# \- 密码：`123456`

# > 首次登录后请立即修改密码！

# 

# \## 🛠️ 技术栈

# \- 后端：Python Flask + SQLAlchemy ORM

# \- 数据库：SQLite（本地）/ PostgreSQL（Railway生产环境）

# \- 安全：Werkzeug密码哈希加密 + Flask-Login权限控制

# \- 报表：OpenPyXL Excel生成

# \- 生产服务器：Gunicorn WSGI

# 

# \## 📝 环境变量（可选）

# 在Railway项目 → Variables中可配置：

# \- `SECRET\_KEY`：自定义应用密钥（生产环境强烈建议设置）

# \- `STOCK\_WARNING\_THRESHOLD`：自定义库存预警阈值（默认10）

# 

# \## 📄 许可证

# MIT License

