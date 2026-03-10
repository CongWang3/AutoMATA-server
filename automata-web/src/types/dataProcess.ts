/**
 * 数据处理相关的类型定义
 */

/**
 * 数据处理表单数据结构
 */
export interface FormData {
  file: File | null
  nomenclature: string
  dataType: string
  organism: string
  email: string
}

/**
 * 命名方式选项
 */
export interface NomenclatureOption {
  label: string
  value: string
}

/**
 * 物种选项
 */
export interface SpeciesOption {
  label: string
  value: string
}