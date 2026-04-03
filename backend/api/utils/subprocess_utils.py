from __future__ import annotations

import asyncio
import functools
import subprocess
from typing import Optional, Sequence, Union, IO, Any

from api.services.concurrency import subprocess_executor


Cmd = Union[Sequence[str], str]


async def run_subprocess(
    cmd: Cmd,
    *,
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
    stdout: Optional[Union[int, IO[Any]]] = None,
    stderr: Optional[Union[int, IO[Any]]] = None,
    text: bool = True,
    shell: bool = False,
) -> subprocess.CompletedProcess:
    """
    Run subprocess.run(...) in a dedicated executor.

    Hard constraint: do not use asyncio.to_thread for subprocess.run; always use
    the shared dedicated executor to keep capacity predictable.
    """
    loop = asyncio.get_running_loop()
    fn = functools.partial(
        subprocess.run,
        cmd,
        cwd=cwd,
        timeout=timeout,
        stdout=stdout,
        stderr=stderr,
        text=text,
        shell=shell,
    )
    return await loop.run_in_executor(subprocess_executor, fn)

