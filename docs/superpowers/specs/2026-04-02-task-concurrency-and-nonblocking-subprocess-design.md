# 任务并发限制与非阻塞子进程执行（路径A）设计

日期：2026-04-02  
范围：模型训练（Supervised/Unsupervised/Semi-supervised）、数据处理（Genome/Transcriptome/Integration/Protein 等）、数据分析（Analysis 模块）  
目标：在同一 FastAPI 服务内，避免长时间同步子进程阻塞事件循环；同时对三类任务分别限制并发上限为 2，并保持“排队仍显示 Submitted”。

## 背景与问题陈述

当前系统中，训练任务与数据处理/分析任务都使用 `asyncio.create_task(...)` 启动后台协程；但后台协程内部存在同步阻塞调用（典型为 `subprocess.run(...)`）。

当某个后台协程在事件循环线程中执行 `subprocess.run(...)` 并持续数百秒时：

- FastAPI 的事件循环会被同步阻塞，导致其它已创建的 asyncio 任务无法得到调度。
- 现象表现为：训练期间新提交的数据处理/分析任务长期停留在 “Processing/Submitted” 的表象状态，直到训练子进程结束后才真正开始执行。
- WebSocket 推送也可能出现整体延迟（因为推送同样需要事件循环调度）。

该问题属于“并发语义错误”（event loop starvation），不是单纯性能不足。

## 目标与非目标

### 目标

- **G1**：训练期间提交的新任务应能立即进入排队/执行流程，不再被训练的同步子进程卡死。
- **G2**：分别限制三类任务的并发上限（每类最多 2 个同时执行）：
  - 训练：≤ 2
  - 数据处理：≤ 2
  - 数据分析：≤ 2
- **G3**：排队时 **前端仍显示 `Submitted`**（不新增状态枚举）；通过 `current_step`/message 表达“排队中”。
- **G4**：避免任务状态错乱（例如已 Completed 的任务被晚到的更新覆盖回 Processing）。

### 非目标（本次不做）

- **NG1**：不引入 Celery/RQ/Redis 等外部任务队列系统。
- **NG2**：不实现“强取消”（杀掉正在运行的训练/R 子进程及其子进程组）。可以保留现有取消语义或仅做软取消标记。
- **NG3**：不做跨多进程 worker 的“全局严格并发限制”。本设计的并发限制在单进程内严格成立；多 worker 部署时，每个进程各自生效。

## 方案选择：路径A（最小改动 + 可控风险）

采用“路径A”：

- 将所有 `subprocess.run(...)` 从事件循环线程中挪走，改为 `await asyncio.to_thread(subprocess.run, ...)` 执行。
- 在真正启动外部脚本前，使用每类一个 `asyncio.Semaphore(2)` 进行并发限制。
- 排队时不标记 Processing，保持 Submitted，并在 `current_step` 中标明排队中。

该方案的核心特点是“**不改变脚本本身、不改变参数传递、不重写日志收集**”，只改变阻塞等待发生的位置，因此更适合论文/演示场景的低风险修复。

## 设计细节

### 1) 统一的外部命令执行 helper（非阻塞）

设计一个统一 helper（放在后端公共模块中，例如 `api/utils/subprocess_utils.py`）：

- 输入：`cmd`, `cwd`, `timeout`, `stdout/stderr` 选项等
- 行为：在后台线程中执行 `subprocess.run`，并将 `CompletedProcess` 结果返回到协程上下文
- 约束：**线程中仅执行子进程调用**；数据库会话、WebSocket 推送、Job 状态更新仍在协程/主线程执行，避免 SQLAlchemy session 的线程安全风险。

### 2) 三类任务各自限流（每类 2）

引入三个全局并发信号量（建议放在服务层模块的单例区域或专门的 `api/services/concurrency.py`）：

- `TRAINING_SEM = asyncio.Semaphore(2)`
- `DATA_PROCESS_SEM = asyncio.Semaphore(2)`
- `ANALYSIS_SEM = asyncio.Semaphore(2)`

限流点选择原则：

- **只包裹外部脚本的执行阶段**（例如训练脚本/`Rscript`/分析脚本），而非整个任务生命周期。
- 这样排队等待不会占用名额，且数据库准备/文件拷贝等轻量步骤可并行执行。

### 3) 排队状态语义（Submitted + current_step）

排队等待 semaphore 时：

- Job `status` 保持 `Submitted`
- `current_step` 更新为：`排队中（等待资源）`（英文可选：`Queued (waiting for resources)`）
- 可选：通过 WebSocket 推送一次 message，仍使用 `Submitted`/不改变 status，仅提示用户进入队列。

拿到 semaphore、即将启动外部脚本前：

- Job `status` 更新为 `Processing`
- `current_step` 更新为具体步骤（例如：`执行 xxx 模型训练` / `开始处理基因组数据` / `开始分析 ...`）
- 通过 WebSocket 推送 `Processing` 更新

### 4) 终态保护（防止状态回滚）

为避免 WS/后台任务的晚到更新覆盖终态：

- 设定终态集合：`Completed/Failed/Cancelled`
- 在每次写入 Job 状态前检查：
  - 若当前数据库状态已为终态，则忽略任何“非终态”的后续更新（例如 Processing、progress 更新）。

该保护适用于三类模块的所有状态写入点。

### 5) 与多 worker 部署的关系

本设计在**单进程** FastAPI/uvicorn 实例内提供严格限流（每类 2）。

若后端以多进程 worker 部署：

- 每个进程各有一套 semaphore
- 全局并发可能上升为：`workers * 2`

论文/演示场景通常可接受；若未来需要“全局严格 2/2/2”，应升级为 DB/Redis 锁或任务队列方案（不在本设计范围）。

## 影响范围（代码触点）

需要覆盖所有同步子进程调用点：

- 训练模块：`api/services/training_service.py` 内监督/无监督/半监督训练脚本调用
- 数据处理模块：`api/services/data_process_service.py` 内 Genome/Transcriptome/Integration 等 `Rscript` 调用
- 分析模块：`api/services/analysis_service.py`、`api/services/analysis_train_service.py` 等涉及 `subprocess.run` 的调用点

## 测试与验证（手工/自动）

### 最小验证用例（推荐手工复现）

1. 用户 A 提交训练任务（脚本运行数分钟）。
2. 训练任务仍在运行时，用户 B 提交 Genome 数据处理任务。
3. 期望：
   - Genome 任务能立刻进入“排队中（等待资源）”或直接开始执行（取决于同类并发占用）
   - 不再出现“必须等训练结束后几百毫秒才开始”的现象
   - WebSocket 推送不因训练而整体延迟

### 并发限制验证

- 同时提交 3 个训练任务：应有 2 个进入 Processing，1 个保持 Submitted + `current_step=排队中...`
- 同时提交 3 个数据处理任务：同理
- 同时提交 3 个分析任务：同理

## 风险与缓解

- **R1：线程中误用 DB session** → 通过代码约束：线程 helper 仅做 `subprocess.run`，DB 更新留在协程
- **R2：多 worker 下并发限制扩大** → 文档明确 + 部署建议（论文场景可单 worker）
- **R3：排队期间用户误以为卡住** → `current_step` 明确显示排队中，并可选推送 message

