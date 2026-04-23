# Agent Gateway：自部署不泄露平台大模型 Key 的设计

日期：2026-04-23  
状态：草案（待评审）  
范围：在 **用户自行部署** AutoMATA（Docker 等）的前提下，**默认使用平台代付** 调用大模型，**平台方的大模型供应商 API Key 永不进入用户仓库、镜像与用户服务器磁盘上的可分发配置**；同时支持 **BYOK**（用户自带 Key），以便平台停服或用户希望完全自控时仍可继续使用 Agent。

## 1. 背景与问题

### 1.1 当前行为（与目标冲突之处）

- 后端通过 `settings` 直接读取 `AGENT_*_API_KEY`，在 `llm_provider.py` 中构造 `ChatOpenAI`（见现有实现）。
- 若将平台 Key 写入用户侧的 `.env.prod`、CI 注入到用户服务器，或提交到 Git，则 **Key 已落在用户控制域**，不满足「不能泄露平台自有 Key」的约束。
- 仓库内若存在含真实 Key 的 `.env.prod`，属于 **供应链与合规高风险**，应与本设计一并清理为 **仅占位模板**。

### 1.2 目标（成功标准）

- **平台模式**：用户部署后 **无需配置** 大模型供应商 Key 即可使用 Agent；请求经 **平台托管的 Agent Gateway** 出站，供应商 Key **仅存在于 Gateway 侧**。
- **BYOK 模式**：管理员在用户实例上配置自己的 `AGENT_*_API_KEY` 等，后端 **直连** 供应商，**不经过** Gateway。
- **可演进 / 抗停服**：平台 Gateway 不可用时，实例可切换或降级到 BYOK（若已配置），避免「只能用平台」单点绑死。
- **自部署体验**：提供 `deploy/.env.prod.example` + 一键脚本：自动生成本地 `SECRET_KEY`、数据库密码等，**不要求用户手写整份 env**；**不要求**在仓库中存放真实 Key。

---

## 2. 方案选择（已确认：方案 2）

采用 **平台托管 Agent Gateway**：

- 用户实例上的 AutoMATA **不持有** 平台供应商 Key。
- 用户实例仅持有 **实例级凭据**（下称 `AGENT_GATEWAY_TOKEN`），用于向 Gateway 鉴权；该凭据 **不是** OpenAI/DeepSeek/Qwen 的 Key，泄露后果可控（可吊销、限流）。

**不采用**：仅在用户服务器注入平台 Key（无法满足保密）。  
**不采用**：仅 BYOK（与「默认平台代付」产品目标不符）。

---

## 3. 总体架构

```
[浏览器] → [用户站点的 AutoMATA 前端]
                ↓
[用户服务器：FastAPI backend / Agent]
     若 AGENT_BILLING_MODE=platform
         → HTTPS → [平台 Agent Gateway] → 供应商 API（持平台 Key）
     若 AGENT_BILLING_MODE=byok
         → HTTPS → 供应商 API（持用户 Key，仅驻用户侧）
```

- **Gateway** 为独立服务（可单独仓库/单独部署），与 AutoMATA 主站版本解耦。
- **通信全程 TLS**；Gateway 与供应商之间使用平台侧 Key；用户实例到 Gateway 使用 **短期或长期实例 Token**（见第 5 节）。

---

## 4. 用户侧配置模型（`.env.prod` 层）

### 4.1 新增 / 调整的语义化变量（建议命名）

| 变量 | 含义 |
|------|------|
| `AGENT_BILLING_MODE` | `platform` \| `byok`（默认 `platform`） |
| `AGENT_GATEWAY_BASE_URL` | Gateway 根 URL，如 `https://agent-gw.example.com` |
| `AGENT_GATEWAY_TOKEN` | 实例级 Token（仅 platform 模式必填） |
| `AGENT_GATEWAY_TIMEOUT_SEC` | 可选，超时 |
| 现有 `AGENT_*_API_KEY` | **仅 BYOK 模式**使用；platform 模式下应为空 |

### 4.2 与「不用手写 .env.prod」的关系

- 发布物提供 **`deploy/bootstrap-env.sh`**（或等价）：从 `deploy/.env.prod.example` 复制，用 `openssl rand` 等生成 `SECRET_KEY`、`DB_PASSWORD`、`MYSQL_ROOT_PASSWORD`，写回本地 `.env.prod`。
- **平台模式**：首次启动前，用户从 **你的控制台 / 邮件 / 一次性链接** 获取 `AGENT_GATEWAY_TOKEN`，脚本交互写入或环境注入；**仍不需要** 用户去申请 DeepSeek/Qwen Key。
- **BYOK 模式**：用户在管理界面或 `.env.prod` 中填入自有 Key，`AGENT_BILLING_MODE=byok`，可留空 Gateway 相关项。

---

## 5. Gateway 职责与接口形态

### 5.1 最小职责

- **鉴权**：校验 `AGENT_GATEWAY_TOKEN`（建议 `Authorization: Bearer`）。
- **路由**：按 `provider`（openai / qwen / deepseek）选择平台侧 Key 与 `base_url`。
- **转发**：对用户实例暴露 **OpenAI 兼容 Chat Completions** 子集即可（与当前 `ChatOpenAI` 一致），或转发 SSE 流式。
- **计量与风控**：按实例 Token 做 **配额、限流、封禁**；记录请求元数据（时间、实例 id、模型、token 用量），**禁止**在日志中打印用户消息全文与供应商 Key。
- **吊销**：Token 失效后立即 401，用户实例应提示切换 BYOK 或联系平台。

### 5.2 可选增强

- **mTLS** 或 **实例注册**：除 Bearer Token 外，绑定 `instance_id` + 公钥指纹，降低 Token 被盗用面。
- **短期 JWT**：Gateway 签发短期访问令牌，进一步减少长期 Token 泄露窗口（实现复杂度更高，可二期）。

---

## 6. AutoMATA 后端改造要点（实现阶段，非本文档执行）

- `get_chat_model()`：当 `AGENT_BILLING_MODE=platform` 时，构造 `ChatOpenAI`，其中：
  - `api_key` = `AGENT_GATEWAY_TOKEN`（或专用 header）
  - `base_url` = `AGENT_GATEWAY_BASE_URL` + `/v1`（或统一前缀）
- 当 `AGENT_BILLING_MODE=byok` 时，保持现有逻辑（直连供应商）。
- **禁止**在 platform 模式下读取 `AGENT_QWEN_API_KEY` / `AGENT_DEEPSEEK_API_KEY` 作为供应商 Key；避免误配置导致 Key 落盘。

---

## 7. 密钥与合规

- **平台供应商 Key**：仅存 Gateway 的 Secret 管理（KMS / 托管环境变量），不入库 GitHub、不进用户镜像。
- **用户 BYOK**：仅存用户服务器（加密-at-rest 视实现而定），平台方不可见。
- **实例 Token**：可轮换；泄露后吊销即可，**不等于** 泄露供应商 Key。
- **仓库清理**：根目录 `.env.prod` 若含真实 Key，必须改为占位并 **轮换已泄露 Key**（实现与运维动作，需在发布前完成）。

---

## 8. 与现有 CI 部署的关系

当前 `.github/workflows/deploy.yml` 存在将 `AGENT_*` 从 GitHub Secrets **写入服务器 `.env.prod`** 的做法——该模式适用于 **你本人** 控制的服务器，但 **不适用于**「把同一套流程交给第三方自部署且要求平台 Key 保密」。

- **你方托管演示/正式站**：可继续用 CI 注入，但注入的应是 **Gateway Token** 或 **BYOK**，而非直接把平台供应商 Key 写到用户可读的 compose 目录（若目录权限非仅 root，仍有泄露面；长期仍建议走 Gateway）。
- **对外自部署文档**：应引导 **platform = Gateway Token**，而非供应商 Key。

---

## 9. 停机与降级（抗停服）

- 文档明确：**platform 模式依赖 Gateway 可用性**。
- 产品行为建议：
  - Gateway 连续失败时，管理端提示 **切换到 BYOK**。
  - 可选：**不自动切换**（避免静默用用户 Key 扣费），除非用户预先勾选「允许自动降级」。

---

## 10. 测试与验收

- **platform**：无供应商 Key 的干净 `.env.prod`，仅 Gateway Token，Agent 对话成功。
- **byok**：无 Gateway Token，直连供应商成功。
- **吊销 Token**：Gateway 返回 401，前端/后端错误信息可读。
- **安全**：扫描镜像与 compose 目录，确认无 `sk-` 类平台 Key；日志无 Key 与完整 prompt 泄露。

---

## 11. 开放问题

- Gateway 由 **谁** 颁发 Token（手工、注册 API、License 绑定域名）？
- 是否对 **免费 tier** 做 IP / 并发限制？
- 是否要求用户实例 **回传匿名用量**（隐私政策）？

---

## 12. 与相关文档

- 桌面无 Docker 方案：`docs/superpowers/specs/desktop_without_docker.md`（若 Agent 同样接入，应复用 Gateway/BYOK 模型）。
