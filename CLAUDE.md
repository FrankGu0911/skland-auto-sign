# 森空岛自动签到系统 - 项目文档

## 项目概述

这是一个独立的森空岛自动签到系统，不依赖 NoneBot2 和任何 IM 软件。支持多账号管理、明日方舟和终末地自动签到。

## 项目结构

```
skland-auto-sign/
├── src/
│   ├── __init__.py
│   ├── main.py              # 程序入口
│   ├── config.py            # 配置管理（Pydantic Settings + YAML）
│   ├── database.py          # 数据库连接（SQLAlchemy）
│   ├── exception.py         # 异常类定义
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py          # 用户模型
│   │   ├── character.py     # 角色模型
│   │   └── sign_record.py   # 签到记录模型
│   ├── core/                # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── skland_login.py  # 登录 API（从原项目复用）
│   │   ├── skland_api.py    # 游戏 API（从原项目复用）
│   │   └── sign_service.py  # 签到服务
│   ├── scheduler/           # 定时任务
│   │   ├── __init__.py
│   │   └── job_manager.py   # 任务管理器
│   ├── utils/               # 工具模块
│   │   ├── __init__.py
│   │   ├── logger.py        # 日志配置（loguru）
│   │   └── decorators.py    # Token 刷新装饰器
│   └── schemas/             # Pydantic 数据模型
│       ├── __init__.py
│       ├── cred.py
│       ├── arknights/
│       │   ├── __init__.py
│       │   └── sign.py
│       └── endfield/
│           ├── __init__.py
│           └── sign.py
├── config/
│   ├── config.yaml          # 应用配置
│   └── accounts.yaml        # 账号配置
├── data/                    # 数据目录
│   └── logs/                # 日志目录
├── scripts/                 # 启动脚本
│   ├── run.py              # 启动服务
│   ├── init_db.py          # 数据库初始化
│   └── run_once.py         # 单次运行
├── docker/                  # Docker 配置
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── skland-auto-sign.service
├── requirements.txt         # Python 依赖
├── README.md               # 项目说明
└── .gitignore
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

## 核心功能

### 1. 配置管理 (config.py)

- 从 YAML 文件加载配置
- 支持应用配置、数据库配置、定时任务配置、日志配置
- 账号配置支持 token 和 cred/cred_token 两种方式

### 2. 数据库 (database.py, models/)

- 使用 SQLAlchemy + aiosqlite
- 三个主要模型：
  - User: 用户（森空岛账号）
  - Character: 游戏角色
  - SignRecord: 签到记录

### 3. 核心 API (core/)

- SklandLoginAPI: 登录相关 API（获取 grant code、获取 cred、刷新 token）
- SklandAPI: 游戏 API（获取绑定、签到）
- SignService: 签到服务，整合签到逻辑

### 4. 定时任务 (scheduler/)

- 使用 APScheduler
- 支持配置签到时间
- 支持随机延迟

### 5. 工具模块 (utils/)

- logger: loguru 日志配置
- decorators: Token 自动刷新装饰器

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置账号

编辑 `config/accounts.yaml`：

```yaml
accounts:
  - name: "账号1"
    enabled: true
    token: "your_token_here"
    remark: "主账号"
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 启动服务

```bash
python scripts/run.py
```

### 5. 单次运行（测试）

```bash
python scripts/run_once.py --game all
```

## Docker 部署

```bash
cd docker
docker-compose up -d
docker-compose logs -f
```

## systemd 服务

将 `docker/skland-auto-sign.service` 复制到 `/etc/systemd/system/`，修改路径后：

```bash
systemctl daemon-reload
systemctl enable skland-auto-sign
systemctl start skland-auto-sign
systemctl status skland-auto-sign
```

## 与原项目的主要区别

1. 移除 NoneBot2 依赖
2. 移除消息发送逻辑
3. 使用标准 SQLAlchemy 替代 nonebot-plugin-orm
4. 自定义用户管理
5. 独立的配置系统（YAML）
6. 独立的日志系统

## 后续计划（第二阶段）

- FastAPI Web 管理界面
- 账号管理 API
- 签到历史查询
- 统计报表
- Webhook 通知
