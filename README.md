# 森空岛自动签到系统

独立的森空岛自动签到服务，支持明日方舟和终末地自动签到，带 Web 管理界面。

## 功能特性

- 多账号管理
- 明日方舟自动签到
- 终末地自动签到
- Token 自动刷新
- 定时任务调度
- 签到记录存储
- Web 管理界面
- Docker 部署支持

## 快速开始

### 方式一：命令行模式

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置账号

编辑 `config/accounts.yaml`，添加您的森空岛账号信息：

```yaml
accounts:
  - name: "账号1"
    enabled: true
    token: "your_access_token_here"
    remark: "主账号"
```

#### 3. 初始化数据库

```bash
python scripts/init_db.py
```

#### 4. 启动服务

```bash
python scripts/run.py
```

### 方式二：Web 管理模式（推荐）

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 初始化数据库

```bash
python scripts/init_db.py
```

#### 3. 启动 Web 服务

```bash
python scripts/run_web.py
```

#### 4. 访问管理界面

打开浏览器访问：`http://localhost:8080`

在 Web 界面中添加和管理账号。

### 单次运行（测试）

```bash
# 签到所有游戏
python scripts/run_once.py

# 只签到明日方舟
python scripts/run_once.py --game arknights

# 只签到终末地
python scripts/run_once.py --game endfield
```

## Docker 部署（推荐）

Docker 部署是最简单的方式，容器启动时会自动初始化数据库。

### Linux/macOS

```bash
cd docker
./start.sh
```

### Windows

```bash
cd docker
start.bat
```

### 或者使用 Docker Compose 命令

```bash
cd docker
docker-compose up --build -d
```

### 访问 Web 界面

打开浏览器访问：`http://localhost:8080`

### 查看日志

```bash
cd docker
docker-compose logs -f
```

### 停止服务

```bash
cd docker
./stop.sh       # Linux/macOS
# 或
stop.bat        # Windows
# 或
docker-compose down
```

## 配置说明

### config.yaml

```yaml
app:
  name: "Skland Auto Sign"
  version: "1.0.0"
  debug: false

database:
  type: "sqlite"
  url: "sqlite:///data/skland.db"

scheduler:
  arknights_sign_time: "00:15"
  endfield_sign_time: "00:20"
  timezone: "Asia/Shanghai"
  random_delay: 300

logging:
  level: "INFO"
  dir: "data/logs"
  retention: "30 days"
  rotation: "1 day"

web:
  enabled: true
  host: "0.0.0.0"
  port: 8080
```

### accounts.yaml

```yaml
accounts:
  - name: "账号1"
    enabled: true
    token: "your_access_token_here"
    remark: "主账号"
```

## Web 管理界面功能

### 概览统计
- 总用户数、启用用户数
- 游戏角色总数
- 今日签到统计

### 账号管理
- 添加/删除账号
- 启用/禁用账号
- 同步游戏角色
- 刷新登录凭证

### 签到管理
- 立即执行签到（全部/明日方舟/终末地）
- 查看签到结果

### 签到记录
- 查看历史签到记录
- 按日期/状态/游戏类型筛选

### 统计信息
- 每日签到统计
- 游戏签到成功率
- 用户签到排行

## API 接口

### 账号管理
- `GET /api/accounts/` - 获取账号列表
- `POST /api/accounts/` - 创建账号
- `PUT /api/accounts/{id}` - 更新账号
- `DELETE /api/accounts/{id}` - 删除账号
- `POST /api/accounts/{id}/refresh` - 刷新凭证
- `POST /api/accounts/{id}/sync` - 同步角色

### 签到管理
- `POST /api/sign/run` - 执行签到
- `POST /api/sign/account/{id}` - 为指定账号签到
- `GET /api/sign/status` - 获取签到状态
- `GET /api/sign/schedule` - 获取定时任务配置

### 签到记录
- `GET /api/records/` - 获取签到记录列表
- `GET /api/records/{id}` - 获取记录详情
- `GET /api/records/user/{id}` - 获取用户记录
- `DELETE /api/records/old` - 删除旧记录

### 统计信息
- `GET /api/stats/overview` - 获取概览统计
- `GET /api/stats/games` - 获取游戏统计
- `GET /api/stats/daily` - 获取每日统计
- `GET /api/stats/users` - 获取用户统计

## 获取 Token

1. 打开森空岛 APP
2. 抓包获取请求头中的 `token` 字段
3. 或使用 Charles/Fiddler 等抓包工具

## systemd 服务

将 `docker/skland-auto-sign.service` 复制到 `/etc/systemd/system/`，修改路径后：

```bash
systemctl daemon-reload
systemctl enable skland-auto-sign
systemctl start skland-auto-sign
systemctl status skland-auto-sign
```

## 项目结构

```
skland-auto-sign/
├── src/
│   ├── main.py              # 程序入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # 数据模型
│   ├── core/                # 核心业务逻辑
│   ├── scheduler/           # 定时任务
│   ├── utils/               # 工具模块
│   ├── schemas/             # 数据模型
│   └── api/                 # Web API
│       ├── app.py           # FastAPI 应用
│       ├── routes/          # API 路由
│       └── templates/       # 前端模板
├── config/
│   ├── config.yaml          # 配置文件
│   └── accounts.yaml        # 账号配置
├── data/                    # 数据目录
├── scripts/                 # 脚本
│   ├── run.py              # 启动服务
│   ├── run_web.py          # 启动 Web 服务
│   ├── init_db.py          # 数据库初始化
│   └── run_once.py         # 单次运行
├── docker/                  # Docker 配置
├── requirements.txt         # 依赖列表
└── README.md
```

## 技术栈

- Python 3.10+
- httpx - HTTP 客户端
- SQLAlchemy - ORM
- aiosqlite - 异步 SQLite
- APScheduler - 定时任务
- Pydantic - 数据验证
- PyYAML - 配置文件解析
- loguru - 日志记录
- FastAPI - Web 框架
- uvicorn - ASGI 服务器
- Jinja2 - 模板引擎

## 许可证

MIT License
