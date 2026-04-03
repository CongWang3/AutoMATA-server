import asyncio
import itertools
from concurrent.futures import ThreadPoolExecutor

"""
Global concurrency + ordering helpers (in-process).

Constraints (per spec):
- External command waits must go through `run_in_executor(subprocess_executor, ...)`.
- Total concurrent external-script executions across all job types is capped at 4.
"""

# Global gate: training + data-process + analysis combined
# 全局并发信号量：训练 + 数据处理 + 分析 合计 ≤ 4
GLOBAL_TASK_SEM = asyncio.Semaphore(4)

# Dedicated executor for blocking subprocess waits.
# Keep max_workers aligned with GLOBAL_TASK_SEM to avoid hidden queuing.
subprocess_executor = ThreadPoolExecutor(max_workers=4)

# Per-process sequence for WS ordering tie-breaks (no DB migration).
_server_seq = itertools.count(1)


def next_server_seq() -> int:
    return next(_server_seq)

