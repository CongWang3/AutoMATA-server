# Analyze and Train（analysis_train / analysis_train_2）迁移至 Vue + FastAPI

日期：2026-03-28  
状态：已评审（用户确认方案）  
范围：将 `analysis_train.php` + `analysis_train_2.php` 的「数据处理 + 监督模型训练 + 差异表达/可视化分析」迁移为与现有 **监督学习 / 数据分析** 一致的 Vue + FastAPI 实现。

## 1. 背景与目标

### 1.1 旧版行为摘要

- **`analysis_train.php`**：单页表单，`multipart/form-data` 提交至 `analysis_train_2.php`。字段包括：
  - 数据类型（Read counts / FPKM）、基因命名（Symbol / Ensembl / Gene ID）
  - 数据策略：三文件上传 / 单文件按比例划分 / K 折 + 独立测试集
  - **样本信息文件**（与表达/训练数据样本顺序一致）
  - 监督模型（CNN…RBFN；PHP 中 “All” 选项已注释）
  - 训练超参：epoch、lr、early stopping、batch、label 数、loss、optimizer、seed
  - 物种、log2(FC)、padj、多重检验校正
  - Email（前端校验为必填）
- **`analysis_train_2.php`**：同步长流程：创建 `download_data/Jobs/<jobId>/`、落盘文件、（旧）写 MySQL `joblist`、调用 `code/train_model/<model>.py`、再执行 R（ID 转换、DESeq2/limma 等）、打包下载、PHPMailer 发邮件，并输出带 Running 动图的结果页。

### 1.2 迁移目标

- **任务模型**：完全以现有 FastAPI **`jobs` 表** + **`/api/v1/jobs`** 为准，与当前 Vue+FastAPI 功能一致；**不再使用** MySQL `joblist`。
- **后端风格**：与 `training_service`、`analysis_service`、`model_use` 一致：创建 `Job`、异步后台执行、更新 `status/progress/current_step`、WebSocket 推送（若现有链路已接）、**可交付结果后再置 Completed**（参考 `model_use` 的 zip 原子写入策略）。
- **前端样式**：与 **`Supervised.vue`** 同套布局与组件习惯（`automata-training-supervised`、`el-card`、分步标题、原生 `form-control` 上传区等）。
- **训练参数**：在 PHP 未传的 **Regularization method / weight、Dropout、Feature selection** 与监督页对齐；按 **模型能力** 禁用/隐藏（与 `Supervised.vue` / `train_model` 脚本一致，如 SOM 隐藏正则与 Dropout）。
- **结果弹窗**：
  - **等待/失败**：与现有 **训练结果弹窗**（`TrainingResultPanel`）一致：参数表 + Running 行（Processing 用 GIF，Submitted 用文字）。
  - **完成态**：在「参数表 + 最终结果 Download」基础上，**图片预览与多格式下载逻辑对齐现有数据分析弹窗**（`AnalysisResultPanel`：存在 PNG 等则预览；Download Figure 下拉多格式等，按分析产物实际文件扩展名启用/禁用）。

## 2. 方案选择（已确认）

采用 **单一 Job、专用 API**（原 brainstorm **方案 1**）：

- 用户一次提交 → 一个 `job_id` → 一个弹窗生命周期。
- 后台 **顺序** 执行：文件就绪 → Python 训练 → R 分析流水线 → 打包可交付 zip → 更新 Job 为 Completed → 可选邮件。

**不采用**：拆成两个 Job（训练 + 分析）或仅 shell 黑盒无进度（除非后续优化）。

## 3. 任务类型与枚举

建议在 `JobType` 中新增专用枚举值，便于列表筛选、权限与统计，且与纯 `MODEL_TRAIN`、纯 `DATA_ANALYSIS` 区分：

- 推荐：`ANALYSIS_TRAIN = "analysis_train"`（显示名：**分析训练** 或 **Analyze and Train**）。

实现注意：

- SQLAlchemy `Enum(JobType)` 扩展需 **数据库迁移**（或项目既有 enum 扩展流程），并在 `jobs` 相关 schema、前端 `JobType` 过滤（若有）中注册。

**备选**（不推荐）：沿用 `JobType.DATA_ANALYSIS` 或 `MODEL_TRAIN`，在 `input_params.pipeline = "analysis_train"` 区分——会增加查询与展示歧义。

## 4. 后端设计

### 4.1 路由与入口

- 新增 `backend/api/routers/analysis_train.py`（名称可微调），在 `main.py` 中 `include_router`。
- `POST /api/v1/analysis-train`（路径以项目 REST 惯例为准）：接收 JSON body（文件已通过通用上传接口得到 `file_id` / `file_path`），或 `multipart` 与现有训练页二选一；**推荐与监督学习一致**：先 `POST /api/v1/files/upload`，再在 body 中传文件 ID 与标量参数，便于校验与去重。

### 4.2 请求体（`input_params` 建议结构）

与监督训练对齐的嵌套 + 分析专用顶层字段，示例（实现时可微调键名，但需在 spec 与前端锁定）：

```json
{
  "training_type": "analysis_train",
  "model_type": "cnn",
  "parameters": {
    "strategy": "split|upload|kfold",
    "split_ratio": { "train": 8, "validation": 1, "test": 1 },
    "kfold": 3,
    "epochs": 20,
    "learning_rate": 0.001,
    "early_stopping": 10,
    "batch_size": 32,
    "label_count": 2,
    "loss_function": "crossentropy",
    "optimizer_function": "adam",
    "seed": 42,
    "r_method": null,
    "r_weight": 0.0,
    "dropout_rate": 0.0,
    "feature_method": null,
    "train_dataset_file_id": "...",
    "validation_dataset_file_id": "...",
    "test_dataset_file_id": "...",
    "kfold_train_dataset_file_id": "...",
    "kfold_test_dataset_file_id": "..."
  },
  "data_type": "read_counts|fpkm",
  "gene_nomenclature": "symbol|ensembl|gene_id",
  "organism": "Homo_sapiens|...",
  "fc_threshold": 1.0,
  "padj_threshold": 0.05,
  "correction": "BH",
  "sample_info_file_id": "...",
  "email": "optional@example.com"
}
```

#### 4.2.1 数据格式适配（原则，非「必须与 PHP 逐行一致」）

**目标**：用户上传的表达矩阵与分组信息，在形态上往往**不能同时**直接满足「监督训练脚本」与「DESeq2 / limma 等 R 流水线」的输入约定。实现上应优先解决 **格式适配问题**，而不是机械复刻 `analysis_train_2.php` 的每一步。

- **训练阶段**：使用「样本 × 特征 + Label」朝向的矩阵（与当前监督学习一致）；**不在训练前**对用户整表做与 PHP 历史实现相同的盲目转置。
- **差异分析阶段**：R 脚本（如 `DESeq2_read_count.R`）期望的是其文档与实现中所假设的矩阵朝向与列结构；若与训练阶段落盘文件不一致，应在编排层通过**明确的、可测试的转换步骤**（复制、派生中间文件、必要时转置/删列等）生成 R 可读文件，而不是隐含依赖「与某段 PHP 完全一致」。
- **split 策略**：仍需在训练完成后为分析阶段恢复「未切分前的完整表达矩阵」等业务语义；具体实现可以是 **PHP 式的 copy + 训练后 rename**，也可以是等价且更清晰的「保留 origin 快照 + 训练只用 split 视图」等方案，**以正确性与可维护性为准**。
- **与旧 R 脚本的边界**：在不大改 `code/*.R` 的前提下，**落盘文件名与路径**（如 `{job_id}_data.txt`、`_info.txt`、`result/` 下产物）宜与现网约定对齐，作为 **集成契约**；矩阵如何从「训练态」变为「分析态」应在服务层用函数与单测说明，**允许**在验证等价或更优后替换掉 PHP 时代的具体写法（例如用显式「导出分析用矩阵」步骤代替难以阅读的转置+删行组合）。

**小结**：Spec 要求的是 **两端输入合法、中间语义正确**，而非「必须与 `analysis_train_2.php` 行为逐字节一致」。若存在更简单、可测试、且同时适配训练+R 的方案，应采用更好方案，并在实现与测试中写清数据流。

### 4.3 执行编排（后台任务）

新建 `analysis_train_service.py`（或等价模块），职责：

1. **创建目录** `download_data/Jobs/<job_id>/` 与 `result/`（与 PHP 一致）。
2. **从上传存储复制/链接** 到标准文件名（与 `training_service` 拷贝逻辑风格一致）。
3. **更新** `Job.status = Processing`，`current_step` 分阶段文案（如「模型训练中」「差异分析中」）。
4. **Python 训练**：`subprocess` 调用 `code/train_model/<model>.py`，CLI 参数与 **`training_service` 白名单/映射** 一致，并传入 `r_method`、`dropout_rate`、`feature_method` 等（与监督学习相同默认值与 null 语义）。
5. **R 流水线**：按 **ID 转换（若需）→ 生成 R 所需的表达矩阵与分组文件 → DESeq2/limma** 等依赖顺序组织 Rscript 调用，抽成可维护层（Python 内函数列表或独立脚本）；环境路径（如 `Rscript`、`code/*.R`）配置化，与现网 conda 路径对齐或可配置。调用顺序以 **R 脚本输入契约** 为准，不必与旧 PHP 文件中的行序一一对应。
6. **失败处理**：任一阶段非零退出 → `Job.status = Failed`，`error_message` 附日志尾部或明确原因；**不在**结果 zip 未就绪时标记 Completed。
7. **成功打包**：对最终结果目录打 zip（`.tmp` → 校验 → `replace` 原子改名，对齐 `model_use`）；设置 `result_file` 后再 `Completed`。
8. **邮件**：成功且可下载后调用 `email_service.send_result_email`（`analysis_type` 文案标明 Analyze and Train）。

### 4.4 与现有服务的关系

- **不重写** `training_service` 的核心训练函数亦可：可在 `analysis_train_service` 内 **复用** 构建命令行与落盘的辅助函数（若需抽取公共模块，小步重构，避免大范围改动）。
- **分析结果列表**：若数据分析依赖 `AnalysisAPI.getResult` 式接口，需约定本 Job 类型如何暴露 **result_files**（或在 zip 外同步写一份 manifest 到 `output_params`）；**完成态弹窗图片预览**需要对前端提供与数据分析一致的 **按文件名/格式的文件 URL**（见第 5.3 节）。

## 5. 前端设计

### 5.1 页面与路由

- 新视图：`AnalyzeTrain.vue`（或 `AnalysisTrain.vue`），路由注册在现有「模型训练/分析」菜单下。
- 结构：**步骤 1** 数据类型与基因命名 → **步骤 2** 策略与上传（与监督页三种策略 UI 对齐）→ **步骤 3** 样本信息文件 → **步骤 4** 模型选择 → **步骤 5** 超参（含正则/Dropout/特征选择，逻辑复制自 `Supervised.vue` 的 `modelExtraCaps`）→ **步骤 6** 物种与差异阈值与校正 → **步骤 7** 通知邮箱（可选时与 PHP 行为脱钩：产品可改为「选填」并校验格式）。

### 5.2 API 客户端

- `automata-web/src/api/analysisTrain.ts`：`submit(payload)`、`getStatus`（若未统一走 `jobsApi` 则仅保留创建；状态以 `jobsApi.getJobDetail` + WS 为准）。

### 5.3 结果弹窗（用户确认：与数据分析逻辑对齐）

**等待 / 失败**：使用 `TrainingResultPanel`（与监督训练一致），`input_params` 来自 `jobsApi.getJobDetail`，并用 **提交快照** 兜底等待阶段空 `input_params`（与现有训练页模式一致）。Email 在等待态是否隐藏遵循当前产品规则。

**完成态**：

- **参数区**：同上（或合并为单一面板组件，避免维护两套表格样式）。
- **结果区**：行为对齐 **`AnalysisResultPanel` 完成态**：
  - 若结果中存在 **PNG 预览图**（及项目已支持的 pdf/svg 等），展示预览与 **Download Figure** 下拉；
  - 若存在 **综合分析式** 多图（volcano/cluster 等），按 `AnalysisResultPanel` 的分支逻辑扩展或抽 **可复用子组件**（例如传入 `resultFiles: { filename, format, url }[]`）。
- **整包下载**：保留与训练一致的 **`jobsApi.getDownloadUrl(job_id)`** 主结果 zip（可在表格最后一行「Data Training Result」或并列「Download package」——具体文案在实现时与 UI 统一）。

若后端暂不能像 `AnalysisAPI.getResult` 一样返回 `result_files` 列表，则 **实现阶段** 必须在 `analysis_train` 完成时写入与数据分析兼容的 **结果清单**（或扩展 `GET /v1/jobs/{id}` 返回解析后的文件列表），否则前端无法复用预览逻辑。

## 6. 测试与验收

- **单元/集成**：创建 Job → 模拟小数据集 → 断言状态流转、**Completed 仅在有 zip 后出现**、`input_params` 持久化正确。
- **手工**：三种数据策略各跑一遍；Symbol / 非 Symbol 各一遍；至少一个模型 + 一种数据类型；验证邮件与下载链接；完成态 **PNG 预览** 与多格式下载与数据分析页一致。

## 7. 明确不在本期范围（除非另行开需求）

- PHP 表单中已注释的 **All 模型并行** 训练（`analysis_train_2.php` 中 `modelType === "all"` 分支）：默认不实现；若需恢复，单独开任务扩展编排与前端选项。
- 旧 **`joblist` MySQL** 的任何读写。

## 8. 用户确认记录

- 任务存储：**仅** FastAPI `Job` + `/api/v1/jobs`，与现有 Vue+FastAPI 功能一致。
- 架构：**方案 1**（单一 Job、专用接口、顺序执行训练 + R）。
- 完成态 UI：**与现有数据分析弹窗的图片预览与下载逻辑对齐**。

---

下一步：按项目流程编写 **实现计划**（`writing-plans`），再分任务实现后端枚举/迁移、router、service、前端页面与结果弹窗组合。
