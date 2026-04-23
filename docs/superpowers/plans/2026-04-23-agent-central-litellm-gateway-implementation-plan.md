# 实施计划：中央大模型网关（Docker）+ 自部署走平台代付 + BYOK

日期：2026-04-23  
关联规格：`docs/superpowers/specs/2026-04-23-agent-gateway-self-deploy-design.md`  
目标：

1. **平台供应商 API Key 仅存在于中央服务器**（Docker 内环境变量/密钥管理），**永不**进入用户仓库、用户镜像、用户可分发的 `.env.prod`。  
2. **自部署实例**通过 HTTPS 调用中央 **OpenAI 兼容** 接口，使用 **实例级 Token**（非供应商 Key）。  
3. **BYOK** 仍保留：用户配置自有 `AGENT_*_API_KEY` 时直连供应商，不经过中央。  
4. 中央「大模型接口」推荐用 **LiteLLM Proxy** 官方镜像：多厂商路由、限流、虚拟 Key、与现有 `langchain_openai.ChatOpenAI` 零协议改造。

---

## 1. 架构总览

```
[用户浏览器] → [用户机：AutoMATA 前端]
                    ↓
[用户机：FastAPI backend /api/v1/agent/ws]
        │
        ├─ AGENT_BILLING_MODE=platform
        │     ChatOpenAI(api_key=AGENT_GATEWAY_TOKEN,
        │                base_url=AGENT_GATEWAY_BASE_URL + "/v1",
        │                model=<与中央配置一致的 model 名>)
        │        → HTTPS 公网/专线 → [中央：LiteLLM Proxy :4000]
        │                → 持有 DEEPSEEK/QWEN/OPENAI Key → 上游厂商
        │
        └─ AGENT_BILLING_MODE=byok
              ChatOpenAI(api_key=用户 AGENT_*_API_KEY, base_url=厂商地址)
```

**网络要求**：

- **platform**：用户后端必须能 **出站访问** 你公开的 `AGENT_GATEWAY_BASE_URL`（HTTPS，443）。纯内网部署需 **专线 / 反向代理到内网** 或只能 BYOK。  
- **byok**：用户后端需能访问对应厂商 API（与现网一致）。

---

## 2. 中央服务器：Docker 组成（推荐）

### 2.1 单容器 MVP

- 镜像：`ghcr.io/berriai/litellm:main-stable`（以 [LiteLLM Docker 文档](https://docs.litellm.ai/docs/proxy/deploy) 为准，版本号可钉 digest）。  
- 暴露：`4000`（或经 Nginx TLS 终结后反代到 4000）。  
- 机密：`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `DASHSCOPE_API_KEY`（Qwen）/ `DEEPSEEK_API_KEY` 等 **只放在中央** `docker-compose` 或密钥管理里。

### 2.2 生产建议（二期）

- 前置 **Nginx/Caddy**：TLS、限连接、WAF。  
- **Redis**：LiteLLM 限流、虚拟 Key 持久化（见 LiteLLM Virtual Keys）。  
- **观测**：Prometheus + 日志脱敏（禁止打印 prompt 全文）。

---

## 3. 中央：`docker-compose` + `config.yaml` 示例

> 路径建议：`deploy/central-llm-gateway/docker-compose.yml` 与 `deploy/central-llm-gateway/config.yaml`（新建目录，与 AutoMATA 主 compose 分离）。

### 3.1 `docker-compose.yml`（示例）

```yaml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    container_name: automata-litellm-proxy
    restart: unless-stopped
    ports:
      - "127.0.0.1:4000:4000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
    environment:
      # 管理 UI / Master Key：仅运维知道，用于创建 Virtual Key
      LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY}
      # 上游厂商 Key（示例名以 LiteLLM 文档为准，按你实际开通的厂商填）
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY}
      DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY}
    command: ["--config", "/app/config.yaml", "--port", "4000"]
```

### 3.2 `config.yaml`（示例骨架）

- 在 `model_list` 中为每个「用户侧 `model` 字符串」配置 `litellm_params` → 实际上游 `model`。  
- 用户侧 `ChatOpenAI(model=...)` 必须与这里 **别名一致**（或通过 `AGENT_GATEWAY_MODEL_*` 映射，见第 5 节）。

```yaml
model_list:
  - model_name: automata-deepseek-chat
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: os.environ/DEEPSEEK_API_KEY

  - model_name: automata-qwen-plus
    litellm_params:
      model: dashscope/qwen-plus
      api_key: os.environ/DASHSCOPE_API_KEY

  - model_name: automata-gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

**虚拟 Key（强烈建议）**：

- 用 LiteLLM Admin API 为每个「自部署客户」生成 **Virtual Key**，写入客户 `.env.prod` 的 `AGENT_GATEWAY_TOKEN`。  
- 吊销、预算、按 key 限流均在中央完成。文档：<https://docs.litellm.ai/docs/proxy/virtual_keys>  

MVP 可暂用 **单一把 `LITELLM_MASTER_KEY` 当 Bearer**（所有客户同权，风险大），仅适合内测；对外必须用 Virtual Key。

---

## 4. 用户侧：`.env.prod` 约定

在 `deploy/.env.prod.example` 增加（示例值）：

```bash
AGENT_ENABLED=true
AGENT_BILLING_MODE=platform

# 中央 LiteLLM 对外 HTTPS 根（不要尾斜杠；LangChain 会拼 /v1）
AGENT_GATEWAY_BASE_URL=https://llm.your-domain.com

# 客户实例专用 Virtual Key（不是 sk-deepseek / sk-dashscope）
AGENT_GATEWAY_TOKEN=sk-litellm-vk-xxxx

# platform 下：与中央 config.yaml 的 model_name 对齐（或见 5.2 用映射）
AGENT_GATEWAY_MODEL_DEEPSEEK=automata-deepseek-chat
AGENT_GATEWAY_MODEL_QWEN=automata-qwen-plus
AGENT_GATEWAY_MODEL_OPENAI=automata-gpt-4o

AGENT_GATEWAY_TIMEOUT_SEC=120
```

BYOK 时：

```bash
AGENT_BILLING_MODE=byok
AGENT_GATEWAY_BASE_URL=
AGENT_GATEWAY_TOKEN=
# 继续使用现有 AGENT_DEEPSEEK_API_KEY 等
```

---

## 5. AutoMATA 后端：须改动的文件与代码草案

### 5.1 `backend/config/settings.py`

在 `Settings` 中新增字段（名称与第 4 节一致），默认值保证开发机不填也能跑：

```python
# --- Agent 计费 / 网关（platform = 走中央 LiteLLM；byok = 直连厂商）---
AGENT_BILLING_MODE: str = "byok"  # 开发默认 byok；生产自部署文档写 platform

AGENT_GATEWAY_BASE_URL: str = ""
AGENT_GATEWAY_TOKEN: str = ""
AGENT_GATEWAY_TIMEOUT_SEC: int = 120

# platform 模式下 ChatOpenAI 使用的「中央侧模型别名」
AGENT_GATEWAY_MODEL_OPENAI: str = ""
AGENT_GATEWAY_MODEL_QWEN: str = ""
AGENT_GATEWAY_MODEL_DEEPSEEK: str = ""
```

> 生产 Docker 通过 `env_file: .env.prod` 注入即可，无需改 `docker-compose.prod.yml` 结构。

### 5.2 `backend/api/agent/llm_provider.py`（核心逻辑）

**设计要点**：

- `_use_gateway() -> bool`：`AGENT_ENABLED and AGENT_BILLING_MODE.lower() == "platform" and AGENT_GATEWAY_BASE_URL and AGENT_GATEWAY_TOKEN`  
- `get_chat_model(provider)`：若 `_use_gateway()`，则 **忽略** 各厂商 `AGENT_*_API_KEY`，统一：

```python
def _gateway_model_for(provider: str) -> str:
    p = provider.lower()
    if p == "openai":
        m = settings.AGENT_GATEWAY_MODEL_OPENAI
    elif p == "qwen":
        m = settings.AGENT_GATEWAY_MODEL_QWEN
    elif p == "deepseek":
        m = settings.AGENT_GATEWAY_MODEL_DEEPSEEK
    else:
        raise ValueError(...)
    if not m.strip():
        raise ValueError(f"platform 模式未配置 AGENT_GATEWAY_MODEL_* for {p}")
    return m.strip()

def _get_gateway_model(provider: str) -> ChatOpenAI:
    base = settings.AGENT_GATEWAY_BASE_URL.rstrip("/")
    return ChatOpenAI(
        api_key=settings.AGENT_GATEWAY_TOKEN,
        base_url=f"{base}/v1",
        model=_gateway_model_for(provider),
        temperature=0,
        streaming=True,
        timeout=settings.AGENT_GATEWAY_TIMEOUT_SEC,
    )
```

在 `get_chat_model` 开头：

```python
if _use_gateway():
    return _get_gateway_model(provider or settings.AGENT_DEFAULT_PROVIDER)
# 否则走现有 _get_openai_model / _get_qwen_model / _get_deepseek_model
```

### 5.3 `validate_provider_config`（与 WebSocket `/status` 一致）

```python
def validate_provider_config(provider: Optional[str] = None) -> tuple[bool, str]:
    provider = (provider or settings.AGENT_DEFAULT_PROVIDER).lower()

    if _use_gateway():
        if not settings.AGENT_GATEWAY_BASE_URL:
            return False, "platform 模式未配置 AGENT_GATEWAY_BASE_URL"
        if not settings.AGENT_GATEWAY_TOKEN:
            return False, "platform 模式未配置 AGENT_GATEWAY_TOKEN"
        try:
            _gateway_model_for(provider)
        except ValueError as e:
            return False, str(e)
        return True, ""

    # 原有 BYOK 校验
    ...
```

### 5.4 `backend/api/agent/router.py`

- **一般无需改消息协议**；`validate_provider_config` 通过后行为与现网一致。  
- 可选：`/status` 响应增加 `billing_mode`、`gateway_configured: bool`，便于前端展示「当前走中央代付」。

### 5.5 前端 `automata-web`（可选增强）

- 若需在 UI 显示「平台代付 / BYOK」：读 `/api/v1/agent/status` 新字段。  
- **不要**在前端存任何 Gateway Token 或厂商 Key。

### 5.6 仓库与 CI

- **删除/净化** 仓库根目录 `/.env.prod` 中真实 Key，改为占位；已泄露的 Key **在厂商控制台轮换**。  
- `.github/workflows/deploy.yml`：对你自己的演示机，改为只注入 `AGENT_GATEWAY_*`，**不再**写入 `AGENT_DEEPSEEK_API_KEY` 等到 `.env.prod`（或仅内测分支保留）。  
- 对外 README：写清「自部署 platform 模式 = 向你们申请 Virtual Key」。

---

## 6. 测试计划

### 6.1 中央单机

1. 启动 LiteLLM compose。  
2. 用 `LITELLM_MASTER_KEY` 调 Admin API 创建一个 Virtual Key（或使用文档中的 UI）。  
3. 本机 `curl`：

```bash
export URL=https://llm.your-domain.com
export VK=sk-litellm-vk-xxxx

curl -sS "$URL/v1/chat/completions" \
  -H "Authorization: Bearer $VK" \
  -H "Content-Type: application/json" \
  -d '{"model":"automata-deepseek-chat","messages":[{"role":"user","content":"ping"}],"stream":false}'
```

应返回 200 且内容正常。

### 6.2 用户侧（platform）

1. 准备 **无** `AGENT_DEEPSEEK_API_KEY` 的 `.env.prod`，仅 `AGENT_BILLING_MODE=platform` + `AGENT_GATEWAY_*` + `AGENT_GATEWAY_MODEL_*`。  
2. 启动 AutoMATA `docker compose ... up`。  
3. 浏览器登录 → 打开 Agent → 发送一条消息；WebSocket 应收到 `agent_response`。  
4. 在中央 LiteLLM 日志/指标中确认 **有请求计数**，且请求体 **未打印** 完整用户内容（按你的日志级别配置）。

### 6.3 用户侧（byok）

1. `AGENT_BILLING_MODE=byok`，填真实用户 `AGENT_DEEPSEEK_API_KEY`。  
2. 断开中央或故意填错 `AGENT_GATEWAY_TOKEN`，确认 **仍可用**（证明未走中央）。

### 6.4 吊销 Virtual Key

1. 在中央吊销该 VK。  
2. 用户侧再发消息应失败；返回错误信息应提示「平台代付不可用，请配置 BYOK 或联系管理员」（需在 `router` 或 `run_agent` 捕获 401 后映射友好文案）。

### 6.5 自动化测试（建议）

- `backend/tests/test_llm_provider_gateway.py`：用 `monkeypatch` 设置 `settings.AGENT_BILLING_MODE` 等，**mock** `ChatOpenAI` 或 httpx，断言 `base_url` / `api_key` / `model` 构造正确。  
- 不对真实外网 Key 做 CI 集成测试。

---

## 7. 上线步骤清单（你可按顺序执行）

| 步骤 | 动作 | 负责方 |
|------|------|--------|
| 1 | 中央准备域名 + TLS 证书 | 运维 |
| 2 | 部署 LiteLLM + `config.yaml`，注入各厂商 Key | 运维 |
| 3 | 启用 Virtual Key，为每个自部署客户发放 VK | 运维/你方控制台 |
| 4 | 合并 AutoMATA 后端改动（settings + llm_provider + validate + 可选 status） | 开发 |
| 5 | 更新 `deploy/.env.prod.example` + 自部署文档 | 开发 |
| 6 | 轮换并清理仓库内历史密钥；`.gitignore` 确保不提交 `.env.prod` | 全员 |
| 7 | 客户侧：`bootstrap-env.sh` 生成 DB 密码等 + 粘贴 VK | 客户 |
| 8 | 联调与压测（限流、超时、流式） | 运维 |

---

## 8. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 中央单点故障 | 文档承诺 BYOK；多副本 + LB |
| VK 被盗刷 | 每客户独立 VK、IP 允许列表、预算、告警 |
| 日志泄露 prompt | 脱敏、结构化日志、禁止 debug 打印 body |
| 合规（数据出境） | 用户协议 + 可选「仅 BYOK」区域部署 |

---

## 9. 与「自写 Gateway」对比

本计划用 **LiteLLM** 作为中央 Docker 中的「大模型接口」，减少自研转发代码；若你希望极简自研，可用 FastAPI 包一层 `httpx` 转发 `/v1/chat/completions`，但需自行处理流式、重试、多厂商差异，**不推荐**作为首版。

---

## 10. 完成后应更新的规格（非本文件）

在 `2026-04-23-agent-gateway-self-deploy-design.md` 中可增加一节「中央实现选型：LiteLLM Proxy + Virtual Key」，与本文保持一致。
