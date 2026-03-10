/**
 * DataProcessAPI 单元测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { DataProcessAPI } from '@/api/data-process'
import { apiClient } from '@/api/client'

// Mock API client
vi.mock('@/api/client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

describe('DataProcessAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('processGenome', () => {
    it('应该正确调用基因组处理API', async () => {
      const mockResponse = {
        job_id: 'test123',
        status: 'submitted',
        message: '任务已提交',
        created_at: '2024-01-01T00:00:00Z'
      }

      ;(apiClient.post as any).mockResolvedValue({ data: mockResponse })

      const formData = new FormData()
      formData.append('file', new File(['content'], 'test.txt'))
      formData.append('gene_nomenclature', 'GeneID')
      formData.append('data_type', 'FPKM')
      formData.append('organism', 'homo_sapiens')

      const result = await DataProcessAPI.processGenome(formData)

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/data-process/genome',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
      expect(result).toEqual(mockResponse)
    })

    it('应该处理API错误', async () => {
      const errorMessage = '文件格式不支持'
      ;(apiClient.post as any).mockRejectedValue(new Error(errorMessage))

      const formData = new FormData()
      formData.append('file', new File(['content'], 'test.txt'))

      await expect(DataProcessAPI.processGenome(formData)).rejects.toThrow(errorMessage)
      expect(console.error).toHaveBeenCalledWith('基因组数据处理失败:', expect.any(Error))
    })
  })

  describe('processTranscriptome', () => {
    it('应该正确调用转录组处理API', async () => {
      const mockResponse = {
        job_id: 'test456',
        status: 'submitted',
        message: '任务已提交',
        created_at: '2024-01-01T00:00:00Z'
      }

      ;(apiClient.post as any).mockResolvedValue({ data: mockResponse })

      const formData = new FormData()
      formData.append('file', new File(['content'], 'test.txt'))
      formData.append('mrna_nomenclature', 'Refseq')
      formData.append('data_type', 'TPM')
      formData.append('organism', 'mus_musculus')

      const result = await DataProcessAPI.processTranscriptome(formData)

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/data-process/transcriptome',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getProcessStatus', () => {
    it('应该正确查询处理状态', async () => {
      const jobId = 'test123'
      const mockResponse = {
        job_id: jobId,
        status: 'finished',
        progress: 100
      }

      ;(apiClient.get as any).mockResolvedValue({ data: mockResponse })

      const result = await DataProcessAPI.getProcessStatus(jobId)

      expect(apiClient.get).toHaveBeenCalledWith(`/api/v1/data-process/status/${jobId}`)
      expect(result).toEqual(mockResponse)
    })

    it('应该处理状态查询错误', async () => {
      const jobId = 'invalid_job'
      const errorMessage = '任务不存在'
      ;(apiClient.get as any).mockRejectedValue(new Error(errorMessage))

      await expect(DataProcessAPI.getProcessStatus(jobId)).rejects.toThrow(errorMessage)
      expect(console.error).toHaveBeenCalledWith('查询处理状态失败:', expect.any(Error))
    })
  })
})