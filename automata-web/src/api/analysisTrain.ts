/**
 * 分析并训练：POST /api/v1/analysis-train/tasks
 */
import { apiClient } from './client'
import type { BaseApiResponse } from './types'

export interface AnalysisTrainSubmitPayload {
  task_name: string
  model_type: string
  parameters: Record<string, unknown>
  dataset_path?: string
  group_info_file_id: string
  analysis: {
    organism: string
    data_type: 'read_counts' | 'fpkm'
    gene_nomenclature: 'symbol' | 'ensembl' | 'gene_id'
    fc: number
    padj: number
    correction: string
  }
  email?: string
}

export interface AnalysisTrainResponse extends BaseApiResponse {
  task_name: string
  model_type: string
  status: string
  job_id: string
  message: string
  created_at: string
  parameters?: Record<string, unknown>
  progress?: number
  current_step?: string
  result_file?: string
  error_message?: string
}

export async function submitAnalysisTrain(
  payload: AnalysisTrainSubmitPayload
): Promise<AnalysisTrainResponse> {
  return apiClient.post<AnalysisTrainResponse>('/v1/analysis-train/tasks', payload)
}

export const analysisTrainApi = { submitAnalysisTrain }
