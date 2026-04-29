# Agent：本地部署下按厂商的 BYOK + 平台 Key 回退（可执行设计）

日期：2026-04-29  
状态：已确认（待实现）  
范围：用户各自在**本机 Docker** 部署 AutoMATA；**不引入网关**；平台提供的 Qwen/DeepSeek Key 仅存在于**后端环境变量**（如 `.env.prod`）；用户可**长期保存**自己的 Qwen/DeepSeek Key，且**按厂商独立**选择 BYOK 或平台 Key；**立即生效**切换。

---

## 1. 业务规则（已确认）

| 场景 | Qwen | DeepSeek |
|------|------|----------|
| 用户仅上传 Qwen BYOK | 始终优先用用户 Qwen Key | 未配置 BYOK → 用平台 `AGENT_DEEPSEEK_API_KEY` |
| 用户仅上传 DeepSeek BYOK | 未配置 BYOK → 用平台 `AGENT_QWEN_API_KEY` | 始终优先用用户 DeepSeek Key |
| 用户上传两者 | 两者均优先 BYOK | 两者均优先 BYOK |
| 用户删除某一侧 BYOK | 该厂商回到平台 Key（若 env 中仍有） | 同上 |

- **OpenAI**：本设计首版可仍仅走平台 env（`AGENT_OPENAI_API_KEY`）；若未来要 BYOK，规则与上表一致，可扩展文件字段。  
- **不能用其他用户的 Key**：同一实例若存在多个登录账号，BYOK 必须与**当前登录用户**绑定（见第 3 节存储策略）。

---

## 2. Key 解析顺序（实现时必须一致）

对 `provider ∈ {qwen, deepseek}`：

1. 若当前用户在该厂商下存在**有效 BYOK**（非空、非仅空白）→ 使用 BYOK。  
2. 否则 → 使用 `settings` 中对应平台环境变量：  
   - Qwen：`AGENT_QWEN_API_KEY`  
   - DeepSeek：`AGENT_DEEPSEEK_API_KEY`  
3. 若两者皆无 → `get_chat_model` / `validate_provider_config` 返回明确错误（与现网一致）。

**不要求**全局开关 `AGENT_BILLING_MODE`；是否 BYOK **完全由「该厂商是否配置了用户覆盖」推导**。

---

## 3. 存储策略（无 MySQL 新表）

### 3.1 为什么不把用户 Key 写回 `.env.prod`

- Compose 注入的 env 在进程启动时固定；**热更新**若只靠改文件，通常需**重建容器**才能进进程环境。  
- 需求为 **立即切换**，因此 BYOK 必须在**运行时**从可写介质读取，而不是仅依赖启动时的 env。

### 3.2 推荐：按用户隔离的本地文件（仍无新 DB 表）

挂载卷路径（与 `docker-compose.prod.yml` 中 `data` 一致）：

- 根目录：`./data/agent_byok/`（宿主机可写，容器内如 `/app/data/agent_byok`）  
- 每用户一个文件：`{user_id}.json`（`user_id` 为业务用户主键字符串/UUID，与 `User.id` 一致）

**文件格式示例**（UTF-8 JSON，权限建议 `0600`）：

```json
{
  "qwen": "sk-...",
  "deepseek": "sk-..."
}
```

- 某键省略或 `null`：表示该厂商**未设置 BYOK**，走平台 env。  
- 某键设为空字符串 `""`：语义为**显式清除**该厂商 BYOK（实现时可选；若不做「清除」UI，可仅支持 PUT 整对象覆盖）。

### 3.3 单账号/内网特例

若产品明确「本实例永远只有一个业务用户」，可简化为单文件 `data/agent_byok/default.json`，但**多用户同实例会串 Key**，与「不能用其他用户的 Key」冲突，故**默认采用 3.2**。

---

## 4. 后端改动清单

### 4.1 新增模块（建议）

- `backend/api/services/agent_byok_store.py`  
  - `load_byok(user_id) -> dict[str, str | None]`  
  - `save_byok(user_id, partial: dict)`（合并写入）  
  - 文件锁（`fcntl` 或 `filelock`）避免并发写损坏 JSON。  
  - **禁止**在日志中打印 Key；异常信息不写 Key 子串。

### 4.2 修改 `backend/api/agent/llm_provider.py`

- `get_chat_model(provider, user_id: str | None = None)`：在构造 `ChatOpenAI` 前，按第 2 节解析 `api_key`。  
- `_get_qwen_model` / `_get_deepseek_model`：增加「先读 BYOK，再读 `settings`」  
- `validate_provider_config(provider, user_id)`：若该平台 env 与用户 BYOK 至少有一个可用 → valid。

**注意**：`ChatOpenAI` 若在进程内缓存（若有 `agent_graphs` 按 provider 缓存），必须在 BYOK 变更后**使缓存失效**或**不要把 graph 按无 user 维度的 key 缓存**。推荐：**按 `(provider, user_id)` 维度缓存 graph**，或在保存 BYOK 后调用**清缓存**函数。

### 4.3 修改 `backend/api/agent/router.py`

- WebSocket 处理 `chat` 时，已具备 `user.id`，将其传入 `get_chat_model(..., user_id=...)` 与 `validate_provider_config(..., user_id=...)`。  
- `_get_or_create_graph(provider)` 改为 `_get_or_create_graph(provider, user_id)`。

### 4.4 新增 REST API（需登录）

| 方法 | 路径 | 行为 |
|------|------|------|
| `GET` | `/api/v1/agent/byok` | 返回 `{ "qwen_configured": bool, "deepseek_configured": bool }`，**永不返回明文 Key** |
| `PUT` | `/api/v1/agent/byok` | Body：`{ "qwen"?: string, "deepseek"?: string }`，只更新提供的字段；保存后立即生效 |

可选：`DELETE` 某厂商或 PUT 空串清除。

**权限**：默认 `get_current_active_user`；若需管理员专用，可加 `is_superuser`（按产品定）。

### 4.5 `docker-compose.prod.yml`

- 为 `backend`（及若共用配置的 `download-server` 不需要读 BYOK 则可不加）增加 volume：  
  `- ./data/agent_byok:/app/data/agent_byok`  
- 确保目录首次启动时由入口脚本 `mkdir -p` + 权限。

### 4.6 环境变量（可选）

- `AGENT_BYOK_DIR`：默认 `REPO_ROOT` 或 `/app/data/agent_byok`，便于测试覆盖。

---

## 5. 前端改动（`ChatPanel.vue` 等）

- 增加「API Key 管理」折叠区：  
  - 两个密码框：Qwen、DeepSeek（可选填）  
  - 「保存」→ `PUT /api/v1/agent/byok`  
  - 展示状态：`已配置 BYOK / 使用平台默认`（来自 GET，布尔即可）  
- **禁止**把 Key 存 `localStorage` 明文（最多仅存「已配置」标记）。

---

## 6. 安全与运维

- 平台 Key：仅 `.env.prod` / 部署机密，**不进仓库**；仓库内示例文件只用占位符。  
- BYOK 文件：磁盘权限、备份策略由用户自负；文档说明「备份目录即备份 Key」。  
- 审计：仅记录「某用户更新了 BYOK」时间与厂商名，不记录 Key。

---

## 7. 测试计划

1. **仅平台 Key**：无 BYOK 文件，Qwen/DeepSeek 均走 env，Agent 对话成功。  
2. **仅 Qwen BYOK**：文件仅 `qwen`，DeepSeek 请求仍走平台 env。  
3. **两者 BYOK**：两厂商均走文件。  
4. **清除 Qwen BYOK**：删除字段或清空后，Qwen 回到平台 env。  
5. **用户 A / 用户 B**：同机两账号，文件路径不同，互不影响。  
6. **立即切换**：保存 PUT 后**不重启容器**，下一次对话即使用新 Key（验证 graph 缓存已处理）。

---

## 8. 与既有规格的关系

- 中央网关方案见 `docs/superpowers/specs/2026-04-23-agent-gateway-self-deploy-design.md`：本设计为**本地无网关**路径，二者可并存为不同发行版/环境变量，但同一部署应只启用一种策略以免混淆。

---

## 9. 实现顺序建议

1. `agent_byok_store` + volume  
2. `llm_provider` 解析顺序 + graph 缓存维度  
3. REST API  
4. 前端表单  
5. 文档与 `deploy/.env.prod.example` 注释  
