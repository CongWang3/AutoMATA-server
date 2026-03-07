/**
 * 安全存储工具
 * 提供加密的localStorage操作功能
 */
import CryptoJS from 'crypto-js'

// <!-- 
// 审查上下文：
// - 设计意图：为用户敏感信息提供加密存储，防止XSS攻击和数据泄露
// - 已知局限：使用AES加密，密钥存储在前端仍存在一定风险，生产环境建议服务端存储敏感信息
// - 业务背景：保护用户认证信息和个性化设置
// - 测试重点：验证加密解密功能正确性，确保数据完整性
// -->

class SecureStorage {
  private static instance: SecureStorage
  private secretKey: string

  private constructor() {
    const key = import.meta.env.VITE_ENCRYPTION_KEY

    if (!key) {
      if (import.meta.env.DEV) {
        // 开发环境下给一个仅限本地的临时密钥
        this.secretKey = 'dev-only-insecure-key'
        console.warn('[secureStorage] 使用开发环境默认密钥，请勿在生产环境使用。')
      } else {
        throw new Error('生产环境必须配置 VITE_ENCRYPTION_KEY')
      }
    } else {
      this.secretKey = key
    }
  }

  static getInstance(): SecureStorage {
    if (!SecureStorage.instance) {
      SecureStorage.instance = new SecureStorage()
    }
    return SecureStorage.instance
  }

  /**
   * 加密数据
   * @param data 要加密的数据
   * @returns 加密后的字符串
   */
  encryptData(data: any): string {
    try {
      const jsonData = JSON.stringify(data)
      return CryptoJS.AES.encrypt(jsonData, this.secretKey).toString()
    } catch (error) {
      console.error('Encryption failed:', error)
      throw new Error('数据加密失败')
    }
  }

  /**
   * 解密数据
   * @param encryptedData 加密的字符串
   * @returns 解密后的数据
   */
  decryptData(encryptedData: string): any {
    try {
      const bytes = CryptoJS.AES.decrypt(encryptedData, this.secretKey)
      const decryptedData = bytes.toString(CryptoJS.enc.Utf8)
      return JSON.parse(decryptedData)
    } catch (error) {
      console.error('Decryption failed:', error)
      // 如果解密失败，清除损坏的数据
      return null
    }
  }

  /**
   * 安全设置存储项
   * @param key 存储键名
   * @param value 要存储的值
   */
  setItem(key: string, value: any): void {
    try {
      const encryptedValue = this.encryptData(value)
      localStorage.setItem(key, encryptedValue)
    } catch (error) {
      console.error(`Failed to set item ${key}:`, error)
    }
  }

  /**
   * 安全获取存储项
   * @param key 存储键名
   * @returns 解密后的值，如果不存在或解密失败返回null
   */
  getItem(key: string): any {
    try {
      const encryptedValue = localStorage.getItem(key)
      if (!encryptedValue) {
        return null
      }
      return this.decryptData(encryptedValue)
    } catch (error) {
      console.error(`Failed to get item ${key}:`, error)
      // 清除损坏的数据
      localStorage.removeItem(key)
      return null
    }
  }

  /**
   * 移除存储项
   * @param key 存储键名
   */
  removeItem(key: string): void {
    localStorage.removeItem(key)
  }

  /**
   * 清除所有存储项
   */
  clear(): void {
    localStorage.clear()
  }
}

// 导出单例实例
export const secureStorage = SecureStorage.getInstance()

// 便捷方法
export const setSecureItem = (key: string, value: any): void => {
  secureStorage.setItem(key, value)
}

export const getSecureItem = (key: string): any => {
  return secureStorage.getItem(key)
}

export const removeSecureItem = (key: string): void => {
  secureStorage.removeItem(key)
}