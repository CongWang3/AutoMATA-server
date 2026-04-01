# 桌面版（乙）：完全离线安装（随包镜像 tar）方案

日期：2026-04-01  
状态：草案（待产品决策）  
范围：用户本机 **Docker** 运行全套 AutoMATA，任务在用户电脑执行；**首次安装不依赖访问公网镜像仓库**，通过安装包或离线介质内的 **`docker load` 预置镜像**。目标平台：**Windows、Linux**，容器平台 **`linux/amd64` 单架构**（x86-64 PC）。

## 1. 背景与目标

### 1.1 适用场景

- 内网机房、涉密环境、或严格禁止安装期出网的终端。
- 与 **联网 pull 方案** 共享同一套 **compose 拓扑、镜像内容、前端同源反代** 设计；差异仅在 **镜像如何到达用户磁盘**。

### 1.2 成功标准（本方案）

- 用户在 **无互联网**（或无法访问 GHCR/私服）条件下，完成安装后仍能 **`docker compose up`** 并达到与联网方案一致的健康检查与会话体验。
- **架构仍为 `linux/amd64`**：一套 tar 集，在 Win（Docker Desktop）与 Linux（Docker Engine）上均可 `docker load`（Linux 容器层）。

---

## 2. 架构概要

与《2026-04-01-desktop-docker-online-pull-design.md》**第 2 节栈拓扑相同**：桌面壳 + MySQL + Redis + 胖 backend + download + nginx 前端；下载经 nginx 同源暴露。

**额外组件：离线介质**

- 一个或多个 **`docker save` 生成的 `.tar`（或分卷压缩包）**，在安装脚本中按顺序 `docker load -i ...`。
- 安装程序（Inno Setup / NSIS / shell 脚本 + tar.xz 等）负责：释放 compose 文件、环境模板、**加载镜像**、创建数据目录、可选创建桌面快捷方式。

---

## 3. 镜像清单与打包流程

### 3.1 需纳入 tar 的镜像

与联网方案 **相同 tag、相同 Dockerfile 产出**；典型包括：

- `mysql:8.x`（或固定 digest 的小版本）
- `redis:7.x`
- 桌面 **backend**（含 R、`code` 挂载或内置）
- 桌面 **download**（若与 backend 拆分为两镜像）
- **frontend/nginx**

**构建侧**：CI 在发布「离线包版本」时执行：

1. `docker pull` 或本地 `docker build` 得到所有依赖镜像；
2. `docker save -o automata-desktop-<version>-amd64.tar` **可多镜像一单包** 或 **分镜像多个 tar**（分文件利于分包 DVD/U 盘）。

### 3.2 版本锁定

- 离线包版本号与 **镜像 digest 列表**（或 save 时的 manifest）写入 `VERSION` 或安装日志，便于支持与审计。
- **不与「最新」漂移**：离线包用户仅通过 **新离线包** 升级，而非运行时 pull。

---

## 4. 安装程序职责

1. 检测/提示安装 **Docker**（若未安装；完全离线时通常要求介质内附带 Docker 安装包或企业预装，**此点需在交付约定中明确**）。
2. 解压到用户选定目录：`compose.yml`、`desktop.env.example`、`load-images.sh` / `load-images.ps1` 等。
3. **顺序执行 `docker load`**（若多 tar，顺序可任意，但需全部成功）。
4. 初始化数据目录与 `.env`（密码、端口占位符）；**首启前**可选运行一次性 DB 迁移/初始化容器。
5. 启动逻辑可委托 **桌面壳**（与联网版同一壳），仅跳过 `pull` 步骤；或安装结束时执行一次 `docker compose up -d`。

---

## 5. 主要代价与缓解

| 代价 | 说明 | 缓解 |
|------|------|------|
| **安装包体积大** | 含 R 的胖镜像 + MySQL 基础层，常达数 GB | 分卷下载；仅企业客户发离线 ISO；高压缩打包 |
| **仅 amd64** | 与你方「不做 arm64」一致 | 单 tar 集简化 |
| **升级路径** | 用户需获取新离线包并重新 load | 发布说明「差量包」可选（高级）；默认整包替换 |
| **Docker 本身离线安装** | Win/Linux Docker 安装仍需介质 | 与 AutoMATA 离线包 **捆绑** 或由甲方镜像站提供 |

---

## 6. 合规与安全

- 捆绑分发的镜像层包含上游基础镜像与 R CRAN 等许可证，需在 **`docs/` 或安装目录附带 NOTICE/第三方清单**。
- 不在 tar 中嵌入生产密钥；桌面 `.env` 由用户或安装向导生成。

---

## 7. 测试建议

- **无网虚拟机**：断网网卡 → 仅执行 load + compose up → 跑通与联网方案相同的 **最小 R/`code/`** 闭环。
- **安装包校验**：load 后 `docker compose config` 与镜像 ID 与发布清单一致。

---

## 8. 与联网 pull 方案的关系

- **compose、nginx 路由、胖后端定义、前端环境变量契约** 应与联网方案 **共用同一套基准文档**，避免两条产品线分叉。
- 联网版首次：pull；离线版首次：load。桌面壳中可用 **标志位或检测本地是否已有镜像** 决定分支（实现阶段细节）。

---

## 9. 开放问题（记录待决策）

- 离线包是否 **附带 Docker Desktop / Engine 安装包**（体积与许可证）。
- 单个大 tar  vs  按镜像拆分 tar（更新小包时的策略，若未来做「增量离线补丁」）。
- Windows 安装器技术选型（Inno Setup、WiX 等）与 Linux 是否仅提供 `tar.gz + install.sh`。
