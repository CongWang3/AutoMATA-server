# Global Task Concurrency Cap (≤4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent FastAPI event-loop starvation from synchronous `subprocess.run`, and cap total concurrent “external-script execution” across training + data-process + analysis to **≤ 4** while keeping queued jobs displayed as `Submitted`.

**Architecture:** Introduce a single in-process global concurrency gate (`GLOBAL_TASK_SEM = Semaphore(4)`) and a dedicated `ThreadPoolExecutor(max_workers=4)` for waiting on external commands. All external command invocations are routed through one helper that uses `loop.run_in_executor(subprocess_executor, subprocess.run, ...)`. Job status updates use atomic terminal-state guards to prevent late updates from reverting terminal states; WS payloads include ordering fields to avoid UI back-jumps.

**Tech Stack:** FastAPI (asyncio), SQLAlchemy Session, Python `subprocess.run`, `concurrent.futures.ThreadPoolExecutor`, existing Jobs/WS infrastructure.

---

## File Structure (what changes where)

**Create:**
- `backend/api/services/concurrency.py`: holds `GLOBAL_TASK_SEM` and `subprocess_executor` (and any small helpers).
- `backend/api/utils/subprocess_utils.py`: a single helper to run `subprocess.run` via `run_in_executor` and return `CompletedProcess`.
- `backend/tests/test_global_concurrency_cap.py`: tests for global cap and terminal-state atomic guard behavior (with a mocked runner).

**Modify:**
- `backend/api/services/training_service.py`: route all training `subprocess.run(...)` calls through helper + `async with GLOBAL_TASK_SEM`; queued status stays `Submitted` until semaphore acquired.
- `backend/api/services/data_process_service.py`: route all Rscript `subprocess.run(...)` calls through helper + global semaphore; queued semantics.
- `backend/api/services/analysis_train_service.py`: route any `subprocess.run(...)` through helper + global semaphore; queued semantics.
- `backend/api/services/analysis_service.py`: identify any external command invocations (if present deeper in file) and route them similarly.
- `backend/api/models/job.py` (if needed): ensure `updated_at` exists/used consistently; consider adding `event_seq` only if already supported (avoid migrations if possible).
- WebSocket payload producers: training/data_process/analysis services where `send_task_status` is called—ensure payload includes `updated_at` (or `event_seq` if exists) consistently.

**No frontend changes required** (queued jobs remain `Submitted`; queuing is shown via `current_step` / message).

---

## Task 1: Add global concurrency + subprocess executor modules

**Files:**
- Create: `backend/api/services/concurrency.py`
- Create: `backend/api/utils/subprocess_utils.py`
- Test: `backend/tests/test_global_concurrency_cap.py` (initial scaffold)

- [ ] **Step 1: Write failing test for “executor helper exists and is awaitable”**

Create a minimal test that imports `run_subprocess` (name TBD) and asserts it can be awaited (using `pytest.mark.asyncio`). Expected initial failure: module/function not found.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_global_concurrency_cap.py -q`  
Expected: ImportError / AttributeError.

- [ ] **Step 3: Implement `backend/api/services/concurrency.py`**

Implement:
- `GLOBAL_TASK_SEM = asyncio.Semaphore(4)`
- `subprocess_executor = ThreadPoolExecutor(max_workers=4)`

Notes:
- Keep it import-safe (no event loop needed at import time).
- Make max_workers configurable via env/settings only if trivial; otherwise hardcode 4 per spec.

- [ ] **Step 4: Implement `backend/api/utils/subprocess_utils.py`**

Implement a single async helper, e.g.:
- `async def run_subprocess(cmd: list[str], *, cwd: str | None, timeout: int | None, stdout=None, stderr=None, text=True, shell=False) -> subprocess.CompletedProcess`
- Internally uses:
  - `loop = asyncio.get_running_loop()`
  - `return await loop.run_in_executor(subprocess_executor, functools.partial(subprocess.run, ...))`

Constraints:
- Thread does **only** `subprocess.run` (no DB/WS work).

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest backend/tests/test_global_concurrency_cap.py -q`  
Expected: PASS (for the minimal helper import/await test).

- [ ] **Step 6: Commit**

```bash
git add backend/api/services/concurrency.py backend/api/utils/subprocess_utils.py backend/tests/test_global_concurrency_cap.py
git commit -m "feat(concurrency): add global semaphore and subprocess executor helper"
```

---

## Task 2: Add atomic terminal-state guard helper for job updates

**Files:**
- Create (or extend): `backend/api/utils/job_update_utils.py` (preferred) OR add helper in `backend/api/services/concurrency.py` (less ideal)
- Modify: `backend/api/services/training_service.py` (first consumer)
- Test: `backend/tests/test_global_concurrency_cap.py`

- [ ] **Step 1: Write failing test for “terminal state cannot be reverted”**

Test idea (no real DB needed if using a lightweight sqlite test DB fixture; otherwise mock Session.execute):
- Arrange a job in terminal state.
- Attempt a non-terminal update through the helper.
- Assert rows_affected == 0 and state unchanged; assert WS sender not called (mock).

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_global_concurrency_cap.py -q`  
Expected: FAIL (helper missing / behavior missing).

- [ ] **Step 3: Implement helper using atomic conditional update**

Requirement from spec:
- Non-terminal updates must be `WHERE status NOT IN (Completed, Failed, Cancelled)`
- If rows_affected == 0, skip WS.

Implementation options:
- SQLAlchemy `query.filter(...).update({...}, synchronize_session=False)`
- Or explicit `update(Job).where(...).values(...)` with `session.execute()`

- [ ] **Step 4: Run tests**

Run: `pytest backend/tests/test_global_concurrency_cap.py -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/api/utils/job_update_utils.py backend/tests/test_global_concurrency_cap.py
git commit -m "feat(jobs): add atomic terminal-state guard for status updates"
```

---

## Task 3: Training module: replace `subprocess.run` + apply global cap + queued semantics

**Files:**
- Modify: `backend/api/services/training_service.py`
- Test: `backend/tests/test_global_concurrency_cap.py` (or dedicated training test file if needed)

- [ ] **Step 1: Write failing test for “training waits behind global semaphore”**

Approach:
- Monkeypatch `run_subprocess` to block on an asyncio Event.
- Acquire 4 slots via spawning 4 fake tasks; the 5th should remain queued (job status stays Submitted + current_step indicates queue) until a slot releases.
- Assert at most 4 concurrent runners invoked.

- [ ] **Step 2: Run test; verify failure**

Run: `pytest backend/tests/test_global_concurrency_cap.py -q`

- [ ] **Step 3: Implement in `training_service.py`**

Changes:
- Import `GLOBAL_TASK_SEM` and `run_subprocess`.
- Right before invoking external training scripts:
  - If semaphore not immediately available, set job `current_step="排队中（等待资源）"` while keeping status `Submitted` (use atomic guard helper).
  - `async with GLOBAL_TASK_SEM:` then transition job -> `Processing`, and run `await run_subprocess(...)`.
- Replace all `subprocess.run` calls in:
  - supervised
  - unsupervised
  - semi-supervised
- Ensure WS payload includes ordering field (`updated_at` at minimum).

- [ ] **Step 4: Run tests**

Run: `pytest backend/tests/test_global_concurrency_cap.py -q`

- [ ] **Step 5: Commit**

```bash
git add backend/api/services/training_service.py backend/tests/test_global_concurrency_cap.py
git commit -m "fix(training): run subprocess in executor and gate with global semaphore"
```

---

## Task 4: Data-process module: replace `subprocess.run` + apply global cap + queued semantics

**Files:**
- Modify: `backend/api/services/data_process_service.py`
- Test: `backend/tests/test_global_concurrency_cap.py`

- [ ] **Step 1: Write failing test for “data-process queued remains Submitted”**
- [ ] **Step 2: Run test; verify failure**
- [ ] **Step 3: Implement: wrap Rscript calls with global semaphore + executor helper**
- [ ] **Step 4: Run tests**
- [ ] **Step 5: Commit**

```bash
git add backend/api/services/data_process_service.py backend/tests/test_global_concurrency_cap.py
git commit -m "fix(data-process): run Rscript in executor and gate with global semaphore"
```

---

## Task 5: Analysis modules: replace `subprocess.run` + apply global cap + queued semantics

**Files:**
- Modify: `backend/api/services/analysis_train_service.py`
- Modify: `backend/api/services/analysis_service.py` (only where external commands exist)
- Test: `backend/tests/test_global_concurrency_cap.py`

- [ ] **Step 1: Write failing test for “analysis obeys global cap”**
- [ ] **Step 2: Run test; verify failure**
- [ ] **Step 3: Implement: route external command waits through executor helper + global semaphore**
- [ ] **Step 4: Run tests**
- [ ] **Step 5: Commit**

```bash
git add backend/api/services/analysis_train_service.py backend/api/services/analysis_service.py backend/tests/test_global_concurrency_cap.py
git commit -m "fix(analysis): run subprocess in executor and gate with global semaphore"
```

---

## Task 6: WS ordering field: ensure payload includes `updated_at` everywhere

**Files:**
- Modify: `backend/api/services/training_service.py`
- Modify: `backend/api/services/data_process_service.py`
- Modify: `backend/api/services/analysis_train_service.py`
- Modify: `backend/api/services/analysis_service.py`

- [ ] **Step 1: Inventory current WS payload fields and pick ordering field**

Prefer `updated_at` (already present on Job model) to avoid migrations.

- [ ] **Step 2: Add `updated_at` to payload consistently**

On each status update, after commit, re-read `job.updated_at` and include it in WS data.

- [ ] **Step 3: Add/adjust test asserting ordering field exists**

Mock WS sender and assert payload includes `updated_at`.

- [ ] **Step 4: Commit**

```bash
git add backend/api/services/training_service.py backend/api/services/data_process_service.py backend/api/services/analysis_train_service.py backend/api/services/analysis_service.py backend/tests/test_global_concurrency_cap.py
git commit -m "chore(ws): include updated_at in task status payloads"
```

---

## Task 7: Verification & docs alignment

**Files:**
- (Optional) Modify: `docs/superpowers/specs/2026-04-02-task-concurrency-and-nonblocking-subprocess-design.md` (only if implementation reveals mismatch)

- [ ] **Step 1: Run backend tests**

Run: `pytest backend/tests -q`  
Expected: PASS.

- [ ] **Step 2: Manual smoke: training running while submitting genome**

Expected: genome job either queues (Submitted + queued step) or starts immediately; it must not wait for training subprocess completion to begin.

- [ ] **Step 3: Commit any tiny doc fixes**

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-02-global-task-concurrency-cap.md`.

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks
2. **Inline Execution** — execute tasks in this session in order with checkpoints

Which approach?

