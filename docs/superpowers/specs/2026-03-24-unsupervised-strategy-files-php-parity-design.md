# 无监督训练：策略与文件落盘对齐 PHP 设计

## 背景与目标

- 参考：`modelTrainPage_un.php`、`modelTrain_un.php`（与监督页同一套 **upload / split / kfold** 策略语义）。
- 目标：**仅**要求「选择策略 + 上传文件」的前后端行为与 PHP 一致（含 Jobs 目录下 `{jobID}_data.txt` / `_val.txt` / `_test.txt` 的落盘规则）；**不要求**损失函数、优化器下拉与 PHP 选项完全一致，可继续使用当前 Vue 较长列表，只要传入脚本的值被 `VAE.py` / `deepcluster.py` 接受即可。
- 非目标：重做无监督结果页、zip 等已有 FastAPI 链路（除非与本次策略/邮件转发需求冲突）。

## 实施范围（与用户约定对齐）

- **仅改两处**：`automata-web/src/views/ModelTrain/Unsupervised.vue` + `backend/api/services/training_service.py`。
- **明确不改**：`BaseTrainingForm.vue`（用户决策 B）。
- **新增目标**：无监督训练任务的邮件转发链路与监督训练一致（任务成功/失败通知策略一致、触发点一致、参数透传一致）。

## PHP 行为摘要（契约）

| `strategy` | 上传 | 落盘文件 | `ratio` / `k_folds`（脚本侧） |
|------------|------|----------|-------------------------------|
| `upload` | 训练、验证、测试各 1 | `_data.txt`, `_val.txt`, `_test.txt` | `ratio=0`, `kfold=0` |
| `split` | 单一数据集 | 仅 `_data.txt` | `ratio` = 表单比例字符串；`kfold=0` |
| `kfold` | 训练集 + 测试集 + K | `_data.txt`, `_test.txt`（无 `_val.txt`） | `ratio=0`；`k_folds` = K |

## 方案对比

### 方案 A（推荐）：`Unsupervised.vue` 内复制监督页上传与参数组装；后端 `_execute_training` 统一落盘

- **做法**：在 `Unsupervised.vue` 内新增并管理独立上传控件与上传状态（train/val/test、kfold_train/kfold_test、split_dataset），用 `trainingApi.uploadFile` 获取文件记录 `id/file_path`；提交时按监督页同名参数传到后端。后端在 `_execute_training` 中对 `unsupervised` 复用监督落盘分支（upload 三文件、kfold 两文件、split 单文件）。
- **参数契约**：与监督一致，`parameters` 传 `train_dataset_file_id` / `validation_dataset_file_id` / `test_dataset_file_id` / `kfold_train_dataset_file_id` / `kfold_test_dataset_file_id`；`dataset_path` 在 split 必传，在 upload/kfold 可传训练集路径作兼容。
- **优点**：满足「不改 BaseTrainingForm」约束；后端保持统一落盘入口。
- **缺点**：`Unsupervised.vue` 会引入一段与监督相似的上传逻辑，存在重复。

### 方案 B：仅依赖当前 `BaseTrainingForm` 输出，后端做兜底解析

- **优点**：前端改动少。
- **缺点**：`BaseTrainingForm` 当前不会给出 upload/kfold 所需多文件 ID，无法稳定对齐 PHP 契约，风险高。

### 方案 C：前端把多文件拼进 `dataset_path` 字符串由后端解析

- **缺点**：脆弱、与现有 `file://` 安全校验不一致，**不推荐**。

### 方案 D：改 `BaseTrainingForm` 补齐上传字段

- **优点**：复用最好、重复最少。
- **缺点**：与用户“B：不碰 BaseTrainingForm”冲突，不采用。

**结论：采用方案 A。**

## 详细设计

### 1）前端（`Unsupervised.vue`，不改共享表单）

- **策略 UI**：在 `Unsupervised.vue` 内新增监督同款策略区（split/upload/kfold）与上传器，不再依赖 `BaseTrainingForm` 内置策略上传块产出多文件字段。
- **上传逻辑**：每个上传位独立调用 `trainingApi.uploadFile`，保存 `uploadedFileInfo.*.id` 与 `uploadedFileInfo.*.file_path`；切换策略时清空历史上传状态，避免串用。
- **提交组装**：`handleSubmit` 按策略写入监督同名参数键：`train_dataset_file_id`、`validation_dataset_file_id`、`test_dataset_file_id`、`kfold_train_dataset_file_id`、`kfold_test_dataset_file_id`；split 继续传 `ratio` + `dataset_path`。
- **校验**：前端提交前做策略必填检查（upload 三文件、kfold 两文件+K、split 单文件+比例），并保留后端二次校验。

### 2）后端（`training_service.py`）

- 在 `_execute_training` 的「处理数据集文件」段，将当前仅针对 `supervised` 的 `upload` / `kfold` 分支**扩展**为：`training_type in ("supervised", "unsupervised")` 时执行相同落盘逻辑（`semi_supervised` 保持现状，除非另有 spec）。
- `split` 与默认：非上述分支时，维持「单 `dataset_path` → `_data.txt`」。
- 不改变无监督脚本命令拼装位置（仍在 `_execute_unsupervised_training_core`），仅保证进入脚本前 Jobs 目录文件布局与 PHP 一致。
- 参数键名约定：前端/任务参数保持 `kfold`；脚本命令层按现有实现映射为 `--k_folds`。

### 3）邮件转发（与监督一致）

- **后端触发点**：无监督任务沿用与监督相同的邮件发送触发逻辑（成功邮件与失败邮件），不创建额外异步通道。
- **前端透传**：`Unsupervised.vue` 提交时确保 `email` 与监督一致透传到任务创建接口；空邮箱时不发邮件。
- **一致性要求**：邮件主题、正文模板、附件/下载链接策略与监督保持一致（由现有 `email_service` 与训练服务公共逻辑负责）。
- 若现有 `email_service` 模板已公共复用，则本次不改模板实现，仅校验无监督调用路径与监督触发点一致。

### 4）损失 / 优化器

- 不修改 PHP 枚举；前端继续提交当前 `loss_function` / `optimizer`（或 `optimizer_function`）字符串。
- 若某选项导致脚本报错，视为「脚本不支持」而非本 spec 范围；可在后续单独做白名单或文档说明。

### 5）错误处理

- 缺少必填文件或 ID 时：创建任务前或执行前 `ValueError` / `HTTPException`，信息明确（与监督同类文案风格）。

### 6）测试与验收

- 手工：三种策略各跑一轮，检查 `download_data/Jobs/{jobId}/` 下文件是否与 PHP 表一致。
- 文件断言清单：`upload` 必有 `_data/_val/_test`；`split` 仅有 `_data`（无 `_val/_test`）；`kfold` 必有 `_data/_test`（无 `_val`）。
- 手工：无监督成功与失败各触发一轮，验证邮件行为与监督任务一致（有邮箱发送、无邮箱不发送、文案模板一致）。
- 自动化（可选）：对 `_execute_training` 中 unsupervised+upload 的复制逻辑做单元测试（mock DB 文件记录）。

## 影响文件（计划）

- **必选**：`automata-web/src/views/ModelTrain/Unsupervised.vue`、`backend/api/services/training_service.py`

## 实施顺序

1. 在 `Unsupervised.vue` 内补齐监督式上传与策略状态管理（不改 `BaseTrainingForm`）。  
2. 调整 `handleSubmit` 参数组装与策略校验。  
3. 扩展 `_execute_training` 落盘分支，使 `unsupervised` 与 `supervised` 共享同一套 `upload` / `kfold` 复制逻辑，并确认邮件发送链路一致。  
4. 联调与最小测试（含邮件路径验证）。
