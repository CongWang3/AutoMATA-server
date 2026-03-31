export interface TrainingParamRow {
  label: string
  value: string
}

type AnyRecord = Record<string, any>

function safeJsonParse(raw: string): AnyRecord {
  try {
    const v = JSON.parse(raw)
    if (v && typeof v === 'object') return v as AnyRecord
  } catch {
    // ignore
  }
  return {}
}

function normalizeInputParams(inputParams: unknown): AnyRecord {
  if (!inputParams) return {}
  if (typeof inputParams === 'string') return safeJsonParse(inputParams)
  if (typeof inputParams === 'object') return inputParams as AnyRecord
  return {}
}

function getPath(obj: AnyRecord, path: string): any {
  const parts = path.split('.').filter(Boolean)
  let cur: any = obj
  for (const p of parts) {
    if (!cur || typeof cur !== 'object') return undefined
    cur = cur[p]
  }
  return cur
}

function isEmptyValue(v: any): boolean {
  return v === null || v === undefined || v === ''
}

function toDisplayString(v: any): string {
  if (isEmptyValue(v)) return ''
  if (typeof v === 'string') return v
  if (typeof v === 'number' || typeof v === 'boolean') return String(v)
  try {
    return JSON.stringify(v)
  } catch {
    return String(v)
  }
}

function basename(p: string): string {
  const s = String(p || '')
  const parts = s.split(/[\\/]/).filter(Boolean)
  return parts.length ? (parts[parts.length - 1] as string) : s
}

function shouldHideZeroLike(key: string, v: any): boolean {
  // 0 / 0.0 / "0.0" 都视为未启用
  if (v === 0 || v === '0' || v === 0.0 || v === '0.0') {
    return key === 'dropout_rate' || key === 'r_weight'
  }
  return false
}

type FieldSpec = {
  label: string
  paths: string[]
  kind?: 'path'
  key?: string
}

const TRAINING_FIELDS: FieldSpec[] = [
  { label: 'Training Type', paths: ['training_type'] },
  { label: 'Model Type', paths: ['model_type'] },
  { label: 'Strategy', paths: ['parameters.strategy'] },
  { label: 'Split Ratio', paths: ['parameters.split_ratio', 'parameters.ratio'] },
  { label: 'K-Fold', paths: ['parameters.kfold'] },
  { label: 'Epoch', paths: ['parameters.epochs', 'parameters.epoch'] },
  { label: 'Learning Rate', paths: ['parameters.learning_rate', 'parameters.lr'] },
  { label: 'Early Stopping Patience', paths: ['parameters.early_stopping', 'parameters.es', 'parameters.early_stopping_patience'] },
  { label: 'Batch Size', paths: ['parameters.batch_size', 'parameters.bs'] },
  { label: 'Random Seed', paths: ['parameters.seed', 'parameters.random_seed'] },
  { label: 'Label Count', paths: ['parameters.label_count', 'parameters.labels', 'parameters.output_size'] },
  { label: 'Loss Function', paths: ['parameters.loss_function'] },
  { label: 'Optimizer', paths: ['parameters.optimizer_function', 'parameters.optimizer'] },
  { label: 'Feature Selection Method', paths: ['parameters.feature_method'] },
  { label: 'Regularization Method', paths: ['parameters.r_method'], key: 'r_method' },
  { label: 'Regularization Weight/Strength', paths: ['parameters.r_weight'], key: 'r_weight' },
  { label: 'Dropout Rate', paths: ['parameters.dropout_rate'], key: 'dropout_rate' },
  { label: 'Email', paths: ['email', 'parameters.email'] },
]

const MODEL_USE_FIELDS: FieldSpec[] = [
  { label: 'Model Type', paths: ['model_type'] },
  { label: 'Test Dataset', paths: ['test_data_path'], kind: 'path' },
  { label: 'Model File', paths: ['model_path', 'un_semi_model_path'], kind: 'path' },
  { label: 'SOM Model File', paths: ['som_model_path'], kind: 'path' },
  { label: 'Encoder Model File', paths: ['encoder_path'], kind: 'path' },
  { label: 'Classifier Model File', paths: ['classifier_path'], kind: 'path' },
  { label: 'Scaler File', paths: ['scaler_path'], kind: 'path' },
  { label: 'Email', paths: ['email', 'parameters.email'] },
]

function buildRowsFromSpecs(root: AnyRecord, specs: FieldSpec[], opts: { isSom: boolean; hideSomReg: boolean }): TrainingParamRow[] {
  const rows: TrainingParamRow[] = []

  for (const spec of specs) {
    if (opts.hideSomReg && opts.isSom) {
      if (spec.key === 'r_method' || spec.key === 'r_weight' || spec.key === 'dropout_rate') {
        continue
      }
    }

    let raw: any = undefined
    for (const p of spec.paths) {
      const v = getPath(root, p)
      if (!isEmptyValue(v)) {
        raw = v
        break
      }
    }

    if (isEmptyValue(raw)) continue
    if (spec.key && shouldHideZeroLike(spec.key, raw)) continue

    let value: string
    if (
      typeof raw === 'object' &&
      raw &&
      'train' in raw &&
      'validation' in raw &&
      'test' in raw
    ) {
      // split_ratio 常见结构：{train, validation, test}
      value = `train=${(raw as any).train}, validation=${(raw as any).validation}, test=${(raw as any).test}`
    } else {
      value = toDisplayString(raw)
    }
    if (!value) continue

    if (spec.kind === 'path') value = basename(value)

    rows.push({ label: spec.label, value })
  }

  return rows
}

function buildExtraParamRows(
  root: AnyRecord,
  alreadyShownLabels: Set<string>,
  coveredParamKeys: Set<string>,
  opts: { isSom: boolean; hideSomReg: boolean }
): TrainingParamRow[] {
  const extra: TrainingParamRow[] = []
  const params: AnyRecord = (root && typeof root === 'object' && root.parameters && typeof root.parameters === 'object')
    ? (root.parameters as AnyRecord)
    : {}

  const hiddenKeys = new Set(['task_name', 'dataset_path'])
  const skipSomKeys = new Set(['r_method', 'r_weight', 'dropout_rate'])

  const keys = Object.keys(params).sort()
  for (const k of keys) {
    if (hiddenKeys.has(k)) continue
    if (coveredParamKeys.has(k)) continue
    if (opts.hideSomReg && opts.isSom && skipSomKeys.has(k)) continue
    const raw = params[k]
    if (isEmptyValue(raw)) continue
    if (shouldHideZeroLike(k, raw)) continue

    // 避免与已展示字段重复（按 label 粗略去重）
    const label = k
    if (alreadyShownLabels.has(label.toLowerCase())) continue

    let value: string
    if (typeof raw === 'object' && raw && 'train' in raw && 'validation' in raw && 'test' in raw) {
      // split_ratio 常见结构：{train, validation, test}
      value = `train=${raw.train}, validation=${raw.validation}, test=${raw.test}`
    } else {
      value = toDisplayString(raw)
    }
    if (!value) continue
    extra.push({ label, value })
  }

  // email 顶层可能不在 parameters
  const topEmail = root?.email
  if (!isEmptyValue(topEmail) && !alreadyShownLabels.has('email')) {
    extra.push({ label: 'email', value: String(topEmail) })
  }

  return extra
}

/**
 * 从 UnifiedJob.input_params 提取“参数行”（不含 JobID 行与最终状态/下载行）
 * - inputParams 可能是 object 或 string；string 会尝试 JSON.parse，失败则视为 {}
 * - 仅展示实际提交/有效参数；固定顺序按 spec 映射表输出
 */
export function buildTrainingResultParamRows(inputParams: unknown): TrainingParamRow[] {
  const root = normalizeInputParams(inputParams)
  const modelType = String(root.model_type || '').toLowerCase()
  const isSom = modelType === 'som'

  const isModelUse = !isEmptyValue(root.test_data_path) ||
    !isEmptyValue(root.model_path) ||
    !isEmptyValue(root.som_model_path) ||
    !isEmptyValue(root.encoder_path) ||
    !isEmptyValue(root.classifier_path) ||
    !isEmptyValue(root.scaler_path) ||
    !isEmptyValue(root.un_semi_model_path)

  if (isModelUse) {
    // spec: SOM 仅展示 som_model_path（不展示 winmap 字段）；此处仅按映射表输出
    const base = buildRowsFromSpecs(root, MODEL_USE_FIELDS, { isSom, hideSomReg: false })
    const shown = new Set(base.map((r) => String(r.label || '').toLowerCase()))
    const covered = new Set<string>([
      // model use 常见参数 key
      'model_type',
      'test_data_path',
      'model_path',
      'som_model_path',
      'encoder_path',
      'classifier_path',
      'scaler_path',
      'un_semi_model_path',
      'email',
    ])
    const extra = buildExtraParamRows(root, shown, covered, { isSom, hideSomReg: false })
    return [...base, ...extra]
  }

  const base = buildRowsFromSpecs(root, TRAINING_FIELDS, { isSom, hideSomReg: true })
  const shown = new Set(base.map((r) => String(r.label || '').toLowerCase()))
  const covered = new Set<string>([
    // training 常见参数 key（用于避免重复展示）
    'strategy',
    'split_ratio',
    'ratio',
    'kfold',
    'epochs',
    'epoch',
    'learning_rate',
    'lr',
    'early_stopping',
    'es',
    'early_stopping_patience',
    'batch_size',
    'bs',
    'seed',
    'random_seed',
    'label_count',
    'labels',
    'output_size',
    'loss_function',
    'optimizer_function',
    'optimizer',
    'feature_method',
    'r_method',
    'r_weight',
    'dropout_rate',
    'email',
    // 文件 id 在 parameters 里也可能出现，避免和其他字段重复刷屏
    'train_dataset_file_id',
    'validation_dataset_file_id',
    'test_dataset_file_id',
    'kfold_train_dataset_file_id',
    'kfold_test_dataset_file_id',
  ])
  const extra = buildExtraParamRows(root, shown, covered, { isSom, hideSomReg: true })
  return [...base, ...extra]
}

