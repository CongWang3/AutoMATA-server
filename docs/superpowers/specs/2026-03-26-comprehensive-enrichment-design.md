# 综合分析结果弹窗：继续 GO/KEGG 富集（同一 JobID）设计

日期：2026-03-26  
范围：AutoMATA 数据分析前端（`automata-web`）+ 后端（FastAPI `backend`）  
目标：在“综合差异表达分析（comprehensive）”的结果弹窗中，允许用户基于已生成的 `select_{up|down|all}.txt` 继续执行 GO/KEGG 富集分析，并在同一弹窗、同一 `job_id` 下展示参数、进度动图、图片与 txt 结果。

---

## 背景与现状

- 综合差异表达分析完成后，会在：
  - `/xp/www/AutoMATA/download_data/Jobs/<job_id>/result/`
  - 生成差异结果：`select_all.txt`、`select_up.txt`、`select_down.txt`
  - 以及综合分析产物：`volcano.*`、`df_cluster_heatmap.*` 等。
- 旧 PHP 逻辑参考：
  - `all_analysis2.php`：综合差异表达分析
  - `all_analysis_sub*.php`：在综合分析后继续 GO/KEGG
  - `go_enrichment.R / kegg_enrichment.R`：实际绘图与导出 txt 的 R 脚本
- 目前前端结果弹窗组件：
  - `automata-web/src/components/AnalysisResultPanel.vue`
  - 已支持在弹窗内展示综合分析两张图与差异 txt（select_*），也已支持 GO/KEGG 的 txt 表格展示样式（针对独立 GO/KEGG 任务）。

---

## 用户需求（明确）

1. **入口位置**：在综合分析结果弹窗（completed）内容的最下方，新增“继续 GO/KEGG 分析”参数区。
2. **选择差异类型**：用户选择继续分析的数据来源类型：`up/down/all`（映射 `select_up.txt / select_down.txt / select_all.txt`）。
3. **参数填写与提交**：用户填写 GO 与 KEGG 的参数（与旧 PHP 及现有 GO/KEGG 页面一致），点击一个 Submit 按钮后 **GO+KEGG 一起跑**。
4. **等待与回显**：提交后在综合分析结果下方展示：
   - 本次提交的 GO/KEGG 参数（表格行展示）
   - `progress_bar_new.gif` 等待提示
5. **结果展示**：执行完成后在综合分析结果下方展示：
   - GO 图（左预览图 / 右下载 dropdown）
   - KEGG 图（左预览图 / 右下载 dropdown）
   - GO txt 与 KEGG txt（表格解析展示 + 下载）
6. **并发安全**：用户担心 GO/KEGG 同时读取一个 txt 文件导致错误；需要合理处理。

---

## 方案选择（已确认）

### Job 模型
- **沿用同一个综合分析 `job_id`**。
- 不创建新的子任务 `job_id`。
- 继续分析的 GO/KEGG 产物写入同一目录：  
  `/xp/www/AutoMATA/download_data/Jobs/<job_id>/result/`

### 执行策略（解决并发担忧）
- 前端“一个 Submit 按钮”。
- 后端接到请求后在后台任务中 **串行执行**：
  1) GO enrichment  
  2) KEGG enrichment
- 两者均只读读取 `select_*.txt`，不会互相改写输入文件；串行可避免外部下载/缓存/日志覆盖等并发风险。

---

## 后端设计

### 新增 API（推荐）

`POST /api/v1/analysis/comprehensive/{job_id}/enrichment`

#### 请求参数（Form）
- `type_analysis`: `all|up|down`（决定使用哪个 `select_*.txt`）
- GO 参数：
  - `go_pvalue`, `go_qvalue`
  - `go_plot_type`（bubble/barplot/chord/cluster/circle）
  - `go_correction`（BH/BY/holm/hochberg/hommel/bonferroni/fdr/none）
  - `go_term_num`
- KEGG 参数：
  - `kegg_pvalue`, `kegg_qvalue`
  - `kegg_plot_type`（bubble/chord/cluster/circle —— 以当前后端校验为准）
  - `kegg_correction`（同 GO）
  - `kegg_term_num`

#### 行为
1. 校验 job：
   - `job_id` 存在、属于当前用户、`job_type=data_analysis`
   - 综合分析的 `job.result_file` 目录存在
2. 校验输入文件存在：
   - `<result_dir>/select_all.txt` / `select_up.txt` / `select_down.txt`（根据 `type_analysis`）
3. 写入“继续分析参数与状态”：
   - 建议写入 `job.output_params`（JSON）增加字段：
     - `post_enrichment`: { submitted_at, type_analysis, go_params, kegg_params, status, go_status, kegg_status, error_message? }
4. 后台异步任务执行（串行）：
   - GO：执行 `go_enrichment.R`，输入为 `select_*.txt`（通过脚本已有 `type_analysis` 参数机制或明确 `-f type_analysis`）
   - KEGG：执行 `kegg_enrichment.R`
5. 产物命名固定化（避免覆盖）
   - GO：
     - 图：`go_enrichment.{pdf,png,svg,tiff,jpeg,bmp}`
     - txt：`GO_enrichment_result.txt`
   - KEGG：
     - 图：`kegg_enrichment.{pdf,png,svg,tiff,jpeg,bmp}`
     - txt：`KEGG_enrichment_result.txt`
6. WebSocket 推送（可选但推荐）
   - 推送 enrichment 的子状态，避免用户只能靠轮询：
     - `post_go_status=Processing/Completed/Failed`
     - `post_kegg_status=...`
   - 或者复用现有 task_status payload 增加字段（不改变主 job status=Completed）。

#### 错误处理
- 任一阶段失败：
  - 记录到 `post_enrichment.error_message`
  - GO 失败则 KEGG 不再执行（或可配置继续执行；本期默认停止以减少不确定性）
- 不把主 job 从 Completed 改回 Processing，避免综合结果弹窗“回退”为 waiting。

---

## 前端设计（`AnalysisResultPanel.vue`）

### UI 分区（均在综合分析结果 completed 区域下方）
1. **Continue GO/KEGG Enrichment（表单区）**
   - `type_analysis`：radio（all/up/down）
   - GO 参数：与 GOEnrichment 页面一致的字段与枚举
   - KEGG 参数：与 KEGGEnrichment 页面一致
   - Submit（一个按钮，提交后端新 API）
2. **Submitted Params + Waiting（回显与等待）**
   - 用现有 `info-table` 样式展示本次提交的参数行
   - 展示 `progress_bar_new.gif`
3. **Results（结果展示）**
   - GO 图：表格行（左图右下载）
   - KEGG 图：表格行（左图右下载）
   - GO txt：复用现有 txt 表格解析展示 + 下载
   - KEGG txt：同上

### 数据流
- Submit 后：
  - 前端保存“提交参数快照”用于展示
  - 设置本地 `postEnrichmentStatus` 为 waiting/processing
- 状态刷新：
  - 首选 WebSocket enrichment 子状态（若实现）
  - 兜底：复用现有 `getResult(job_id)` 轮询；当 result_files 中出现 `GO_enrichment_result.txt` / `KEGG_enrichment_result.txt` 等即认为完成并展示

---

## 不在本期范围（明确不做）
- 不做 renderer.php 那样的复杂筛选器（zScore/pvalue 过滤等），仅做基础表格展示 + 滚动条 + “加载更多”
- 不改数据库结构（优先写入 job.output_params JSON）

---

## 验收标准
1. 综合分析完成后，弹窗底部出现“继续 GO/KEGG”区块。
2. 用户选择 all/up/down，填写参数，一键提交后：
   - 立即显示参数表 + gif
3. 后端在同一 `<job_id>/result/` 中生成 GO/KEGG 图与 txt。
4. 弹窗下方按既定样式展示：
   - GO/KEGG 图：左预览右下载
   - GO/KEGG txt：表格解析展示 + 下载
5. GO 与 KEGG 执行采用串行，不会出现输出覆盖或日志互相覆盖的问题。

