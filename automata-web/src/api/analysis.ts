/**
 * 数据分析API客户端
 * 提供各种数据分析功能的API调用封装
 */
import { apiClient } from './client'
import type { BaseApiResponse } from './types'

// ==================== 类型定义 ====================

/**
 * 分析任务响应
 */
export interface AnalysisResponse extends BaseApiResponse {
  job_id: string
  status: string
  message: string
  created_at: string
}

/**
 * 分析结果文件信息
 */
export interface AnalysisResultFile {
  filename: string
  format: string
  url: string
}

/**
 * 分析结果响应
 */
export interface AnalysisResultResponse extends BaseApiResponse {
  job_id: string
  status: string
  result_files: AnalysisResultFile[]
  error_message?: string
}

/**
 * 综合分析：继续 GO + KEGG 富集（沿用同一 job_id）
 */
export interface ComprehensiveEnrichmentPayload {
  type_analysis: 'all' | 'up' | 'down'

  go_organism: string
  go_pvalue: number
  go_qvalue: number
  go_plot_type: string
  go_term_num: number
  go_correction: string

  kegg_organism: string
  kegg_pvalue: number
  kegg_qvalue: number
  kegg_plot_type: string
  kegg_term_num: number
  kegg_correction: string
}

/**
 * 分析表单字段选项
 */
export interface AnalysisFieldOption {
  label: string
  value: string | number
}

/**
 * 分析表单字段配置
 */
export interface AnalysisField {
  /** 字段类型 */
  type: 'input' | 'select' | 'radio' | 'number'
  /** FormData 字段名 */
  name: string
  /** 显示标签 */
  label: string
  /** 默认值 */
  defaultValue?: string | number | boolean
  /** select/radio 的选项 */
  options?: AnalysisFieldOption[]
  /** 输入框占位符 */
  placeholder?: string
  /** 是否必填 */
  required?: boolean
  /** 条件显示：布尔值或函数 */
  visible?: boolean | ((formValues: Record<string, any>) => boolean)
  /** 提示文字 */
  tip?: string
  /** 最小值（number类型） */
  min?: number
  /** 最大值（number类型） */
  max?: number
  /** 步进值（number类型） */
  step?: number
}

// ==================== API 客户端类 ====================

export class AnalysisAPI {
  /**
   * 运行 PCA 分析
   * @param formData 表单数据
   */
  static async runPCA(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/pca',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('PCA分析失败:', error)
      throw error
    }
  }

  /**
   * 运行相关性热图分析
   * @param formData 表单数据
   */
  static async runCorrelationHeatmap(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/correlation-heatmap',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('相关性热图分析失败:', error)
      throw error
    }
  }

  /**
   * 运行火山图分析
   * @param formData 表单数据
   */
  static async runVolcano(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/volcano',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('火山图分析失败:', error)
      throw error
    }
  }

  /**
   * 运行韦恩图分析
   * @param formData 表单数据
   */
  static async runVenn(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/venn',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('韦恩图分析失败:', error)
      throw error
    }
  }

  /**
   * 运行基因聚类热图分析
   * @param formData 表单数据
   */
  static async runGeneClusterHeatmap(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/gene-cluster-heatmap',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('基因聚类热图分析失败:', error)
      throw error
    }
  }

  /**
   * 运行哑铃图分析
   * @param formData 表单数据
   */
  static async runDumbbell(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/dumbbell',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('哑铃图分析失败:', error)
      throw error
    }
  }

  /**
   * 运行哑铃柱状图分析
   * @param formData 表单数据
   */
  static async runDumbbellBar(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/dumbbell-bar',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('哑铃柱状图分析失败:', error)
      throw error
    }
  }

  /**
   * 运行 GO 富集分析
   * @param formData 表单数据
   */
  static async runGOEnrichment(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/go-enrichment',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('GO富集分析失败:', error)
      throw error
    }
  }

  /**
   * 运行 KEGG 富集分析
   * @param formData 表单数据
   */
  static async runKEGGEnrichment(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/kegg-enrichment',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('KEGG富集分析失败:', error)
      throw error
    }
  }

  /**
   * 运行 PPI 蛋白互作网络分析
   * @param formData 表单数据
   */
  static async runPPI(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/ppi',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('PPI分析失败:', error)
      throw error
    }
  }

  /**
   * 运行综合分析流程
   * @param formData 表单数据
   */
  static async runComprehensive(formData: FormData): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        '/v1/analysis/comprehensive',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('综合分析失败:', error)
      throw error
    }
  }

  /**
   * 综合分析结果：继续 GO + KEGG 富集
   */
  static async runComprehensiveEnrichment(
    jobId: string,
    payload: ComprehensiveEnrichmentPayload
  ): Promise<AnalysisResponse> {
    try {
      return await apiClient.post<AnalysisResponse>(
        `/v1/analysis/comprehensive/${encodeURIComponent(jobId)}/enrichment`,
        payload
      )
    } catch (error) {
      console.error('综合分析继续富集失败:', error)
      throw error
    }
  }

  /**
   * 获取分析结果
   * @param jobId 任务ID
   */
  static async getResult(jobId: string): Promise<AnalysisResultResponse> {
    try {
      return await apiClient.get<AnalysisResultResponse>(
        `/v1/analysis/result/${jobId}`
      )
    } catch (error) {
      console.error('获取分析结果失败:', error)
      throw error
    }
  }

  /**
   * 获取分析任务状态
   * @param jobId 任务ID
   */
  static async getStatus(jobId: string): Promise<AnalysisResultResponse> {
    try {
      return await apiClient.get<AnalysisResultResponse>(
        `/v1/analysis/status/${jobId}`
      )
    } catch (error) {
      console.error('获取分析状态失败:', error)
      throw error
    }
  }

  /**
   * 生成结果文件下载URL
   * @param jobId 任务ID
   * @param filename 文件名
   */
  static getResultFileUrl(jobId: string, filename: string): string {
    // 使用独立下载服务（端口8001）
    return `http://localhost:8001/analysis-result/${jobId}/${encodeURIComponent(filename)}`
  }

  /**
   * 从主API获取下载链接（包含签名）
   * @param jobId 任务ID
   * @param filename 文件名
   */
  static async getDownloadUrl(jobId: string, filename: string): Promise<string> {
    try {
      const response = await apiClient.get<{ download_url: string }>(
        `/v1/analysis/download-url/${jobId}/${encodeURIComponent(filename)}`
      )
      return response.download_url
    } catch (error) {
      console.error('获取下载链接失败:', error)
      throw error
    }
  }
}

// 默认导出
export default AnalysisAPI
