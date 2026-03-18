<template>
  <div class="chat-message" :class="[`chat-message--${message.role}`]">
    <!-- 用户消息 -->
    <div v-if="message.role === 'user'" class="message-bubble user-bubble">
      <div class="message-content">{{ message.content }}</div>
      <div class="message-time">{{ formatTime(message.timestamp) }}</div>
    </div>

    <!-- Assistant 消息 -->
    <div v-else-if="message.role === 'assistant'" class="message-bubble assistant-bubble">
      <!-- 思考中状态 -->
      <div v-if="message.isThinking" class="thinking-indicator">
        <span class="thinking-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </span>
        <span class="thinking-text">正在思考</span>
      </div>
      
      <!-- 消息内容 -->
      <div 
        v-else 
        class="message-content markdown-content" 
        v-html="renderMarkdown(message.content)"
      ></div>
      <div class="message-time">{{ formatTime(message.timestamp) }}</div>
    </div>

    <!-- 工具调用消息 -->
    <div v-else-if="message.role === 'tool'" class="tool-card">
      <div class="tool-header" @click="toggleToolExpand">
        <span class="tool-icon">🔧</span>
        <span class="tool-name">{{ message.toolCall?.tool || '工具调用' }}</span>
        <span class="tool-status" :class="message.toolResult ? 'completed' : 'running'">
          {{ message.toolResult ? '✓ 完成' : '运行中...' }}
        </span>
        <span class="expand-icon">{{ isExpanded ? '▼' : '▶' }}</span>
      </div>
      
      <!-- 展开的详情 -->
      <div v-if="isExpanded" class="tool-details">
        <div v-if="message.toolCall?.args" class="tool-args">
          <div class="detail-label">参数:</div>
          <pre class="detail-content">{{ formatArgs(message.toolCall.args) }}</pre>
        </div>
        <div v-if="message.toolResult" class="tool-result">
          <div class="detail-label">结果:</div>
          <pre class="detail-content">{{ truncateResult(message.toolResult.result) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { ChatMessage } from '@/stores/agent'

// Props
const props = defineProps<{
  message: ChatMessage
}>()

// 工具卡片展开状态
const isExpanded = ref(false)

/**
 * 切换工具卡片展开/折叠
 */
function toggleToolExpand(): void {
  isExpanded.value = !isExpanded.value
}

/**
 * 格式化时间
 */
function formatTime(date: Date): string {
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

/**
 * 格式化工具参数
 */
function formatArgs(args: any): string {
  try {
    return JSON.stringify(args, null, 2)
  } catch {
    return String(args)
  }
}

/**
 * 截断过长的结果
 */
function truncateResult(result: string, maxLength: number = 500): string {
  if (result.length <= maxLength) return result
  return result.slice(0, maxLength) + '...(已截断)'
}

/**
 * 简单的 Markdown 渲染
 * 支持：加粗、斜体、行内代码、代码块、换行
 */
function renderMarkdown(text: string): string {
  if (!text) return ''
  
  let html = text
  
  // 转义 HTML 特殊字符
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // 代码块 (```code```)
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre class="code-block"><code>${code.trim()}</code></pre>`
  })
  
  // 行内代码 (`code`)
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  
  // 加粗 (**text** 或 __text__)
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>')
  
  // 斜体 (*text* 或 _text_)
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  html = html.replace(/_([^_]+)_/g, '<em>$1</em>')
  
  // 换行
  html = html.replace(/\n/g, '<br>')
  
  return html
}
</script>

<style scoped>
.chat-message {
  margin-bottom: 12px;
  display: flex;
}

.chat-message--user {
  justify-content: flex-end;
}

.chat-message--assistant {
  justify-content: flex-start;
}

.chat-message--tool {
  justify-content: flex-start;
}

/* 消息气泡基础样式 */
.message-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  word-wrap: break-word;
  position: relative;
}

/* 用户消息气泡 */
.user-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

/* Assistant 消息气泡 */
.assistant-bubble {
  background: #f0f2f5;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
}

.message-time {
  font-size: 11px;
  opacity: 0.7;
  margin-top: 4px;
  text-align: right;
}

/* 思考中动画 */
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  background: #667eea;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.thinking-text {
  font-size: 13px;
  color: #666;
}

/* 工具卡片样式 */
.tool-card {
  width: 90%;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  font-size: 13px;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f8f9fa;
  cursor: pointer;
  user-select: none;
}

.tool-header:hover {
  background: #f0f2f5;
}

.tool-icon {
  font-size: 14px;
}

.tool-name {
  flex: 1;
  font-weight: 500;
  color: #333;
}

.tool-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

.tool-status.running {
  background: #fff7e6;
  color: #fa8c16;
}

.tool-status.completed {
  background: #f6ffed;
  color: #52c41a;
}

.expand-icon {
  font-size: 10px;
  color: #999;
}

.tool-details {
  padding: 10px 12px;
  border-top: 1px solid #e4e7ed;
}

.detail-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.detail-content {
  margin: 0;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', monospace;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 150px;
  overflow-y: auto;
}

.tool-args {
  margin-bottom: 8px;
}

/* Markdown 内容样式 */
.markdown-content :deep(strong) {
  font-weight: 600;
}

.markdown-content :deep(em) {
  font-style: italic;
}

.markdown-content :deep(.inline-code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.markdown-content :deep(.code-block) {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 6px;
  margin: 8px 0;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.markdown-content :deep(.code-block code) {
  background: none;
  padding: 0;
  color: inherit;
}
</style>
