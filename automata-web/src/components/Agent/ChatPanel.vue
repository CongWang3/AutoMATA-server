<template>
  <!-- 仅在用户已登录时显示 -->
  <div v-if="userStore.isAuthenticated" class="chat-panel-container">
    <!-- 悬浮按钮 -->
    <button 
      class="chat-fab" 
      :class="{ 'chat-fab--open': agentStore.isOpen }"
      @click="agentStore.togglePanel"
      :title="agentStore.isOpen ? 'Chat off' : 'Open the AI assistant'"
    >
      <span class="fab-icon">
        <svg v-if="!agentStore.isOpen" viewBox="0 0 24 24" width="35" height="35" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" width="35" height="35" fill="currentColor">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </span>
      
      <span 
        class="connection-indicator" 
        :class="agentStore.isConnected ? 'connected' : 'disconnected'"
        :title="agentStore.isConnected ? 'Connected' : 'Disconnected'"
      ></span>
    </button>

    <!-- 聊天面板 -->
    <Transition name="panel-slide">
      <div v-if="agentStore.isOpen" class="chat-panel">
        <!-- 顶部栏 -->
        <div class="panel-header">
          <div class="header-left">
            <span class="header-title">AI Assistant</span>
            <span class="connection-status" :class="agentStore.isConnected ? 'online' : 'offline'">
              {{ agentStore.isConnected ? 'Online' : 'Offline' }}
            </span>
          </div>
          
          <div class="header-actions">
            <!-- 模型切换下拉 -->
            <div class="provider-select">
              <select 
                v-model="selectedProvider" 
                @change="onProviderChange"
                class="provider-dropdown"
              >
                <option 
                  v-for="provider in PROVIDERS" 
                  :key="provider.value" 
                  :value="provider.value"
                >
                  {{ provider.label }} ({{ provider.description }})
                </option>
              </select>
            </div>
            
            <!-- 清空按钮 -->
            <button 
              v-if="agentStore.hasMessages"
              class="header-btn" 
              @click="onClearHistory"
              title="Clear chat history"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
            </button>
            
            <!-- 关闭按钮 -->
            <button class="header-btn close-btn" @click="agentStore.closePanel" title="Close">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- BYOK：Qwen / DeepSeek 自有 API Key（仅存本机，不落 localStorage） -->
        <div class="byok-panel">
          <button type="button" class="byok-toggle" @click="byokExpanded = !byokExpanded">
            {{ byokExpanded ? '▼' : '▶' }} API Keys (Qwen / DeepSeek)
          </button>
          <div v-show="byokExpanded" class="byok-body">
            <p class="byok-hint">
              Optional. Leave empty to use server default keys. Save overwrites; clear field + Save removes your BYOK for that provider.
            </p>
            <div class="byok-row">
              <span class="byok-label">Qwen</span>
              <span class="byok-badge" :class="byokStatus.qwen_configured ? 'on' : 'off'">
                {{ byokStatus.qwen_configured ? 'BYOK' : 'Default' }}
              </span>
            </div>
            <input
              v-model="byokQwenInput"
              type="password"
              class="byok-input"
              placeholder="sk-... (optional)"
              autocomplete="off"
            />
            <div class="byok-row">
              <span class="byok-label">DeepSeek</span>
              <span class="byok-badge" :class="byokStatus.deepseek_configured ? 'on' : 'off'">
                {{ byokStatus.deepseek_configured ? 'BYOK' : 'Default' }}
              </span>
            </div>
            <input
              v-model="byokDeepseekInput"
              type="password"
              class="byok-input"
              placeholder="sk-... (optional)"
              autocomplete="off"
            />
            <div class="byok-actions">
              <button type="button" class="byok-save" :disabled="byokSaving" @click="saveByok">Save</button>
              <button type="button" class="byok-refresh" @click="loadByokStatus">Refresh</button>
            </div>
            <p v-if="byokMessage" class="byok-msg">{{ byokMessage }}</p>
          </div>
        </div>

        <!-- 消息列表区 -->
        <div class="messages-container" ref="messagesContainer">
          <!-- 空状态 -->
          <div v-if="!agentStore.hasMessages" class="empty-state">
            <div class="empty-icon">🤖</div>
            <div class="empty-title">Hello! I am the AI Assistant</div>
            <div class="empty-desc">
              I can help you with data analysis and answer questions.<br>
              Try asking me any questions about bioinformatics!
            </div>
            <!-- 结果解读，失败诊断，参数建议 -->
            <div class="quick-actions">
              <button class="quick-action-btn" @click="onQuickMode('param_advice')">Parameter Suggestion</button>
              <button class="quick-action-btn" @click="onQuickMode('failure_diagnosis')">Failure Diagnosis</button>
              <button class="quick-action-btn" @click="onQuickMode('result_interpretation')">Result Interpretation</button>
            </div>
          </div>

          <!-- 消息列表 -->
          <ChatMessage 
            v-for="message in agentStore.messages" 
            :key="message.id" 
            :message="message"
          />
        </div>

        <!-- 错误提示 -->
        <div v-if="agentStore.error" class="error-bar">
          <span>{{ agentStore.error }}</span>
          <button @click="agentStore.clearError">✕</button>
        </div>

        <!-- 底部输入区 -->
        <div class="input-container">
          <div v-if="agentStore.currentIntentDisplay" class="intent-bar">
            Current Mode: {{ agentStore.currentIntentDisplay }}
          </div>
          <div class="jobid-bar">
            <input
              v-model.trim="linkedJobId"
              class="jobid-input"
              placeholder="Optional: Linked JobID (e.g. 20260331163004_e29ee5e8)"
            >
            <span v-if="agentStore.currentJobContext?.jobId" class="jobid-status">
              Identified Job: {{ agentStore.currentJobContext.jobId }}
            </span>
          </div>
          <div class="input-wrapper">
            <textarea
              ref="inputRef"
              v-model="inputMessage"
              @keydown="onKeyDown"
              placeholder="Enter message, Shift+Enter to newline..."
              class="message-input"
              :disabled="agentStore.isSending"
              rows="1"
            ></textarea>
            <button 
              class="send-btn" 
              @click="onSend"
              :disabled="!inputMessage.trim() || agentStore.isSending"
              :title="agentStore.isSending ? 'Sending...' : 'Send message'"
            >
              <svg v-if="!agentStore.isSending" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
              <span v-else class="sending-spinner"></span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useAgentStore, PROVIDERS, type AgentMode } from '@/stores/agent'
import { fetchAgentByokStatus, saveAgentByokKeys } from '@/api/agentByok'
import ChatMessage from './ChatMessage.vue'

// Stores
const userStore = useUserStore()
const agentStore = useAgentStore()

// 组件状态
const inputMessage = ref('')
const linkedJobId = ref('')
const selectedProvider = ref(agentStore.currentProvider)
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

const byokExpanded = ref(false)
const byokStatus = ref({ qwen_configured: false, deepseek_configured: false })
const byokQwenInput = ref('')
const byokDeepseekInput = ref('')
const byokSaving = ref(false)
const byokMessage = ref('')

async function loadByokStatus(): Promise<void> {
  try {
    byokStatus.value = await fetchAgentByokStatus()
    byokMessage.value = ''
  } catch (e) {
    byokMessage.value = e instanceof Error ? e.message : 'Failed to load API key status'
  }
}

async function saveByok(): Promise<void> {
  byokSaving.value = true
  byokMessage.value = ''
  try {
    const payload: Record<string, string> = {}
    if (byokQwenInput.value.trim()) {
      payload.qwen = byokQwenInput.value.trim()
    } else if (byokStatus.value.qwen_configured) {
      payload.qwen = ''
    }
    if (byokDeepseekInput.value.trim()) {
      payload.deepseek = byokDeepseekInput.value.trim()
    } else if (byokStatus.value.deepseek_configured) {
      payload.deepseek = ''
    }
    if (Object.keys(payload).length === 0) {
      byokMessage.value = 'No changes to save.'
      return
    }
    await saveAgentByokKeys(payload)
    byokQwenInput.value = ''
    byokDeepseekInput.value = ''
    await loadByokStatus()
    byokMessage.value = 'Saved. Next chat uses updated keys.'
  } catch (e) {
    byokMessage.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    byokSaving.value = false
  }
}

/**
 * 发送消息
 */
async function onSend(): Promise<void> {
  if (!inputMessage.value.trim() || agentStore.isSending) return
  
  const message = inputMessage.value
  inputMessage.value = ''
  
  // 重置输入框高度
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
  
  await agentStore.sendMessage(message, undefined, linkedJobId.value || undefined)
}

async function onQuickMode(mode: AgentMode): Promise<void> {
  const presets: Record<AgentMode, string> = {
    param_advice: 'Please suggest practical parameters for my task goal in plain language.',
    failure_diagnosis: 'Please diagnose why the task failed. I can provide terminal logs; start with error classification.',
    result_interpretation: 'Please interpret my results and generate a concise report for non-technical biology users.',
  }
  await agentStore.sendMessage(presets[mode], mode, linkedJobId.value || undefined)
}

/**
 * 键盘事件处理
 */
function onKeyDown(event: KeyboardEvent): void {
  // Enter 发送，Shift+Enter 换行
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    onSend()
  }
}

/**
 * 切换 AI 提供商
 */
function onProviderChange(): void {
  agentStore.switchProvider(selectedProvider.value)
}

/**
 * 清空聊天记录
 */
function onClearHistory(): void {
  if (confirm('Are you sure you want to clear all chat history?')) {
    agentStore.clearHistory()
  }
}

/**
 * 滚动到底部
 */
function scrollToBottom(): void {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

/**
 * 自动调整输入框高度
 */
function autoResizeInput(): void {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    const newHeight = Math.min(inputRef.value.scrollHeight, 120)
    inputRef.value.style.height = `${newHeight}px`
  }
}

// 监听消息变化，自动滚动
watch(
  () => agentStore.messages.length,
  () => {
    scrollToBottom()
  }
)

// 监听消息内容变化（流式更新），自动滚动
watch(
  () => agentStore.messages.map(m => m.content).join(''),
  () => {
    scrollToBottom()
  }
)

// 监听输入内容变化，自动调整高度
watch(inputMessage, () => {
  autoResizeInput()
})

// 同步 provider 状态
watch(
  () => agentStore.currentProvider,
  (newVal) => {
    selectedProvider.value = newVal
  }
)

// Linked JobID 与当前「已识别任务」不一致时立即清空展示，避免换 job 后仍显示旧 Identified Job
watch(linkedJobId, (v) => {
  const t = v.trim()
  const ctxId = agentStore.currentJobContext?.jobId ?? ''
  if (t !== ctxId) {
    agentStore.clearJobContext()
  }
})

// 面板打开时聚焦输入框
watch(
  () => agentStore.isOpen,
  (isOpen) => {
    if (isOpen) {
      void loadByokStatus()
      nextTick(() => {
        inputRef.value?.focus()
      })
    }
  }
)

onMounted(() => {
  // 初始化时如果面板已打开，聚焦输入框
  if (agentStore.isOpen) {
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

onUnmounted(() => {
  // 组件卸载时断开连接
  agentStore.disconnect()
})
</script>

<style scoped>
/* 容器：仅包裹 FAB；面板用 position:fixed 贴视口，避免父级仅 70×70 时 absolute 面板被裁剪或叠层异常 */
.chat-panel-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 10050;
  width: 70px;
  height: 70px;
  pointer-events: none;
}

.chat-panel-container .chat-fab,
.chat-panel-container .chat-panel {
  pointer-events: auto;
}

/* 悬浮按钮 */
.chat-fab {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  position: relative;
}

.chat-fab:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.chat-fab--open {
  background: #ff6b6b;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
}

.fab-icon {
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.connection-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid white;
}

.connection-indicator.connected {
  background: #52c41a;
}

.connection-indicator.disconnected {
  background: #ff4d4f;
}

/* 聊天面板：fixed 相对视口，避免 absolute 相对 70px 容器导致内容被裁切/不可见 */
.chat-panel {
  position: fixed;
  right: 20px;
  bottom: calc(20px + 70px + 10px);
  width: 380px;
  max-width: calc(100vw - 32px);
  height: min(550px, calc(100vh - 120px));
  max-height: calc(100vh - 120px);
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 面板动画 */
.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: all 0.3s ease;
}

.panel-slide-enter-from,
.panel-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* 顶部栏 */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.connection-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
}

.connection-status.online {
  background: rgba(82, 196, 26, 0.3);
}

.connection-status.offline {
  background: rgba(255, 77, 79, 0.3);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-select {
  position: relative;
}

.provider-dropdown {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 6px;
  padding: 4px 8px;
  color: white;
  font-size: 12px;
  cursor: pointer;
  outline: none;
}

.provider-dropdown option {
  color: #333;
  background: white;
}

.header-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: background 0.2s;
}

.header-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* BYOK 折叠区 */
.byok-panel {
  border-bottom: 1px solid #eee;
  background: #f9f9fb;
  flex-shrink: 0;
}
.byok-toggle {
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: #555;
  cursor: pointer;
}
.byok-toggle:hover {
  background: #efeff4;
}
.byok-body {
  padding: 0 12px 10px;
}
.byok-hint {
  font-size: 11px;
  color: #888;
  margin: 0 0 8px;
  line-height: 1.4;
}
.byok-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
}
.byok-label {
  font-size: 12px;
  font-weight: 600;
  color: #444;
}
.byok-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}
.byok-badge.on {
  background: #e6f7ff;
  color: #096dd9;
}
.byok-badge.off {
  background: #f0f0f0;
  color: #666;
}
.byok-input {
  width: 100%;
  margin-top: 4px;
  padding: 6px 8px;
  font-size: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-sizing: border-box;
}
.byok-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.byok-save,
.byok-refresh {
  flex: 1;
  padding: 6px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid #ccc;
  cursor: pointer;
  background: white;
}
.byok-save {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}
.byok-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.byok-msg {
  font-size: 11px;
  margin: 8px 0 0;
  color: #096dd9;
}

/* 消息列表区 */
.messages-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  line-height: 1.6;
  color: #888;
}

.quick-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-action-btn {
  border: 1px solid #dcdfe6;
  background: #fff;
  color: #303133;
  border-radius: 16px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}

.quick-action-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

/* 错误提示 */
.error-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #fff2f0;
  border-top: 1px solid #ffccc7;
  color: #ff4d4f;
  font-size: 13px;
}

.error-bar button {
  background: none;
  border: none;
  color: #ff4d4f;
  cursor: pointer;
  font-size: 14px;
}

/* 底部输入区 */
.input-container {
  padding: 12px 16px;
  background: white;
  border-top: 1px solid #e8e8e8;
}

.intent-bar {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.jobid-bar {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.jobid-input {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 12px;
  outline: none;
}

.jobid-input:focus {
  border-color: #409eff;
}

.jobid-status {
  font-size: 12px;
  color: #67c23a;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #f5f7fa;
  border-radius: 12px;
  padding: 8px 12px;
}

.message-input {
  flex: 1;
  border: none;
  background: transparent;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  max-height: 120px;
  outline: none;
  font-family: inherit;
}

.message-input:disabled {
  opacity: 0.6;
}

.message-input::placeholder {
  color: #bbb;
}

.send-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 发送中动画 */
.sending-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 响应式：小屏幕全屏展开 */
@media (max-width: 480px) {
  .chat-panel-container {
    bottom: 10px;
    right: 10px;
  }
  
  .chat-panel {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: 100%;
    border-radius: 0;
  }
  
  .chat-fab {
    width: 50px;
    height: 50px;
  }
}

/* 滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #ccc;
}
</style>
