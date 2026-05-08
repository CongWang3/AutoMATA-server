# AutoMATA — 生信模型训练平台 AI 助手

> 从 PHP 单体架构全栈重构为 Vue3 + FastAPI 的生物学多组学数据分析平台，集成 LangGraph AI Agent 实现对话式分析。

[![Build and Deploy](https://github.com/CongWang3/AutoMATA-server/actions/workflows/deploy.yml/badge.svg)](https://github.com/CongWang3/AutoMATA-server/actions/workflows/deploy.yml)
![Commits](https://img.shields.io/badge/commits-280-blue)
![License](https://img.shields.io/badge/license-private-red)

## 核心功能

🧬 **多组学数据处理** — 转录组、蛋白质组、基因组、多组学整合、P 值整合

📊 **数据分析与可视化** — PCA、火山图、热图、GO/KEGG 富集分析、PPI 网络、Venn 图、哑铃图

🤖 **深度学习模型训练** — CNN、VAE、LSTM、Transformer、AutoEncoder、DeepCluster 等 12+ 种架构，支持监督/半监督/无监督学习

🧠 **AI Agent 对话式操作** — 基于 LangGraph 的智能助手，支持参数建议、失败诊断、结果解读三种模式，让生物学家用自然语言驱动分析

🔑 **BYOK 多模型灵活接入** — 支持用户自带 OpenAI / 通义千问 (Qwen) / DeepSeek API Key

## 技术架构

```
┌────────────────────────────────────────────────┐
│                   Nginx (:8080)                  │
│                 Vue 3 + TypeScript                │
│              Element Plus + Pinia                  │
└──────────┬──────────────────┬──────────────────┘
           │ /api/*           │ /download/*
┌──────────▼──────────┐  ┌────▼──────────────────┐
│   Backend (:8005)    │  │ Download Server (:8001) │
│   FastAPI + Celery   │  │ FastAPI                 │
│   LangGraph Agent    │  │ 文件下载/结果分发       │
└──────────┬───────────┘  └─────────┬──────────────┘
           │                        │
    ┌──────┴──────┐          ┌──────┴──────┐
    │   MySQL 8.0  │          │   Redis 7    │
    └─────────────┘          └─────────────┘
```

## 技术栈

| 层 | 技术 |
|---|---|
| **前端** | Vue 3.5 · TypeScript 5.9 · Vite 7.3 · Pinia 3 · Vue Router 5 · Element Plus · Bootstrap 5 · ECharts |
| **后端** | Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic 2.12 · Celery 5.3 · Alembic |
| **AI Agent** | LangChain 0.3 · LangGraph 0.6 · LangChain-OpenAI · WebSocket 实时通信 |
| **LLM** | OpenAI GPT-4o · 通义千问 (Qwen DashScope) · DeepSeek（BYOK 用户自带 Key） |
| **数据库** | MySQL 8.0 · Redis 7 |
| **分析引擎** | R 4.4 (DESeq2 / limma / clusterProfiler / ggplot2 等) · PyTorch 2.x · scikit-learn |
| **部署** | Docker Compose (5 容器) · Nginx · GitHub Actions CI/CD · GHCR + 阿里云 ACR 双推 · 阿里云 ECS |

## 项目规模

| 指标 | 数值 |
|---|---|
| 后端代码 | 24,219 行 Python |
| 前端代码 | 35,601 行 Vue+TS |
| API 路由 | 10 个模块 |
| 前端页面 | 33 个 Vue 视图 |
| 分析脚本 | 21 个 R 脚本 + 38 个 Python 脚本 |
| AI Agent | 7 个 LangChain Tool · 48 条脚本语义卡 · 6 个确定性规则检查器 |
| 数据库 | 50+ 张表（JWT 认证、用户、任务、文件、模型） |
| Docker | 5 容器生产编排 |

## 目录结构

```
AutoMATA/
├── automata-web/            # Vue 3 前端
│   ├── src/
│   │   ├── views/           # 33 个页面视图
│   │   │   ├── DataProcess/   # 数据处理
│   │   │   ├── DataAnalysis/  # 数据分析
│   │   │   ├── ModelTrain/    # 模型训练
│   │   │   └── ModelUse/      # 模型应用
│   │   ├── router/         # 路由
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── api/            # 后端接口封装
│   │   └── components/     # UI 组件
│   └── nginx.conf          # Nginx 配置
├── backend/                 # FastAPI 后端
│   ├── main.py             # 入口
│   ├── download_server.py  # 独立下载服务
│   ├── api/
│   │   ├── routers/        # 10 个路由模块
│   │   ├── services/       # 业务逻辑层
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── agent/          # LangGraph AI Agent
│   │   │   ├── graph.py         # StateGraph 编排
│   │   │   ├── router.py        # WebSocket 路由
│   │   │   ├── script_semantics.py  # 48 条脚本语义卡
│   │   │   ├── llm_provider.py     # 3 家 LLM 工厂
│   │   │   └── tools/             # 7 个 LangChain Tool
│   │   └── websocket/     # WebSocket 推送
│   ├── config/             # 数据库/环境配置
│   ├── alembic/            # 数据库迁移
│   └── tests/              # 26 个测试文件
├── code/                   # 59 个 R/Python 分析脚本
│   ├── *.R                 # 21 个 R 脚本（DESeq2、limma、KEGG/GO 等）
│   └── *.py                # 38 个 Python 脚本（模型训练/应用/工具）
├── deploy/                 # 部署配置
│   ├── docker-compose.prod.yml
│   ├── .env.prod.example
│   └── conda-r442.yml      # R 环境依赖
├── docs/                   # 49 个技术文档
└── .github/workflows/      # CI/CD 流水线
```

## 快速开始

### 开发环境

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.development  # 编辑数据库连接等配置
python main.py

# 前端
cd automata-web
npm install
npm run dev
```

### 生产部署

```bash
# 1. 准备环境
cp deploy/.env.prod.example .env.prod  # 编辑所有密钥和数据库密码

# 2. 拉取镜像并启动
docker compose --env-file .env.prod -f docker-compose.prod.yml pull
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

# 3. 验证
curl -fsS http://127.0.0.1:8080/     # 前端
curl -fsS http://127.0.0.1:18005/health  # 后端
curl -fsS http://127.0.0.1:18001/health  # 下载服务
```

### CI/CD 自动部署

GitHub Actions 自动构建镜像（双推 GHCR + 阿里云 ACR），SSH 远程部署到阿里云 ECS。详见 `.github/workflows/deploy.yml`。

## AI Agent 使用

通过 WebSocket 连接与 Agent 对话：

```javascript
const ws = new WebSocket("wss://your-domain/api/v1/agent/chat");

// 1. 认证
ws.send(JSON.stringify({ type: "auth", token: "your_jwt_token" }));

// 2. 对话（自动识别意图：参数建议 / 失败诊断 / 结果解读）
ws.send(JSON.stringify({ type: "chat", message: "帮我分析这个差异表达结果" }));

// 3. 指定 LLM 提供商和任务 ID
ws.send(JSON.stringify({
  type: "chat",
  message: "这个任务为什么失败了？",
  provider: "deepseek",
  job_id: "20260402175022_3b04dc64"
}));
```

## 关键设计决策

- **PHP → 前后端分离重构**：196 个 PHP 单体文件拆分为 Vue3 SPA + FastAPI RESTful，提升可维护性和扩展性
- **AI Agent 脚本语义感知**：为 59 个分析脚本建立语义卡映射＋规则检查器，实现失败任务的源码自动回读诊断
- **BYOK 多租户隔离**：用户自带 API Key 存储为独立 JSON，变更后自动失效 Agent 图缓存，兼顾安全与灵活性
- **容器化全链路部署**：前端、后端、下载服务、数据库、缓存五容器编排，GitHub Actions 一键自动部署

## License

Private — © 2026 AutoMATA Team
