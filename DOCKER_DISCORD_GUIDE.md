# Linux Docker 部署 + Discord 推送完整指南

本文档提供 HotSpot Hunter 在 Linux 系统上使用 Docker 部署，并配置 Discord 推送通知的完整指南。

## 📋 目录

- [系统要求](#系统要求)
- [第一部分：环境准备](#第一部分环境准备)
- [第二部分：Docker 安装](#第二部分docker-安装)
- [第三部分：项目部署](#第三部分项目部署)
- [第四部分：Discord 配置](#第四部分discord-配置)
- [第五部分：启动与测试](#第五部分启动与测试)
- [第六部分：运维管理](#第六部分运维管理)
- [故障排查](#故障排查)
- [常见问题](#常见问题)

---

## 系统要求

### 硬件要求
- **CPU**: 1核心以上（推荐2核心）
- **内存**: 512MB 以上（推荐1GB）
- **磁盘**: 2GB 可用空间（用于 Docker 镜像和数据存储）

### 软件要求
- **操作系统**: Linux（Ubuntu 20.04+、Debian 10+、CentOS 7+、RHEL 8+）
- **Docker**: 20.10+ 版本
- **Docker Compose**: 1.29+ 版本（可选，推荐使用）
- **网络**: 能够访问 GitHub 和 Discord API

---

## 第一部分：环境准备

### 1.1 更新系统软件包

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 1.2 安装必要工具

```bash
# Ubuntu/Debian
sudo apt install -y git curl wget vim

# CentOS/RHEL
sudo yum install -y git curl wget vim
```

### 1.3 检查系统信息

```bash
# 查看系统版本
cat /etc/os-release

# 查看内核版本
uname -r

# 查看可用磁盘空间
df -h

# 查看内存使用情况
free -h
```

---

## 第二部分：Docker 安装

### 2.1 Ubuntu/Debian 系统安装 Docker

```bash
# 1. 卸载旧版本（如果存在）
sudo apt remove docker docker-engine docker.io containerd runc

# 2. 安装依赖包
sudo apt update
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4. 设置 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装 Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. 验证安装
sudo docker --version
sudo docker compose version
```

### 2.2 CentOS/RHEL 系统安装 Docker

```bash
# 1. 卸载旧版本
sudo yum remove docker \
    docker-client \
    docker-client-latest \
    docker-common \
    docker-latest \
    docker-latest-logrotate \
    docker-logrotate \
    docker-engine

# 2. 安装依赖
sudo yum install -y yum-utils

# 3. 添加 Docker 仓库
sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# 4. 安装 Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 6. 验证安装
sudo docker --version
sudo docker compose version
```

### 2.3 配置 Docker（所有系统通用）

```bash
# 1. 将当前用户添加到 docker 组（避免每次使用 sudo）
sudo usermod -aG docker $USER

# 2. 重新登录或执行以下命令使组权限生效
newgrp docker

# 3. 验证无需 sudo 即可运行 docker
docker ps

# 4. 配置 Docker 镜像加速（可选，国内用户推荐）
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
EOF

# 5. 重启 Docker 服务
sudo systemctl daemon-reload
sudo systemctl restart docker

# 6. 验证配置
docker info | grep -A 5 "Registry Mirrors"
```

---

## 第三部分：项目部署

### 3.1 克隆项目代码

```bash
# 1. 选择项目安装目录
cd ~

# 2. 克隆 GitHub 仓库
git clone https://github.com/starCarlos/HotSpot-Hunter.git

# 3. 进入项目目录
cd HotSpot-Hunter

# 4. 查看项目结构
ls -la
```

### 3.2 创建必要的目录

```bash
# 创建数据存储目录
mkdir -p output

# 创建配置文件目录（如果不存在）
mkdir -p config

# 验证目录创建
ls -la
```

### 3.3 配置文件准备

#### 3.3.1 AI 配置（必需）

```bash
# 复制 AI 配置示例文件
cp config/ai_config.yaml.example config/ai_config.yaml

# 编辑 AI 配置文件
vim config/ai_config.yaml
```

在编辑器中配置 AI API（示例使用 DeepSeek）：

```yaml
# AI 配置
AI_PROVIDER: "deepseek"  # 可选: openai, deepseek, anthropic
AI_MODEL: "deepseek-chat"
AI_API_KEY: "your-deepseek-api-key-here"  # 替换为你的 API Key
AI_BASE_URL: "https://api.deepseek.com"

# 分析配置
MAX_NEWS_FOR_ANALYSIS: 50
ANALYSIS_BATCH_SIZE: 10
```

保存并退出（vim 中按 `ESC`，输入 `:wq` 回车）。

#### 3.3.2 关键词配置（可选）

```bash
# 复制关键词配置示例文件
cp config/frequency_words.txt.example config/frequency_words.txt

# 编辑关键词配置（可选）
vim config/frequency_words.txt
```

#### 3.3.3 推送通知配置（Discord 配置将在第四部分详细说明）

```bash
# 复制推送配置示例文件
cp config/notification_config.yaml.example config/notification_config.yaml
```

### 3.4 检查 Docker 配置文件

```bash
# 查看 docker-compose.yml 内容
cat docker-compose.yml

# 查看 Dockerfile 内容
cat Dockerfile
```

---

## 第四部分：Discord 配置

### 4.1 创建 Discord Webhook

#### 步骤 1：打开 Discord 服务器设置

1. 打开 Discord 应用或网页版
2. 选择你要接收通知的服务器
3. 右键点击服务器名称，选择 **"服务器设置"**（Server Settings）

#### 步骤 2：创建 Webhook

1. 在左侧菜单中，点击 **"集成"**（Integrations）
2. 点击 **"Webhook"** 或 **"查看 Webhook"**
3. 点击 **"新建 Webhook"**（New Webhook）按钮

#### 步骤 3：配置 Webhook

1. **名称**：输入 Webhook 名称，例如 "HotSpot Hunter"
2. **频道**：选择要接收消息的频道（例如 #news、#alerts）
3. **头像**（可选）：上传自定义头像
4. 点击 **"复制 Webhook URL"** 按钮

#### 步骤 4：保存 Webhook URL

Webhook URL 格式如下：
```
https://discord.com/api/webhooks/{webhook_id}/{webhook_token}
```

**重要提示**：
- 请妥善保管 Webhook URL，不要泄露给他人
- 任何拥有此 URL 的人都可以向你的频道发送消息
- 如果 URL 泄露，请立即删除并重新创建 Webhook

### 4.2 配置 HotSpot Hunter

编辑推送配置文件：

```bash
# 编辑配置文件
vim config/notification_config.yaml
```

找到 Discord 配置部分，填入你的 Webhook URL：

```yaml
# Discord Webhook URL（多个用 ; 分隔）
# 获取方式：Discord 服务器设置 -> 集成 -> Webhook -> 新建 Webhook
# 格式：https://discord.com/api/webhooks/{webhook_id}/{webhook_token}
DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
```

**示例配置**：
```yaml
DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/1234567890123456789/abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
```

保存并退出（vim 中按 `ESC`，输入 `:wq` 回车）。

### 4.3 多频道配置（可选）

如果你想同时推送到多个 Discord 频道，可以使用分号 `;` 分隔多个 Webhook URL：

```yaml
DISCORD_WEBHOOK_URL: "webhook_url_1;webhook_url_2;webhook_url_3"
```

**示例**：
```yaml
DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/111/aaa;https://discord.com/api/webhooks/222/bbb"
```

### 4.4 其他推送配置（可选）

你还可以配置其他推送渠道，编辑同一个配置文件：

```yaml
# 推送配置
MAX_ACCOUNTS_PER_CHANNEL: 3  # 每个渠道最多使用的账号数量
BATCH_SEND_INTERVAL: 1.0  # 批次发送间隔（秒）

# 显示区域配置
DISPLAY:
  REGIONS:
    HOTLIST: true  # 热榜
    RSS: true  # RSS
    AI_ANALYSIS: true  # AI 分析
    STANDALONE: false  # 独立展示区
```

---

## 第五部分：启动与测试

### 5.1 构建 Docker 镜像

```bash
# 确保在项目根目录
cd ~/HotSpot-Hunter

# 使用 Docker Compose 构建镜像
docker compose build

# 或者使用 docker-compose（旧版本）
docker-compose build
```

构建过程可能需要几分钟，请耐心等待。

### 5.2 启动服务

```bash
# 使用 Docker Compose 启动服务（后台运行）
docker compose up -d

# 或者使用 docker-compose（旧版本）
docker-compose up -d
```

**预期输出**：
```
[+] Running 1/1
 ✔ Container hotspot-hunter-api  Started
```

### 5.3 检查服务状态

```bash
# 查看容器状态
docker compose ps

# 预期输出（STATUS 应该是 Up）
NAME                   IMAGE                      STATUS         PORTS
hotspot-hunter-api     hotspot-hunter-api:latest  Up 10 seconds  0.0.0.0:1236->1236/tcp
```

### 5.4 查看日志

```bash
# 实时查看日志
docker compose logs -f

# 查看最近 100 行日志
docker compose logs --tail=100

# 只查看特定服务的日志
docker compose logs -f hotspot-hunter-api
```

**正常启动的日志示例**：
```
hotspot-hunter-api  | INFO:     Started server process [1]
hotspot-hunter-api  | INFO:     Waiting for application startup.
hotspot-hunter-api  | [API] 使用数据目录: /app/output
hotspot-hunter-api  | [调度器] 定时任务调度器已启动
hotspot-hunter-api  | INFO:     Application startup complete.
hotspot-hunter-api  | INFO:     Uvicorn running on http://0.0.0.0:1236
```

按 `Ctrl+C` 退出日志查看。

### 5.5 访问 Web 界面

打开浏览器，访问以下地址：

```
http://your-server-ip:1236
```

将 `your-server-ip` 替换为你的服务器 IP 地址。

**本地测试**：
```
http://localhost:1236
```

**API 文档**：
```
http://your-server-ip:1236/docs
```

**健康检查**：
```
http://your-server-ip:1236/api/health
```

### 5.6 手动抓取数据并测试 Discord 推送

```bash
# 进入容器
docker compose exec hotspot-hunter-api bash

# 在容器内执行数据抓取
python crawl_data.py

# 退出容器
exit
```

**预期输出**：
```
开始抓取新闻数据...
成功抓取 XX 条新闻
Discord消息分为 X 批次发送 [当日汇总]
发送Discord第 1/X 批次，大小：XXX 字符 [当日汇总]
Discord第 1/X 批次发送成功 [当日汇总]
Discord所有 X 批次发送完成 [当日汇总]
```

### 5.7 验证 Discord 消息

1. 打开你的 Discord 应用
2. 进入配置的频道
3. 你应该能看到来自 HotSpot Hunter 的消息

**消息内容包括**：
- 📰 热点新闻标题和链接
- 📊 统计信息
- 🤖 AI 分析结果（如果启用）
- 🔗 RSS 订阅内容（如果启用）

---

## 第六部分：运维管理

### 6.1 常用管理命令

```bash
# 查看容器状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 重启服务
docker compose restart

# 停止服务
docker compose stop

# 启动服务
docker compose start

# 停止并删除容器
docker compose down

# 重新构建并启动
docker compose up -d --build
```

### 6.2 进入容器调试

```bash
# 进入容器 bash
docker compose exec hotspot-hunter-api bash

# 查看配置文件
cat /app/config/notification_config.yaml

# 查看数据目录
ls -la /app/output

# 手动执行抓取
python crawl_data.py

# 退出容器
exit
```

### 6.3 数据备份

```bash
# 备份数据目录
tar -czf hotspot-hunter-backup-$(date +%Y%m%d).tar.gz output/

# 备份配置文件
tar -czf hotspot-hunter-config-$(date +%Y%m%d).tar.gz config/

# 查看备份文件
ls -lh *.tar.gz
```

### 6.4 数据恢复

```bash
# 恢复数据目录
tar -xzf hotspot-hunter-backup-20240101.tar.gz

# 恢复配置文件
tar -xzf hotspot-hunter-config-20240101.tar.gz
```

### 6.5 更新升级

```bash
# 1. 停止服务
docker compose down

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建镜像
docker compose build

# 4. 启动服务
docker compose up -d

# 5. 查看日志确认启动成功
docker compose logs -f
```

### 6.6 定时任务配置

HotSpot Hunter 默认启用定时任务，每小时自动抓取一次数据。

**查看定时任务状态**：
```bash
# 访问健康检查接口
curl http://localhost:1236/api/health
```

**修改定时任务配置**：

编辑 `docker-compose.yml` 文件：
```yaml
environment:
  - CRAWL_SCHEDULER_ENABLED=true  # 启用/禁用定时任务
  - CRAWL_INTERVAL_HOURS=2.0      # 修改抓取间隔（小时）
```

修改后重启服务：
```bash
docker compose down
docker compose up -d
```

### 6.7 日志管理

```bash
# 查看日志大小
docker compose logs --tail=0 | wc -l

# 清理日志（重启容器）
docker compose restart

# 限制日志大小（编辑 docker-compose.yml）
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## 故障排查

### 问题 1：容器无法启动

**症状**：执行 `docker compose up -d` 后容器立即退出

**排查步骤**：

```bash
# 1. 查看容器状态
docker compose ps

# 2. 查看详细日志
docker compose logs hotspot-hunter-api

# 3. 检查端口占用
sudo netstat -tulpn | grep 1236
# 或
sudo lsof -i :1236
```

**常见原因**：
- 端口 1236 被占用
- 配置文件格式错误
- 缺少必要的配置文件

**解决方案**：
```bash
# 如果端口被占用，修改 docker-compose.yml 中的端口映射
ports:
  - "8080:1236"  # 将宿主机端口改为 8080

# 检查配置文件是否存在
ls -la config/
```

### 问题 2：Discord 推送失败

**症状**：日志显示 Discord 发送失败

**排查步骤**：

```bash
# 1. 检查配置文件
docker compose exec hotspot-hunter-api cat /app/config/notification_config.yaml | grep DISCORD

# 2. 测试 Webhook URL
curl -X POST "YOUR_DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "测试消息"}'
```

**常见原因**：
- Webhook URL 配置错误
- Webhook 已被删除或失效
- 网络连接问题

**解决方案**：
```bash
# 1. 重新创建 Discord Webhook
# 2. 更新配置文件
vim config/notification_config.yaml

# 3. 重启服务
docker compose restart
```

### 问题 3：无法访问 Web 界面

**症状**：浏览器无法打开 `http://server-ip:1236`

**排查步骤**：

```bash
# 1. 检查容器是否运行
docker compose ps

# 2. 检查端口映射
docker compose port hotspot-hunter-api 1236

# 3. 检查防火墙
sudo ufw status
sudo firewall-cmd --list-ports  # CentOS/RHEL
```

**解决方案**：

```bash
# Ubuntu/Debian 开放端口
sudo ufw allow 1236/tcp
sudo ufw reload

# CentOS/RHEL 开放端口
sudo firewall-cmd --permanent --add-port=1236/tcp
sudo firewall-cmd --reload
```

### 问题 4：数据抓取失败

**症状**：日志显示抓取错误或无数据

**排查步骤**：

```bash
# 1. 进入容器手动测试
docker compose exec hotspot-hunter-api bash
python crawl_data.py

# 2. 检查网络连接
curl -I https://api.example.com

# 3. 查看详细错误日志
docker compose logs --tail=100 | grep -i error
```

**常见原因**：
- API 配置错误
- 网络连接问题
- API 限流

### 问题 5：AI 分析不工作

**症状**：没有 AI 分析结果

**排查步骤**：

```bash
# 检查 AI 配置
docker compose exec hotspot-hunter-api cat /app/config/ai_config.yaml
```

**解决方案**：
- 确认 AI_API_KEY 已正确配置
- 检查 API 额度是否充足
- 验证 API 端点是否可访问

---

## 常见问题

### Q1: 如何修改抓取频率？

**A**: 编辑 `docker-compose.yml`，修改环境变量：

```yaml
environment:
  - CRAWL_INTERVAL_HOURS=2.0  # 改为 2 小时抓取一次
```

然后重启服务：
```bash
docker compose down && docker compose up -d
```

### Q2: 如何禁用定时任务？

**A**: 编辑 `docker-compose.yml`：

```yaml
environment:
  - CRAWL_SCHEDULER_ENABLED=false
```

### Q3: Discord 消息太长被截断怎么办？

**A**: HotSpot Hunter 会自动将长消息分批发送，每批最多 2000 字符。你可以在配置中调整批次间隔：

```yaml
BATCH_SEND_INTERVAL: 2.0  # 增加到 2 秒
```

### Q4: 如何查看 Discord Webhook 是否有效？

**A**: 使用 curl 测试：

```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "测试消息"}'
```

如果返回空响应且状态码为 204，说明 Webhook 有效。

### Q5: 如何同时推送到多个 Discord 频道？

**A**: 在配置文件中使用分号分隔多个 Webhook URL：

```yaml
DISCORD_WEBHOOK_URL: "webhook1;webhook2;webhook3"
```

### Q6: 容器重启后数据会丢失吗？

**A**: 不会。数据存储在 `./output` 目录，已通过 volume 挂载到宿主机，容器重启不影响数据。

### Q7: 如何在后台运行并开机自启？

**A**: Docker Compose 默认配置了 `restart: unless-stopped`，容器会自动重启。

要设置开机自启动 Docker 服务：
```bash
sudo systemctl enable docker
```

### Q8: 如何更换 Discord Webhook？

**A**: 编辑配置文件，替换 Webhook URL，然后重启服务：

```bash
vim config/notification_config.yaml
docker compose restart
```

---

## 安全建议

### 1. 保护配置文件

```bash
# 设置配置文件权限
chmod 600 config/notification_config.yaml
chmod 600 config/ai_config.yaml

# 确保配置文件不被提交到 Git
echo "config/notification_config.yaml" >> .gitignore
echo "config/ai_config.yaml" >> .gitignore
```

### 2. 使用环境变量（推荐）

创建 `.env` 文件存储敏感信息：

```bash
# 创建 .env 文件
cat > .env << 'EOF'
AI_API_KEY=your-api-key-here
DISCORD_WEBHOOK_URL=your-webhook-url-here
EOF

# 设置权限
chmod 600 .env

# 添加到 .gitignore
echo ".env" >> .gitignore
```

### 3. 定期更新

```bash
# 定期更新系统和 Docker
sudo apt update && sudo apt upgrade -y
docker compose pull
docker compose up -d --build
```

---

## 性能优化

### 1. 限制容器资源

编辑 `docker-compose.yml`，添加资源限制：

```yaml
services:
  hotspot-hunter-api:
    # ... 其他配置 ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 2. 使用 Docker 镜像加速

```bash
# 编辑 Docker 配置
sudo vim /etc/docker/daemon.json

# 添加镜像源
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}

# 重启 Docker
sudo systemctl restart docker
```

### 3. 优化日志配置

```yaml
# 在 docker-compose.yml 中添加
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## 快速参考命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 进入容器
docker compose exec hotspot-hunter-api bash

# 手动抓取数据
docker compose exec hotspot-hunter-api python crawl_data.py

# 查看容器状态
docker compose ps

# 更新服务
git pull && docker compose up -d --build

# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz output/ config/
```

---

## 总结

恭喜！你已经成功完成了 HotSpot Hunter 在 Linux 上的 Docker 部署，并配置了 Discord 推送通知。

**你已经完成的工作**：
- ✅ 安装并配置 Docker 环境
- ✅ 部署 HotSpot Hunter 应用
- ✅ 配置 Discord Webhook 推送
- ✅ 设置定时任务自动抓取
- ✅ 了解运维管理命令

**下一步建议**：
1. 配置其他推送渠道（Telegram、Slack 等）
2. 调整 AI 分析参数优化结果
3. 设置数据备份计划
4. 监控服务运行状态
5. 根据需求调整抓取频率

**相关文档**：
- [README.md](README.md) - 项目主文档
- [DOCKER.md](DOCKER.md) - Docker 部署详细说明
- [NOTIFICATION.md](NOTIFICATION.md) - 推送功能使用指南
- [config/README.md](config/README.md) - 配置文件说明

**获取帮助**：
- GitHub Issues: https://github.com/starCarlos/HotSpot-Hunter/issues
- 项目文档: https://github.com/starCarlos/HotSpot-Hunter

---

**文档版本**: v1.0
**最后更新**: 2026-01-30
**作者**: HotSpot Hunter Team

