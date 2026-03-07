/**
 * 前端安全存储测试
 * 测试加密存储功能的正确性
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { secureStorage } from '@/utils/secureStorage'

describe('Secure Storage Tests', () => {
  beforeEach(() => {
    // 清理localStorage
    localStorage.clear()
  })

  it('should encrypt and decrypt data correctly', () => {
    const testData = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      is_authenticated: true
    }

    // 加密数据
    const encrypted = secureStorage.encryptData(testData)
    expect(encrypted).toBeTypeOf('string')
    expect(encrypted).not.toEqual(JSON.stringify(testData))

    // 解密数据
    const decrypted = secureStorage.decryptData(encrypted)
    expect(decrypted).toEqual(testData)
  })

  it('should handle secure storage operations', () => {
    const testData = { message: 'Hello World', timestamp: Date.now() }

    // 设置安全存储项
    secureStorage.setItem('test-key', testData)

    // 获取安全存储项
    const retrieved = secureStorage.getItem('test-key')
    expect(retrieved).toEqual(testData)

    // 验证localStorage中存储的是加密数据
    const rawStored = localStorage.getItem('test-key')
    expect(rawStored).not.toEqual(JSON.stringify(testData))
  })

  it('should handle invalid data gracefully', () => {
    // 测试解密无效数据
    const result = secureStorage.decryptData('invalid-encrypted-data')
    expect(result).toBeNull()

    // 测试获取不存在的键
    const nonExistent = secureStorage.getItem('non-existent-key')
    expect(nonExistent).toBeNull()
  })

  it('should remove items correctly', () => {
    const testData = { test: 'data' }
    
    secureStorage.setItem('temp-key', testData)
    expect(secureStorage.getItem('temp-key')).toEqual(testData)
    
    secureStorage.removeItem('temp-key')
    expect(secureStorage.getItem('temp-key')).toBeNull()
  })
})