## 训练任务邮件通知迁移（Vue + FastAPI）

### 背景与现状

AutoMATA 已有两条链路：

1. 旧版 PHP 页面会在训练任务成功后提供结果，并支持基于 `JobID` 的离线结果组织。
2. 新版系统已提供 `Vue` 前端与 `FastAPI` 后端的训练任务 API，并通过 `jobs` 表统一管理任务状态；同时已有邮件服务实现 `send_result_email`（成功附带 zip）。

当前问题：

- 后端训练路由 `/api/v1/training/{supervised|unsupervised|semi-supervised}` 的请求体 schema 已包含 `email`，但路由未把 `payload.email` 传递给服务层。
- `TrainingService` 当前从 `parameters.get("email")` 获取邮箱，而前端把邮箱放在顶层 `payload.email`，导致邮件发送链路很可能无法触发。
- 前端当前的监督学习页面 `Supervised.vue` 未实现“登录用户邮箱自动回填”，且重置逻辑会清空邮箱；无监督/半监督页面虽复用了通用表单组件，但提交时也未携带 `email` 到后端。

### 目标

1. 将三类训练任务（监督/无监督/半监督）统一支持邮件通知。
2. 邮件行为满足：
  - 成功：发送邮件并附带训练结果 `zip`。
  - 失败：发送邮件但不附带 zip，只包含错误摘要（截断到合理长度）。
3. 前端满足：
  - 邮箱输入框默认自动填入登录用户邮箱。
  - 用户允许手动修改与清空。
  - 当用户清空后，后续点击“重置/开始新任务”不应覆盖回填（保持空）。

### 非目标

- 不实现邮件发送失败时对训练任务状态回滚或阻断。
- 不实现取消/重试任务对应的邮件策略（仅实现“训练完成/失败”的结果通知）。
- 不新增异步队列/消息总线；沿用当前训练任务的后台异步执行方式。

### 现有组件概览（用于对齐代码）

- 后端邮件服务：`backend/api/services/email_service.py`
  - 已存在：`send_result_email(to_email, job_id, analysis_type, result_dir)`
- 后端训练服务：`backend/api/services/training_service.py`
  - 已有：训练执行成功后压缩结果 zip，并在 `_execute_training` 末尾发送结果邮件（但邮箱取值不正确，且失败分支无邮件发送）
- 后端训练路由：`backend/api/routers/training.py`
  - 已有：三个训练入口与上传接口
  - 缺少：将 `payload.email` 传入服务层
- 前端监督页面：`automata-web/src/views/ModelTrain/Supervised.vue`
  - 已有：邮箱输入框、提交时带 `email: notification.email`
  - 缺少：自动回填登录邮箱与“保持空”逻辑
- 前端通用训练表单：`automata-web/src/components/Training/BaseTrainingForm.vue`
  - 已有：邮箱输入框（`localFormData.email`）
  - 缺少：自动回填、 touched 语义、reset 不应无条件清空邮箱
- 前端无监督/半监督页面：
  - `automata-web/src/views/ModelTrain/Unsupervised.vue`
  - `automata-web/src/views/ModelTrain/SemiSupervised.vue`
  - 缺少：提交时把 `email` 顶层传给后端
- 前端训练 API 客户端：`automata-web/src/api/training.ts`
  - 缺少：`payload` 类型里显式声明 `email?: string`（便于 TS 与后端契约一致）

### 设计：后端邮件通知

#### 1) 训练路由：把 `payload.email` 显式传入服务层

修改文件：`backend/api/routers/training.py`

- 在三个入口中：
  - `train_supervised(payload: TrainingTaskCreate, ...)`
  - `train_unsupervised(...)`
  - `train_semi_supervised(...)`
- 将 `payload.email` 作为独立参数传给服务层（而不是塞进 `parameters`）。

#### 2) 训练服务：让邮箱在执行链路中透传，并处理成功/失败

修改文件：`backend/api/services/training_service.py`

新增/调整点：

1. `TrainingService.create_supervised_task / create_unsupervised_task / create_semi_supervised_task`
  - 增加入参：`email: Optional[str] = None`
2. `_create_training_task(...)`
  - 增加入参并向 `_execute_training` 透传。
3. `_execute_training(...)`
  - 成功分支：调用 `email_service.send_result_email(to_email=email, result_dir=zip_file, ...)`
  - 失败分支：调用新增的 `email_service.send_failure_email(...)`

邮箱来源规则：

- 以 `payload.email` 为准。
- 若邮箱为空/不存在：跳过邮件发送，不影响训练与任务状态。

分析类型映射（提升邮件可读性；可选但推荐）：

- `supervised`   -> `监督学习模型训练`
- `unsupervised` -> `无监督学习模型训练`
- `semi_supervised` -> `半监督学习模型训练`

#### 3) 邮件服务：新增失败邮件发送方法

修改文件：`backend/api/services/email_service.py`

- 增加方法：
  - `send_failure_email(to_email: str, job_id: str, analysis_type: str, error_message: str) -> bool`
- 邮件正文规则：
  - 包含 `analysis_type`、`job_id`、`error_message` 摘要
  - 不附加任何附件
  - `error_message` 截断到前 2000 字符（默认值，可按后续需求配置）
  - 截断口径与渲染规则：
    - 按 `error_message` 的 Unicode 字符长度（等价 `Python len`）截断到前 2000 个字符
    - 对截断后的字符串执行 `HTML` 转义（建议 `html.escape`，避免 `<`/`&` 等字符破坏正文）
    - 将换行 `\n` 替换为 `<br/>`（建议在 `HTML` 转义之后替换换行，避免 `<br/>` 被再次转义）

### 设计：前端自动回填 + 保持空

#### 1) 监督学习页面：`Supervised.vue`

修改文件：`automata-web/src/views/ModelTrain/Supervised.vue`

- 在组件内新增状态：
  - `emailTouched: boolean`：用户是否“动过”邮箱输入框（包含清空）
  - `isAutoFilling: boolean`：仅在自动回填时阻止触发 touched
  - `userEmailCache: string`：缓存登录邮箱，用于 reset 恢复逻辑
- 自动回填：
  - 页面初始化时从 `useUserStore().userInfo.email` 获取
  - 若 `emailTouched=false` 则填入 `notification.email`
  - 若 `emailTouched=true` 则不覆盖当前输入（保持用户选择）
- touched 判定：
  - watch `notification.email`，当不是自动回填阶段时，将 `emailTouched=true`
- reset 行为：
  - 不再无条件 `notification.email=''`
  - 若 `emailTouched=false`：reset 恢复为登录邮箱
  - 若 `emailTouched=true`：reset 保持当前输入（可能为空）

#### 2) 无监督/半监督通用表单：`BaseTrainingForm.vue`

修改文件：`automata-web/src/components/Training/BaseTrainingForm.vue`

- 复用与监督页面相同的语义：
  - `emailTouched` / `isAutoFilling`
  - onMounted：若未 touched 则从登录用户 email 自动填入 `localFormData.email`
  - watch：用户编辑将置 touched
  - resetForm：不再无条件把 `localFormData.email` 清空
    - 若 touched=false -> 恢复登录邮箱
    - 若 touched=true  -> 保持当前 email（保持空）

#### 3) 无监督/半监督提交参数携带 email

修改文件：

- `automata-web/src/views/ModelTrain/Unsupervised.vue`
- `automata-web/src/views/ModelTrain/SemiSupervised.vue`

在构造 `trainingParams` 时添加顶层字段：

- `email: data.email || undefined`

### 设计：前端 API 客户端类型契约

修改文件：`automata-web/src/api/training.ts`

- 在 `trainSupervised / trainUnsupervised / trainSemiSupervised` 的 payload 类型中显式加入 `email?: string`
- 确保请求体把 `email` 透传到后端。

### 错误处理与边界情况

1. 用户未登录或用户信息未加载：
  - 前端自动回填跳过，`notification.email` / `data.email` 为空时后端不发送邮件。
2. 用户邮箱无效或为空：
  - 前端输入框允许编辑；无需强制后端校验（后续可追加）。
3. 训练失败：
  - 后端发送失败邮件（不附 zip），内容包含截断后的错误摘要。
4. 训练成功但结果压缩失败/zip 不存在：
  - 不应发送“成功邮件并附 zip”。
  - 该场景视为“结果不可交付”，走失败邮件分支（不附任何附件），并将任务标记为 `FAILED`（以保持任务状态与通知一致）。
  - 可执行判定条件（实现时必须落地其中之一/等价）：
    - 压缩完成后，检查 `zip_path` 是否存在：`Path(zip_path).exists()`
    - 且检查文件是否可交付：`Path(zip_path).stat().st_size > 0`（空 zip 视为不可交付）
5. SMTP 或邮件发送失败：
  - 邮件发送异常只记录日志，不应回滚或二次改变训练任务最终判定（即 job status 仍由训练/压缩结果决定）。

### 验证与测试建议

后端：

1. 成功路径：
  - 提交一组小数据集（或能快速失败/成功的极小样本），确保训练完成触发成功邮件并带 zip。
2. 失败路径：
  - 刻意提交错误模型类型/错误数据路径触发异常，验证发送失败邮件且不附带附件。

前端：

1. 自动回填：
  - 登录后进入监督/无监督/半监督页面，邮箱输入框默认显示用户 email。
2. “保持空”：
  - 手动清空邮箱后，点击重置/开始新任务，邮箱仍保持为空。
3. 提交携带：
  - console/network 校验创建训练任务请求体包含顶层 `email` 字段（或为空时不传/传空）。

### 回滚策略（如需）

- 邮件通知逻辑独立于训练结果压缩与任务状态，可通过回滚后端 email 发送改动恢复到仅训练功能。
- 前端仅影响邮箱回填/参数透传，可回滚对应字段以恢复原始提交行为。

