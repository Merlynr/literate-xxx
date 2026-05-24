# 部署指南 - CentOS 8

## 1. 上传代码到服务器

```bash
# 在本地
scp -r . root@your-server:/opt/xxzx/

# 或用 git
ssh root@your-server
cd /opt
git clone <your-repo-url> xxzx
```

## 2. 安装系统依赖

```bash
cd /opt/xxzx/deploy
sudo bash install_env_centos.sh
```

安装内容：
- Python 3.11 (如系统 Python < 3.10)
- Node.js 18
- 编译工具链

## 3. 配置环境变量

```bash
cd /opt/xxzx/python-bff
cp .env.example .env
vim .env
```

必须配置的项：
- `DATABASE_URL` - MySQL 连接地址
- `REDIS_URL` - Redis 连接地址
- `JWT_SECRET_KEY` - JWT 密钥 (随机生成)
- `WX_APP_ID` / `WX_APP_SECRET` - 微信小程序配置
- `DASHSCOPE_API_KEY` - AI API 密钥

## 4. 初始化数据库

```bash
cd /opt/xxzx/python-bff
source .venv/bin/activate
alembic upgrade head
```

## 5. 启动服务

### 方式一：使用启动脚本 (推荐测试环境)

```bash
cd /opt/xxzx/deploy
sudo bash start_backend.sh start    # 启动 API + Worker + Beat
sudo bash start_backend.sh stop     # 停止
sudo bash start_backend.sh restart  # 重启
sudo bash start_backend.sh status   # 查看状态（含 Beat）
```

脚本方式会同时启动 Beat（`start_celery_beat`）。若已用 systemd 管理，请勿再用脚本启动，避免重复进程。

### 方式二：使用 systemd (推荐生产环境)

```bash
cd /opt/xxzx/deploy

# 一键安装三个 unit（路径会按当前代码目录替换 /opt/xxzx）
sudo bash install_systemd.sh

# 若不用 install_systemd.sh，可手动复制后 sed 改路径：
# sudo cp xxzx-backend.service xxzx-celery.service xxzx-celery-beat.service /etc/systemd/system/
# sudo systemctl daemon-reload

# 先停掉 nohup 脚本起的进程，避免重复
sudo bash start_backend.sh stop

# 启动（API + Worker + Beat）
sudo systemctl start xxzx-backend xxzx-celery xxzx-celery-beat

# 开机自启（install_systemd.sh 已 enable，可跳过）
sudo systemctl enable xxzx-backend xxzx-celery xxzx-celery-beat

# 查看状态
sudo systemctl status xxzx-backend xxzx-celery xxzx-celery-beat

# 查看日志
sudo journalctl -u xxzx-backend -f
sudo journalctl -u xxzx-celery -f
sudo journalctl -u xxzx-celery-beat -f
# 或文件：tail -f /var/log/xxzx/celery_beat.log
```

**Celery Beat 说明**

| 进程 | 作用 |
|------|------|
| `xxzx-celery` | 执行生成任务（Worker） |
| `xxzx-celery-beat` | 每 5 分钟触发 `generation.reconcile`，无人 poll 时也能恢复卡住任务 |

**全集群只运行 1 个 Beat 实例**（不要多台机器各起一个 Beat）。

Beat 调度已在 `python-bff/app/workers/celery_app.py` 的 `beat_schedule` 中配置，无需改代码。

## 6. Web 前端部署 (`web-fe`)

前端是 **Vite 构建的静态站点**（`dist/`），用 Nginx（或 Caddy）托管；接口仍走 `python-bff`（默认 `8000`）。

### 6.1 构建（本地或服务器均可）

```bash
cd web-fe
npm install

# 生产 API 地址（构建时写入 JS，按你的域名/IP 修改）
cp .env.example .env.production
# 编辑 .env.production，例如：
# VITE_API_BASE_URL=http://8.141.7.56:8000/api/v1
# 若 Nginx 把 /api 反代到本机 8000，可写：
# VITE_API_BASE_URL=/api/v1

npm run build
# 产物在 web-fe/dist/
```

### 6.2 上传到服务器

```bash
# 在本地（把路径改成你的服务器）
scp -r web-fe/dist/* root@8.141.7.56:/var/www/xxzx-web/

# 或在服务器上 git pull 后直接构建
ssh root@8.141.7.56
cd /root/literate-xxx/web-fe   # 或 /opt/xxzx/web-fe
npm install
npm run build
sudo mkdir -p /var/www/xxzx-web
sudo rsync -a --delete dist/ /var/www/xxzx-web/
```

### 6.3 Nginx（推荐：同一域名，静态 + API）

安装 Nginx 后新建站点，例如 `/etc/nginx/conf.d/xxzx-web.conf`：

```nginx
server {
    listen 80;
    server_name your-domain.com;   # 或服务器公网 IP

    root /var/www/xxzx-web;
    index index.html;

    # Vue Router history 模式：除静态资源外回落到 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 与构建变量 VITE_API_BASE_URL=/api/v1 配套
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

浏览器访问：`http://your-domain.com/app/login`（商家端）、`/admin/login`（运营端）。

**构建变量对照**

| `VITE_API_BASE_URL` | 说明 |
|---------------------|------|
| `/api/v1` | 与上面 Nginx `/api/` 反代配套（推荐，无跨域） |
| `http://IP:8000/api/v1` | 前端、API 不同端口；BFF 已开 CORS，也可用 |

### 6.4 仅静态、API 仍用 8000 端口

不配置 Nginx 反代时，`.env.production` 写完整地址：

```env
VITE_API_BASE_URL=http://8.141.7.56:8000/api/v1
```

Nginx 只托管 `dist`，并开放 80；安全组需同时放行 **80** 与 **8000**。

### 6.5 更新发布

```bash
cd /root/literate-xxx/web-fe
git pull
npm run build
sudo rsync -a --delete dist/ /var/www/xxzx-web/
```

无需重启 BFF；用户浏览器 **强刷**（Ctrl+F5）即可。

---

## 7. 仅 API 的 Nginx 反代（无 Web 静态站时）

若暂时只部署后端、不部署 `web-fe`，可把整个站点指到 FastAPI：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 8. 防火墙配置

```bash
# 开放端口
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

## 9. 日志位置

| 服务 | 日志路径 |
|------|----------|
| FastAPI | `/var/log/xxzx/backend.log` |
| Celery | `/var/log/xxzx/celery.log` |
| Celery Beat | `/var/log/xxzx/celery_beat.log` |

## 常见问题

### Q: 启动报错 "No module named 'app'"

确保在 `python-bff` 目录下启动，或设置 `PYTHONPATH`:

```bash
export PYTHONPATH=/opt/xxzx/python-bff
```

### Q: 数据库连接失败

检查 `.env` 中的 `DATABASE_URL` 格式:
```
DATABASE_URL=mysql+aiomysql://用户名:密码@localhost:3306/数据库名
```

### Q: Redis 连接失败 / 任务一直排队

生产环境 Redis 通常开启了密码，`redis-cli ping` 会返回 `NOAUTH Authentication required`，**不代表 Redis 挂了**。

```bash
# 1. 从 python-bff/.env 读取密码（与 CELery 使用同一配置）
grep -E '^(REDIS_URL|CELERY_BROKER_URL)=' /opt/xxzx/python-bff/.env

# 2. 带密码探测（把 YOUR_PASSWORD 换成 .env 里 redis://:密码@ 中的密码）
redis-cli -a 'YOUR_PASSWORD' ping
# 应返回 PONG

# 3. 后端就绪检查（含 Redis）
curl -s http://127.0.0.1:8000/api/v1/health/readiness | python3 -m json.tool

# 4. Celery 是否连上 broker（看日志里是否有连接错误）
tail -n 80 /var/log/xxzx/celery.log
```

`.env` 中 URL 格式必须为（注意密码前的冒号）：

```
REDIS_URL=redis://:你的密码@127.0.0.1:6379/0
CELERY_BROKER_URL=redis://:你的密码@127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://:你的密码@127.0.0.1:6379/2
```

修改 `.env` 后务必重启三个服务：

```bash
sudo systemctl restart xxzx-backend xxzx-celery xxzx-celery-beat
```

若 `readiness` 里 `redis` 不是 `ok`，Worker 即使 `active (running)` 也无法消费队列，前端会长期显示「排队中」。

### Q: `xxzx-celery` 状态 `203/EXEC` / `activating (auto-restart)`

systemd **无法执行** `run_celery.sh`，常见原因：

1. 脚本在 Windows 上编辑过，带 **CRLF**（`\r\n`），Linux 内核执行 shebang 失败  
2. 脚本没有 **可执行权限**（`chmod +x`）

在服务器上修复：

```bash
cd /root/literate-xxx
sed -i 's/\r$//' deploy/*.sh deploy/lib/*.sh
chmod +x deploy/run_celery.sh deploy/run_celery_beat.sh deploy/run_backend.sh
sudo bash deploy/install_systemd.sh   # 会写入 ExecStart=/bin/bash ... 并去 CRLF
sudo systemctl restart xxzx-celery xxzx-celery-beat
systemctl status xxzx-celery --no-pager
```

### Q: Beat 在跑但任务一直「排队中」/ 进度条 88%

Beat 只负责**定时发 reconcile 消息**，真正执行任务的是 **Worker**（`xxzx-celery`），不是 Beat。

```bash
# 1. 看 Worker 日志（应有 generation.process / generation.reconcile）
tail -n 100 /var/log/xxzx/celery.log

# 2. 确认 Worker 已注册任务（应包含 generation.process、generation.reconcile）
cd /opt/xxzx/python-bff   # 或你的部署目录
source .venv/bin/activate
export PYTHONPATH=$PWD
python -m celery -A app.workers.celery_app inspect registered

# 3. 手动 ping 测试
python -m celery -A app.workers.celery_app inspect ping

# 4. 看 broker 队列积压（**broker 在 Redis DB 1**，不是 DB 0）
redis-cli -a '密码' -n 1 LLEN celery

# 一键诊断（推荐）
sudo bash deploy/check_celery.sh

# 5. 更新代码后务必重启 Worker + Beat
sudo systemctl restart xxzx-celery xxzx-celery-beat
```

前端 **88%** 是「排队状态」的估算上限，**不是**生成快完成了；超过约 3 分钟排队会显示不确定进度条和橙色提示。

卡住的老任务：删除后重新提交，或等 reconcile 自动重投（最多 3 次后标记失败）。
