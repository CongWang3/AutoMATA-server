# Comprehensive Analysis Email Notification Design

Date: 2026-03-26  
Scope: Comprehensive differential expression analysis only (`read_counts` + `fpkm`)  
Out of scope: Follow-up GO/KEGG enrichment email flow

## 1. Goal

Enable email notification for Comprehensive Analysis with behavior consistent with other analysis modules:

- User optionally fills `email` in the front-end form.
- If the task completes successfully, backend sends result email.
- If task fails, no email is sent.
- If email sending fails, task result must not be affected.

## 2. Requirements

### Functional

1. Support both comprehensive modes:
   - `data_type = read_counts`
   - `data_type = fpkm`
2. Reuse current email field and API payload conventions used by other analysis pages.
3. Send email only after successful completion and result directory is ready.
4. Define deterministic `result_dir_ready` criteria before sending email:
   - result directory exists
   - required file set is satisfied:
     - for `read_counts`: at least one `volcano.{png|pdf|svg|tiff|jpeg|bmp}` exists
     - for `fpkm`: at least one `volcano.{png|pdf|svg|tiff|jpeg|bmp}` exists
   - `df_cluster_heatmap.*` is optional (may be absent when no differential genes)

### Non-functional

1. Keep changes minimal and low-risk.
2. Maintain existing WebSocket/polling and result dialog behavior.
3. Keep failure isolation:
   - Analysis completion status remains authoritative.
   - Email failure is logged as warning only.

## 3. Current State Summary

- Frontend comprehensive page already uses `AnalysisForm`, which includes a shared email input.
- Other analysis services already send email via `email_service.send_result_email(...)` after successful R execution.
- Comprehensive analysis has separate execution logic and must explicitly apply the same post-success email behavior.

## 4. Selected Approach

Use the same pattern as existing analysis flows:

1. Frontend:
   - Keep `ComprehensiveAnalysis.vue` unchanged in UI pattern (reuse `AnalysisForm` email field).
2. Router:
   - Accept `email` from form data in comprehensive endpoint.
3. Service:
   - Persist `email` in job input params.
   - Pass `email` through comprehensive execution path.
   - On success, call `email_service.send_result_email(...)`.
   - Email send is a best-effort side effect and must not participate in core task completion transaction.
   - Enforce at-most-once send per job (use a persisted marker in job metadata, e.g. `email_sent_at`).
   - On email error, log warning and continue.

This matches existing modules and avoids introducing a separate mail pipeline.

## 5. Data Flow

1. User submits comprehensive task in frontend with optional `email`.
2. `AnalysisForm` appends `email` to `FormData`.
3. `POST /api/v1/analysis/comprehensive` receives `email`.
4. Service stores job and starts async execution.
5. On successful script completion:
   - validate `result_dir_ready`
   - persist job `COMPLETED` and `result_dir`
   - if `email` exists and email is not already sent for this `job_id`, trigger best-effort email send
   - persist `email_sent_at` (or equivalent marker) on successful send
6. On email send exception:
   - log warning only
   - do not downgrade completed task

## 6. Error Handling

- No email provided: skip send silently.
- Analysis failed: no email send.
- Email service failed: warning log only; task remains completed.
- Invalid email format:
  - fixed behavior for this project: keep consistent with existing analysis modules
  - frontend performs format validation (HTML/Element email rule)
  - backend does not reject task by email format; if mail provider rejects recipient, log warning only
- Retry/restart/replay of the same job:
  - do not send duplicate email for same `job_id` when marker already exists

## 7. Validation Plan

1. `read_counts` + valid email:
   - expect completed status
   - expect email received
2. `fpkm` + valid email:
   - expect completed status
   - expect email received
3. `read_counts` and `fpkm` without email:
   - expect completed status
   - expect no email attempts
4. Simulated email failure:
   - expect warning log
   - expect task status still completed
5. Unit test (service):
   - verify `email_service.send_result_email(...)` call count is 0/1 as expected
   - verify send arguments include correct `job_id`, analysis type and `result_dir`
6. Unit test (failure isolation):
   - when email send throws, job remains `COMPLETED`
   - warning log contains `job_id`
7. Integration test (`result_dir_ready`):
   - when ready criteria fail, skip email and log warning
   - task completion status remains `COMPLETED` (email is side effect only)
8. Idempotency test:
   - replay completion path for same `job_id` does not send duplicate email

## 8. Files Expected to Change (Implementation Phase)

- `automata-web/src/views/DataAnalysis/ComprehensiveAnalysis.vue` (only if payload wiring gap exists)
- `backend/api/routers/analysis.py`
- `backend/api/services/analysis_service.py`

