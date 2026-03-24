# 监督学习模型选择与参数对齐设计

## 背景

当前 Vue 版监督学习页面与历史 PHP 页面在以下点存在差异：

- 模型选择为多选，而 PHP 页面是单选。
- 训练超参数中的 `Loss Function`、`Optimizer` 选项未严格对齐到 PHP 页面同款枚举。
- 后端需要稳定接收并透传 `loss_function` 与 `optimizer_function` 到训练脚本参数（`cnn.py` 等脚本会消费该参数）。

本设计用于在不破坏现有训练邮件通知链路的前提下，完成监督学习前后端参数对齐。

## 目标

1. 监督学习模型选择改为“单选”，支持 8 个模型，并额外支持 `All`。
2. 前端参数对齐 PHP 页面：
   - `Loss Function`: `CrossEntropyLoss` / `FocalLoss` / `NLLLoss`
   - `Optimizer`: `Adam` / `SGD` / `RMSprop`
3. 后端训练服务稳定接收并透传：
   - `parameters.loss_function` -> `--loss_function`
   - `parameters.optimizer_function` -> `--optimizer_function`
4. 兼容旧请求：缺失或异常值回退默认值，不中断训练任务。
5. `model_type` 在后端也执行白名单校验，值域为：
   `cnn/lstm/rnn/mlp/autoencoder/transformer/som/rbfn/all`。

## 非目标

- 不改造无监督、半监督训练页面的参数集合。
- 不重构训练脚本内部算法逻辑。
- 不改变邮件通知成功/失败语义和 zip 可交付判定逻辑。

## 方案概览（已选）

采用最小改动方案（前端 UI + 后端参数映射兜底）：

- 前端 `Supervised.vue` 将模型选择从多选改为单选。
- 前端提交时统一输出已约定值域：
  - `model_type`: `cnn/lstm/rnn/mlp/autoencoder/transformer/som/rbfn/all`
  - `parameters.loss_function`: `crossentropy/focalloss/nllloss`
  - `parameters.optimizer_function`: `adam/sgd/rmsprop`
- 后端 `TrainingService` 增加轻量白名单归一化与默认值回退：
  - loss 默认 `crossentropy`
  - optimizer 默认 `adam`
- 训练命令继续使用脚本参数：
  - `--loss_function`
  - `--optimizer_function`
  - `--type`（单模型 `single`，选 `all` 时为 `all`）

## 详细设计

## 1) 前端交互设计（`Supervised.vue`）

- 模型区改为单选控件（radio 或单选卡片），选项：
  - `cnn`, `lstm`, `rnn`, `mlp`, `autoencoder`, `transformer`, `som`, `rbfn`, `all`
- 删除/下线“多模型并行选择”逻辑及其辅助提示。
- 提交逻辑中 `model_type` 直接取当前单选值，不再根据数组长度推断。

## 2) 前端参数映射设计

- “与 PHP 页面一致”定义：**UI 展示项一致**，请求值采用当前后端/脚本约定的小写枚举。
- `Loss Function` 下拉展示文案与值映射：
  - `CrossEntropyLoss` -> `crossentropy`
  - `FocalLoss` -> `focalloss`
  - `NLLLoss` -> `nllloss`
- `Optimizer` 下拉展示文案与值映射：
  - `Adam` -> `adam`
  - `SGD` -> `sgd`
  - `RMSprop` -> `rmsprop`
- 请求结构（监督学习）：
  - 顶层：`task_name`, `model_type`, `dataset_path`, `email`
  - `parameters`：包含 `loss_function`, `optimizer_function` 及现有超参数

## 3) 后端训练服务设计

- 路由层协议保持不变，仅接收并传递 `parameters`。
- `TrainingService` 在构建监督学习命令前做参数归一化：
  - `model_type` 若不在 `{cnn, lstm, rnn, mlp, autoencoder, transformer, som, rbfn, all}`，
    回退 `cnn` 并记录 warning。
  - `loss_function` 若不在 `{crossentropy, focalloss, nllloss}`，回退 `crossentropy` 并记录 warning。
  - `optimizer_function` 若不在 `{adam, sgd, rmsprop}`，回退 `adam` 并记录 warning。
- 命令参数透传：
  - `--loss_function <value>`
  - `--optimizer_function <value>`
- `model_type == 'all'` 时，脚本 `--type all`；否则 `--type single`。

## 4) 错误处理与兼容性

- 前端通过下拉限制可选值，减少脏值输入。
- 后端保持容错回退策略，不因脏值中断任务。
- 训练失败继续走既有失败处理（状态、错误信息、失败邮件）。

## 5) 测试与验收

- 前端验收：
  - 模型控件为单选。
  - 8 模型 + `All` 可选。
  - `Loss Function` 下拉展示文案必须为：`CrossEntropyLoss` / `FocalLoss` / `NLLLoss`。
  - `Optimizer` 下拉展示文案必须为：`Adam` / `SGD` / `RMSprop`。
  - 请求中出现 `parameters.loss_function` 与 `parameters.optimizer_function`。
  - 请求示例（节选）：
    - `model_type: "cnn"`
    - `parameters.loss_function: "crossentropy"`
    - `parameters.optimizer_function: "adam"`
- 后端验收：
  - 训练命令包含 `--loss_function`、`--optimizer_function`。
  - `all` 分支正确传递 `--type all`。
  - 非法 `model_type` 触发回退 `cnn` 并记录 warning。
  - 非法值触发回退并记录 warning。
- 回归验收：
  - 监督学习任务仍可正常创建、执行、下载结果。
  - 邮件通知功能行为不变。

## 影响文件（计划）

- 前端：
  - `automata-web/src/views/ModelTrain/Supervised.vue`
  - （如有需要）`automata-web/src/api/training.ts`
- 后端：
  - `backend/api/services/training_service.py`
  - （如有需要）`backend/api/routers/training.py`
  - `backend/tests/...`（新增/修改用例）

## 风险与缓解

- 风险：旧前端或外部调用传入旧枚举值。
  - 缓解：后端兜底归一化与默认值回退。
- 风险：模型控件改造影响现有校验逻辑。
  - 缓解：调整 `isFormValid` 与提交前检查，仅依赖单一 `selectedModel`。

## 实施顺序（高层）

1. 前端：模型多选改单选 + 参数下拉对齐。
2. 前端：提交 payload 映射规范化。
3. 后端：参数归一化与命令透传兜底。
4. 测试：前端构建与关键后端用例验证。

