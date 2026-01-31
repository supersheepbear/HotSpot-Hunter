# Linux Docker 部署 + Discord 推送快速指南

> 🚀 5 分钟快速部署 HotSpot Hunter 并配置 Discord 推送

## 📋 前置要求

- Linux 服务器（Ubuntu 20.04+ 或 CentOS 7+）
- 已安装 Docker 和 Docker Compose
- Discord 账号和服务器

---

## 第一步：安装 Docker（如果未安装）

### Ubuntu/Debian 系统

```bash
# 一键安装 Docker
curl -fsSL https://get.docker.com | bash

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker
```

### CentOS/RHEL 系统

```bash
# 一键安装 Docker
curl -fsSL https://get.docker.com | bash

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker
```

---

## 第二步：部署 HotSpot Hunter

```bash
# 1. 克隆项目
git clone https://github.com/starCarlos/HotSpot-Hunter.git
cd HotSpot-Hunter

# 2. 创建数据目录
mkdir -p output

# 3. 复制配置文件
cp config/ai_config.yaml.example config/ai_config.yaml
cp config/notification_config.yaml.example config/notification_config.yaml
```

---

## 第三步：配置 AI（必需）

编辑 AI 配置文件：

```bash
vim config/ai_config.yaml
```

填入你的 AI API Key：

```yaml
AI_PROVIDER: "deepseek"
AI_MODEL: "deepseek-chat"
AI_API_KEY: "your-api-key-here"  # 替换为你的 API Key
AI_BASE_URL: "https://api.deepseek.com"
```

保存退出（按 `ESC`，输入 `:wq` 回车）。

---

## 第四步：配置 Discord

### 4.1 创建 Discord Webhook

1. 打开 Discord，进入你的服务器
2. 右键点击服务器名称 → **服务器设置**
3. 点击 **集成** → **Webhook**
4. 点击 **新建 Webhook**
5. 设置名称（如 "HotSpot Hunter"）和频道
6. 点击 **复制 Webhook URL**

### 4.2 配置 Webhook

编辑推送配置文件：

```bash
vim config/notification_config.yaml
```

找到 Discord 部分，粘贴你的 Webhook URL：

```yaml
# Discord Webhook URL（多个用 ; 分隔）
DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN"
```

保存退出。

---

## 第五步：启动服务

```bash
# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f
```

看到以下日志说明启动成功：

```
INFO:     Uvicorn running on http://0.0.0.0:1236
[调度器] 定时任务调度器已启动
```

按 `Ctrl+C` 退出日志查看。

---

## 第六步：测试 Discord 推送

```bash
# 手动抓取数据并推送到 Discord
docker compose exec hotspot-hunter-api python crawl_data.py
```

几秒钟后，你应该能在 Discord 频道看到推送的消息！

---

## 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 手动抓取数据
docker compose exec hotspot-hunter-api python crawl_data.py
```

---

## 访问 Web 界面

打开浏览器访问：

```
http://your-server-ip:1236
```

API 文档：`http://your-server-ip:1236/docs`

---

## 自动抓取配置

默认每小时自动抓取一次。如需修改频率，编辑 `docker-compose.yml`：

```yaml
environment:
  - CRAWL_INTERVAL_HOURS=2.0  # 改为 2 小时
```

然后重启：

```bash
docker compose restart
```

---

## 多频道推送

如果想推送到多个 Discord 频道，在配置文件中用分号分隔：

```yaml
DISCORD_WEBHOOK_URL: "webhook1;webhook2;webhook3"
```

---

## 常见问题

### Q: 端口 1236 被占用怎么办？

编辑 `docker-compose.yml`，修改端口映射：

```yaml
ports:
  - "8080:1236"  # 改为 8080
```

### Q: Discord 没收到消息？

1. 检查 Webhook URL 是否正确
2. 测试 Webhook：

```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "测试消息"}'
```

### Q: 如何查看详细日志？

```bash
docker compose logs --tail=100
```

---

## 完成！

🎉 恭喜！你已经成功部署 HotSpot Hunter 并配置了 Discord 推送。

**下一步**：
- 调整抓取频率
- 配置其他推送渠道（Telegram、Slack 等）
- 查看 [完整文档](DOCKER_DISCORD_GUIDE.md) 了解更多高级功能

**获取帮助**：
- GitHub: https://github.com/starCarlos/HotSpot-Hunter
- 完整指南: [DOCKER_DISCORD_GUIDE.md](DOCKER_DISCORD_GUIDE.md)

---

**文档版本**: v1.0 (简化版)
**最后更新**: 2026-01-30
