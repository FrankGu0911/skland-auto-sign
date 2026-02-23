# Docker 部署说明

## 快速开始

### 1. 准备配置文件

在项目根目录创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的账号配置：

```bash
# 账号配置（JSON 格式）
ACCOUNTS_JSON='[{"name":"账号1","enabled":true,"token":"your_token_here"}]'

# 启用 Web 服务
WEB_ENABLED=true
WEB_HOST=0.0.0.0
WEB_PORT=8080
```

### 2. 启动服务

```bash
cd docker
docker-compose up -d
```

### 3. 查看日志

```bash
docker-compose logs -f
```

### 4. 停止服务

```bash
docker-compose down
```

## 端口说明

| 容器端口 | 主机端口 | 说明 |
|---------|---------|------|
| 8080 | 15151 | Web 管理界面 |

访问地址：`http://your-server-ip:15151`

## 数据持久化

数据目录挂载到 `./data`：
- `./data/skland.db` - 数据库文件
- `./data/logs/` - 日志文件

## 网络配置

服务使用独立的网络 `skland-network`，如需与其他容器通信，可以加入该网络：

```bash
docker network connect skland-network your-container
```

## 重启服务

```bash
docker-compose restart
```

## 更新服务

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 故障排查

### 查看容器状态

```bash
docker-compose ps
```

### 进入容器

```bash
docker-compose exec skland-auto-sign bash
```

### 重新初始化数据库

```bash
docker-compose exec skland-auto-sign python /app/scripts/init_db.py
```

## 堆栈名称

Docker Compose 会自动使用目录名作为堆栈前缀。当前配置：
- 容器名称：`skland-auto-sign`
- 网络名称：`skland-network`
- 堆栈名称：基于 `docker` 目录名，自动添加 `docker-` 前缀

如需自定义堆栈名称，可以使用：

```bash
docker-compose -p skland-auto-sign up -d
```
