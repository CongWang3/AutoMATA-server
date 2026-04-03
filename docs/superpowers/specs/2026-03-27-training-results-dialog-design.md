# 训练/模型应用结果弹窗统一设计（对齐数据分析弹窗）

日期：2026-03-27  
范围：监督学习 / 无监督学习 / 半监督学习 / 模型应用（ModelUse）  
目标：四个模块的“结果弹窗”样式与交互 **统一为数据分析弹窗同款**，并实现“等待 → 结果”的双阶段界面。

## 背景与问题

当前训练与模型应用弹窗使用了不同的结果呈现方式（含 JobStatus 卡片、按钮布局等），与数据分析弹窗的“灰底表格 + 居中”视觉不一致；同时用户期望在任务执行期间先展示 Waiting 界面，任务结束后自动切换 Result 界面，并在表格最后一行提供最终结果文件下载按钮（走独立下载服务）。

## 设计目标（验收标准）

### 统一样式

- 弹窗内容为一个表格，整体风格对齐数据分析弹窗（参考 `AnalysisResultPanel.vue`）：
  - **灰色背景**
  - **字体/单元格内容居中显示**
  - **斑马纹行样式（stripe）**

### 统一交互：Waiting → Result

#### Waiting（Submitted / Processing）

- 顶部提示文案：`Trainings is in progress, please wait`（带颜色，风格与数据分析等待界面一致）
- 表格最后一行（**严格对齐数据分析等待界面**）：
  - 左侧：`Running`
  - 右侧：
    - 当 `status = Processing`：显示 gif（复用数据分析同款）：`/images/progress_bar_new.gif`
    - 当 `status = Submitted`：显示文字 `Submitted`（不显示 gif）

#### Result（Completed）

- 表格展示 JobID 与用户提交的参数（见“参数展示规则”）
- 表格最后一行固定为最终结果文件下载：
  - 左侧单元格：`Data Training Result`
  - 右侧单元格：`Download` 按钮
  - 点击按钮：走独立下载服务签名链接下载最终结果文件（与训练下载链路一致，即 `jobsApi.getDownloadUrl(job_id)` → `window.open(download_url, '_blank')`）

#### Failed（Failed）

- 仍使用同款表格展示 JobID 与参数
- 最后一行展示失败信息（与数据分析失败界面一致的呈现方式即可）

## 参数展示规则（关键）

### 固定行顺序（用户选择：A）

Waiting 与 Result 两个界面均按固定顺序展示（存在才显示）：

1. JobID（必有）
2. Task/Model Type（必有：训练为 training_type+model_type；模型应用为 model_type）
3. 其余参数按 **训练表单顺序**展示（仅当用户实际提交/有效时展示）
4. Waiting：最后一行为 Running + gif
5. Result：最后一行为 Data Training Result + Download 按钮

### “只显示有的参数”

- 仅显示用户提交且对当前模型有效的参数行：
  - 例如 SOM 不支持 `Regularization method / weight / Dropout`，则这些行不出现
  - 例如用户未填写 email，不显示 email 行

### 参数来源（统一）

- 统一从后端 `jobs` 详情接口返回的 `input_params`（JSON）中提取展示（即 `jobsApi.getJobDetail(job_id).input_params`）
  - 训练模块：`input_params.parameters`（以及 `training_type/model_type/task_name/dataset_path`）
  - 模型应用：`input_params` 中 `model_type/test_data_path`、模型文件路径等（以及可选 email）
- 说明：弹窗展示数据不再仅依赖页面内“本地 currentJob 对象”，必须以 `UnifiedJob` 的 `input_params` 为准，才能稳定实现“只显示有的参数 + 固定顺序”。

## 下载按钮行为（统一）

- 统一通过 `jobsApi.getDownloadUrl(job_id)` 获取下载链接
- 前端以新窗口打开下载链接（`window.open(url, '_blank')`）
- 不依赖前端持有 `result_file` 的绝对路径，避免环境差异

## 动作按钮（取消/重试）

- 本次变更 **不保留 Cancel / Retry / View-result** 等操作按钮（用户确认：不需要保留）。
- 弹窗仅负责展示 Waiting/Result/Failed 三态表格，以及 Completed 时的下载按钮。

## 组件与代码改造建议（推荐实现方式）

### 方案：抽复用组件 `TrainingResultPanel.vue`

在 `automata-web/src/components/` 新增可复用组件：

- Props（建议）：
  - `jobId: string`
  - `status: string`
  - `inputParams: Record<string, any>`（已解析的 input_params）
  - `errorMessage?: string`
  - `onDownload: () => Promise<void>` 或传入 `getDownloadUrl` 方法
- 内部根据 `status` 渲染 Waiting/Result/Failed 三态，并输出同款表格
- 由四个页面的 `el-dialog` 直接引用该组件，替换当前 `JobStatus` 卡片式展示

## 参数字段映射（最小可落地）

> 目标：固定顺序 A + “只显示有的参数”。实现时使用映射表生成 `param_rows`，再按顺序渲染。

### 通用展示规则

- **空值不展示**：`null/undefined/''` 不展示
- **数值 0 是否展示**：
  - 训练超参数中 `dropout_rate=0`、`r_weight=0` 视为“未启用”，不展示
  - 其他数值（如 `epochs=0` 理论上不会出现）按“空值不展示”处理
- **路径字段展示 basename**：如 `.../uploaded_files/xxx.pth` 在表格里显示为 `xxx.pth`

### 训练任务（supervised / unsupervised / semi_supervised）

固定顺序建议（存在才显示）：

1. `task_name` → Task Name
2. `training_type` → Training Type
3. `model_type` → Model Type
4. `dataset_path` → Dataset
5. `parameters.strategy` → Strategy
6. `parameters.ratio` → Split Ratio
7. `parameters.kfold` → K-Fold
8. `parameters.epochs` → Epoch
9. `parameters.lr` 或 `parameters.learning_rate` → Learning Rate
10. `parameters.es` 或 `parameters.early_stopping_patience` → Early Stopping Patience
11. `parameters.bs` 或 `parameters.batch_size` → Batch Size
12. `parameters.random_seed` → Random Seed
13. `parameters.loss_function` → Loss Function
14. `parameters.optimizer_function` → Optimizer
15. `parameters.output_size` 或 `parameters.labels` → Output Size
16. `parameters.feature_method` → Feature Selection Method
17. `parameters.r_method` → Regularization Method
18. `parameters.r_weight` → Regularization Weight/Strength
19. `parameters.dropout_rate` → Dropout Rate
20. `parameters.email`（如存在）→ Email

备注：
- SOM：若 `model_type=som`，则 17-19 不展示（即使 parameters 中出现也过滤掉）

### 模型应用（ModelUse）

固定顺序建议（存在才显示）：

1. `model_type` → Model Type
2. `test_data_path` → Test Dataset
3. `model_path` → Model File
4. `som_model_path` → SOM Model File
5. `encoder_path` → Encoder Model File
6. `classifier_path` → Classifier Model File
7. `scaler_path` → Scaler File
8. `un_semi_model_path` → Model File
9. `email`（如存在）→ Email

备注：
- SOM 仅展示 `som_model_path`（不展示 winmap 字段）

### 需要改动的页面

- `automata-web/src/views/ModelTrain/Supervised.vue`
- `automata-web/src/views/ModelTrain/Unsupervised.vue`
- `automata-web/src/views/ModelTrain/SemiSupervised.vue`
- `automata-web/src/views/ModelUse/ModelUse.vue`

四个页面的弹窗结构保持一致：

- 弹窗打开时先显示 Waiting 版表格
- 轮询/WS 更新状态为 Completed 后自动切换到 Result 版表格
- Download 按钮永远位于表格最后一行的右单元格

## 风险与注意事项

- 参数展示需要做映射与过滤（尤其是不同模块参数名不同），必须保证：
  - **未提交/不支持的参数不显示**
  - 行顺序稳定（固定顺序 A）
- 下载按钮不应在 Waiting 阶段出现（仅 Completed 且可下载时出现）

