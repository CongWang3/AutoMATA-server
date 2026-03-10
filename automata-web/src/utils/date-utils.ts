/**
 * 日期格式化工具函数
 * 提供统一的日期处理和格式化功能
 */

/**
 * 格式化日期字符串
 * @param dateString 日期字符串
 * @returns 格式化后的日期字符串
 */
export function formatDate(dateString: string | undefined): string {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '无效日期'
  return date.toLocaleString('zh-CN')
}

/**
 * 获取文件上传时间（兼容新旧字段）
 * @param file 文件信息对象
 * @returns 格式化的时间字符串
 */
export function getFileUploadTime(file: { created_at?: string; upload_time?: string }): string {
  // 优先使用 created_at，降级到 upload_time
  const timeString = file.created_at || file.upload_time
  return formatDate(timeString)
}

/**
 * 格式化相对时间
 * @param date 日期对象或字符串
 * @returns 相对时间描述
 */
export function formatRelativeTime(date: Date | string): string {
  const targetDate = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffMs = now.getTime() - targetDate.getTime()
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMinutes < 1) {
    return '刚刚'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return formatDate(targetDate.toISOString())
  }
}