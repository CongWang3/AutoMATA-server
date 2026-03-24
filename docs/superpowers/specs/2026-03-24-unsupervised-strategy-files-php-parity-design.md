# 无监督训练：策略与文件落盘对齐 PHP 设计

## 背景与目标

- 参考：`modelTrainPage_un.php`、`modelTrain_un.php`（与监督页同一套 **upload / split / kfold** 策略语义）。
- 目标：**仅**要求「选择策略 + 上传文件」的前后端行为与 PHP 一致（含 Jobs 目录下 `{jobID}_data.txt` / `_val.txt` / `_test.txt` 的落盘规则）；**不要求**损失函数、优化器下拉与 PHP 选项完全一致，可继续使用当前 Vue 较长列表，只要传入脚本的值被 `VAE.py` / `deepcluster.py` 接受即可。
- 非目标：重做无监督结果页、邮件、zip 等已有 FastAPI 链路（除非与落盘冲突）。

## 实施范围（与用户约定对齐）

- **主修改面**：`automata-web/src/views/ModelTrain/Unsupervised.vue` + 无监督任务对应后端（主要为 `backend/api/services/training_service.py` 中 `_execute_training` 数据集落盘段，及必要时 `create_unsupervised_task` 的校验与 `parameters` 透传）。
- **重要依赖（现状）**：无监督页通过 `BaseTrainingForm` 渲染策略上传区。当前组件内 **`handleTrainSelected` / `handleValidationSelected` / `handleKfoldSelected` 仅打日志**，未调用上传接口，也未把各文件的 **数据库 `id`** 放进 `submit` 载荷；`split` 用的 `handleDatasetSelected` 与测试集用的 `handleTestSelected` 才会上传并记录路径。因此：**只改 `Unsupervised.vue` 与后端无法完成 `upload` / `kfold` 的多文件 ID 传递**，除非二选一：
  1. **推荐**：对 `BaseTrainingForm.vue` 做**最小**补齐——与 `handleDatasetSelected`、`handleTestSelected` 同模式：`trainingApi.uploadFile`（或 `FileUploader` 的 `upload-complete` 解析出 `id`）写入 ref，在 `onSubmit` 时合并进 `submit`（字段名与监督一致：`train_dataset_file_id` 等，或统一用 `file_path` + 后端解析，但以前者与现后端分支一致为佳）。
  2. **备选**：仅在 `Unsupervised.vue` 内复制监督页式上传与 ID 收集逻辑，弱化或绕过 `BaseTrainingForm` 的策略区——**不增新文件**，但重复代码多、维护成本高，**非首选**。

以下「影响文件」在坚持「仅 Unsupervised + 后端」时，将 **(1)** 记为**允许的最小共享组件补丁**。

## PHP 行为摘要（契约）

| `strategy` | 上传 | 落盘文件 | `ratio` / `k_folds`（脚本侧） |
|------------|------|----------|-------------------------------|
| `upload` | 训练、验证、测试各 1 | `_data.txt`, `_val.txt`, `_test.txt` | `ratio=0`, `kfold=0` |
| `split` | 单一数据集 | 仅 `_data.txt` | `ratio` = 表单比例字符串；`kfold=0` |
| `kfold` | 训练集 + 测试集 + K | `_data.txt`, `_test.txt`（无 `_val.txt`） | `ratio=0`；`k_folds` = K |

## 方案对比

### 方案 A（推荐）：后端 `_execute_training` 按 `training_type` + `strategy` 分支落盘（与监督同源风格）

- **做法**：在 `TrainingService._execute_training` 中，对 `unsupervised`（及必要时 `semi_supervised` 若未来对齐）复用与 `supervised` 相同的分支结构：`upload` 三 ID、`kfold` 两 ID、`split`/默认单 `dataset_path`。
- **参数契约**：与监督一致，在 `parameters` 中传递 `train_dataset_file_id` / `validation_dataset_file_id` / `test_dataset_file_id`（upload）、`kfold_train_dataset_file_id` / `kfold_test_dataset_file_id`（kfold）；`split` 仍可用顶层 `dataset_path: file://...`。
- **优点**：单一落盘入口、与监督维护方式一致、易测。
- **缺点**：`parameters` 字段名与监督共用，需在文档中写清「无监督也使用相同键」。

### 方案 B：仅在 `_execute_unsupervised_training_core` 内复制文件

- **优点**：改动局部在 unsupervised 核心。
- **缺点**：与监督 `_execute_training` 重复路径逻辑，易漂移。

### 方案 C：前端把多文件拼进 `dataset_path` 字符串由后端解析

- **缺点**：脆弱、与现有 `file://` 安全校验不一致，**不推荐**。

**结论：采用方案 A。**

## 详细设计

### 1）前端（主：`Unsupervised.vue`；配套：见上文「实施范围」）

- **策略 UI**：继续用现有 `BaseTrainingForm`，与 PHP 对齐的配置调整包括：打开三文件上传（例如 `showTestUpload: true`，与监督默认一致）、`split` / `kfold` 区块保持组件已有布局。
- **提交**：`Unsupervised.vue` 的 `handleSubmit` 在 `upload` / `kfold` 下从表单 `submit` 载荷读取各文件 ID（依赖 `BaseTrainingForm` 补齐后提供的字段），写入 `parameters`：`train_dataset_file_id`、`validation_dataset_file_id`、`test_dataset_file_id`、`kfold_train_dataset_file_id`、`kfold_test_dataset_file_id`；`split` 继续传 `ratio` 与 `dataset_path`（`file://...`）。`dataset_path` 与监督类似可作为训练集占位/兼容。
- **校验**：在 `handleSubmit`（及必要时后端）校验各策略必填项与 K 值范围，与 PHP 语义一致。

### 2）后端（`training_service.py`）

- 在 `_execute_training` 的「处理数据集文件」段，将当前仅针对 `supervised` 的 `upload` / `kfold` 分支**扩展**为：`training_type in ("supervised", "unsupervised")` 时执行相同落盘逻辑（`semi_supervised` 保持现状，除非另有 spec）。
- `split` 与默认：非上述分支时，维持「单 `dataset_path` → `_data.txt`」。
- 不改变无监督脚本命令拼装位置（仍在 `_execute_unsupervised_training_core`），仅保证进入脚本前 Jobs 目录文件布局与 PHP 一致。

### 3）损失 / 优化器

- 不修改 PHP 枚举；前端继续提交当前 `loss_function` / `optimizer`（或 `optimizer_function`）字符串。
- 若某选项导致脚本报错，视为「脚本不支持」而非本 spec 范围；可在后续单独做白名单或文档说明。

### 4）错误处理

- 缺少必填文件或 ID 时：创建任务前或执行前 `ValueError` / `HTTPException`，信息明确（与监督同类文案风格）。

### 5）测试与验收

- 手工：三种策略各跑一轮，检查 `download_data/Jobs/{jobId}/` 下文件是否与 PHP 表一致。
- 自动化（可选）：对 `_execute_training` 中 unsupervised+upload 的复制逻辑做单元测试（mock DB 文件记录）。

## 影响文件（计划）

- **必选**：`automata-web/src/views/ModelTrain/Unsupervised.vue`、`backend/api/services/training_service.py`
- **强烈推荐（最小配套）**：`automata-web/src/components/Training/BaseTrainingForm.vue`（补齐 train/val/kfold 训练集的上传与 submit 载荷中的 ID 字段）

## 实施顺序

1. （若采纳配套）补齐 `BaseTrainingForm` 中多文件上传与 ID 进入 `submit` 载荷。  
2. 调整 `Unsupervised.vue` 的 `formConfig` 与 `handleSubmit`（含校验与 `parameters` / `dataset_path`）。  
3. 扩展 `_execute_training` 落盘分支，使 `unsupervised` 与 `supervised` 共享同一套 `upload` / `kfold` 复制逻辑。  
4. 联调与最小测试。
