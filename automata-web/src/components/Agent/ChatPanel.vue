<template>
  <!-- 仅在用户已登录时显示 -->
  <div v-if="userStore.isAuthenticated" class="chat-panel-container">
    <!-- 悬浮按钮 -->
    <button 
      class="chat-fab" 
      :class="{ 'chat-fab--open': agentStore.isOpen }"
      @click="agentStore.togglePanel"
      :title="agentStore.isOpen ? '关闭聊天' : '打开 AI 助手'"
    >
      <span class="fab-icon">
        <svg v-if="!agentStore.isOpen" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </span>
      <!-- 连接状态指示器 -->
      <span 
        class="connection-indicator" 
        :class="agentStore.isConnected ? 'connected' : 'disconnected'"
        :title="agentStore.isConnected ? '已连接' : '未连接'"
      ></span>
    </button>

    <!-- 聊天面板 -->
    <Transition name="panel-slide">
      <div v-if="agentStore.isOpen" class="chat-panel">
        <!-- 顶部栏 -->
        <div class="panel-header">
          <div class="header-left">
            <span class="header-title">AI 助手</span>
            <span class="connection-status" :class="agentStore.isConnected ? 'online' : 'offline'">
              {{ agentStore.isConnected ? '在线' : '离线' }}
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
              title="清空聊天记录"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
            </button>
            
            <!-- 关闭按钮 -->
            <button class="header-btn close-btn" @click="agentStore.closePanel" title="关闭">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- 消息列表区 -->
        <div class="messages-container" ref="messagesContainer">
          <!-- 空状态 -->
          <div v-if="!agentStore.hasMessages" class="empty-state">
            <div class="empty-icon">🤖</div>
            <div class="empty-title">你好！我是 AI 助手</div>
            <div class="empty-desc">
              我可以帮助你进行数据分析、解答问题。<br>
              试试问我任何关于生物信息学的问题吧！
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
          <div class="input-wrapper">
            <textarea
              ref="inputRef"
              v-model="inputMessage"
              @keydown="onKeyDown"
              placeholder="输入消息，Shift+Enter 换行..."
              class="message-input"
              :disabled="agentStore.isSending"
              rows="1"
            ></textarea>
            <button 
              class="send-btn" 
              @click="onSend"
              :disabled="!inputMessage.trim() || agentStore.isSending"
              :title="agentStore.isSending ? '发送中...' : '发送消息'"
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
import { useAgentStore, PROVIDERS } from '@/stores/agent'
import ChatMessage from './ChatMessage.vue'

// Stores
const userStore = useUserStore()
const agentStore = useAgentStore()

// 组件状态
const inputMessage = ref('')
const selectedProvider = ref(agentStore.currentProvider)
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

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
  
  await agentStore.sendMessage(message)
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
  if (confirm('确定要清空所有聊天记录吗？')) {
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

// 面板打开时聚焦输入框
watch(
  () => agentStore.isOpen,
  (isOpen) => {
    if (isOpen) {
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
/* 容器 */
.chat-panel-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
}

/* 悬浮按钮 */
.chat-fab {
  width: 56px;
  height: 56px;
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

/* 聊天面板 */
.chat-panel {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 380px;
  height: 550px;
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

/* 消息列表区 */
.messages-container {
  flex: 1;
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
