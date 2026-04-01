# 桌面版（乙）：联网 pull 镜像安装方案

日期：2026-04-01  
状态：草案（待产品决策）  
范围：用户本机 **Docker** 运行全套 AutoMATA 服务，任务在用户电脑执行；**首次安装与更新镜像依赖网络**，从镜像仓库拉取。目标平台：**Windows、Linux**，容器平台 **`linux/amd64` 单架构**（x86-64 PC）。

## 1. 背景与目标

### 1.1 与网页版、生产部署的关系

- 与 **docker-compose.prod.yml** 同属「多容器 + 前端 nginx 反代」思路，但桌面版需额外满足：
  - **胖后端**：含 **R**、Python 分析/训练依赖，以及可访问的 **`code/`** 脚本树（当前生产用 `backend/Dockerfile` 仅为 Python slim，**不足以**覆盖乙类全功能）。
  - **独立下载服务**：`download_server`（原 8001）与 **FastAPI**（8005）一并纳入 compose；经由 **同源 nginx** 暴露下载路径，避免前端写死 `http://localhost:8001`。
- **桌面壳**（Electron 或 Tauri）：检测 Docker → 启动/停止 compose 工程 → 健康检查 → 内嵌 WebView 打开本地入口 URL。

### 1.2 成功标准（本方案）

- 用户在 **已安装 Docker**（Win：Docker Desktop；Linux：Docker Engine + 可选 compose plugin）且 **可访问镜像仓库** 的前提下，完成安装后能 **离线使用业务**（不连业务服务器即可跑任务），直至用户主动更新镜像。
- **同一 `linux/amd64` 镜像 tag** 供 Windows 与 Linux 上的 Docker 拉取（均为 Linux 容器）。

---

## 2. 架构概要

```
[桌面壳] --spawn--> docker compose up/down
                        |
    +-------------------+-------------------+
    v                   v                   v
 [nginx:前端+反代]   [backend:8005]    [download:8001]
    |                   |                   |
    +---------> 同卷: code、uploaded_files、download_data 等 <----------+
    |                   v                   v                           |
    +--------------> [MySQL] [Redis] <-------------------------------------+
```

- **前端**：Vite 构建产物由 nginx 容器提供；浏览器/WebView 只访问 **单一 origin**（如 `http://127.0.0.1:<hostPort>`）。
- **API/WebSocket**：nginx → `backend:8005` 的 `/api/`、`/ws/`（与现有 `automata-web/nginx.conf` 延伸一致）。
- **下载**：nginx → download 服务路径（需在桌面 compose/nginx 中 **新增** location，生产域名部署若尚未统一也应与此 spec 对齐）。

---

## 3. 镜像与仓库

| 镜像角色 | 说明 |
|----------|------|
| 前端 | 现有 `automata-frontend` 思路或可合并进单一「门户」镜像；以 compose 为准。 |
| 后端（桌面） | **新建/独立 Dockerfile**（或目标阶段）：内置 R 与 Python 依赖、工作目录与脚本路径通过**环境变量**与卷挂载对齐，避免硬编码仅适用于开发机的绝对路径。 |
| 下载服务 | 可与后端共用镜像不同 CMD，或独立镜像；需能连接同一 MySQL、同一文件根。 |
| mysql / redis | 可选用与 **docker-compose.prod.yml** 相同主版本的基础镜像。 |

- **注册表**：例如 **GHCR**（`ghcr.io/<owner>/...`），与现有 CI 发布流程衔接。
- **平台**：构建与推送 **`linux/amd64` 单平台**；不在首版要求 `arm64`。

---

## 4. 桌面壳职责

1. **环境**：检测 `docker` 与 `docker compose`（或 `docker-compose`）可用；可选检测 WSL2（Win）。
2. **生命周期**：在**固定项目目录**下执行 `compose up -d`；退出时可 `compose stop` 或 `down`（是否 `down -v` 需产品决策并写入用户文档）。
3. **就绪**：轮询 FastAPI `/health`、下载服务探测、MySQL/Redis 就绪（顺序与超时策略可配置）。
4. **界面**：打开 WebView 至 `http://127.0.0.1:<PUBLISHED_FRONTEND_PORT>`；失败时展示最近日志路径或 `docker compose logs` 摘录。
5. **更新**：提供「检查更新」→ `docker compose pull` → `compose up -d`（**需联网**）；镜像 tag 策略（固定 digest 说明可选）。

---

## 5. 配置与前端契约

- 构建期或运行时注入：**API、WS、下载** 的 **相对路径**（推荐）或单一 **`VITE_PUBLIC_APP_ORIGIN`**，禁止使用散落硬编码的 `localhost:8001`。
- **`download_server` CORS**：允许 origin 与桌面 WebView 实际访问的 origin 一致（如 `http://127.0.0.1:<port>`）。
- **密钥与加密**：`VITE_ENCRYPTION_KEY` 等待生产/桌面一致策略；桌面版不得在仓库提交真实密钥。

---

## 6. 数据卷与路径

- **持久化**：MySQL 数据目录、上传目录、结果目录（如 `download_data`）、日志目录；compose 使用命名卷或用户目录下绑定挂载。
- **`code/`**：开发时路径为 `/xp/www/AutoMATA/code`；容器内应通过 **env**（如 `AUTOMATA_CODE_ROOT`）统一，与挂载宿主机目录一致。

---

## 7. 风险与依赖

- **后端路径硬编码**（`/xp/www/AutoMATA/...`、`/opt/anaconda/...`）：实现阶段需 **收敛为可配置路径** 或容器内约定布局，否则桌面镜像无法稳定复用。
- **大镜像体积**：首次 pull 耗时长；需在安装说明中明示，并可选镜像压缩或分层优化。
- **Linux 发行版差异**：权限、SELinux、Docker socket 路径；需在用戶文档列出测试过的发行版。

---

## 8. 测试建议

- **矩阵**：Windows 11 + Docker Desktop；至少一种主流桌面 Linux + Docker Engine。
- **用例**：冷启动 pull → 健康检查通过 → 登录（若启用）→ 触发依赖 **R/`code/`** 的最小任务 → 经 **同源下载** 拉取结果。
- **弱网/断网**：断网后仅验证**已拉镜像**场景下业务仍可用（不要求断网下首次安装）。

---

## 9. 与「完全离线 tar」方案的关系

- 本方案 **不包含** 安装介质内的镜像 tar；**首次安装必须能访问注册表**。
- 同一 compose 文件与镜像 tag 可被离线方案 **复用**（离线方案改为 `docker load` 预置 tar）。

---

## 10. 开放问题（记录待决策）

- Electron vs Tauri（打包体积、团队栈、CI）。
- 退出 GUI 时默认 `stop` 还是 `down`、是否保留匿名卷。
- 自动更新通道（仅手动按钮 vs 启动时检查）。
