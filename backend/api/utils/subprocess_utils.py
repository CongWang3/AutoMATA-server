from __future__ import annotations

import asyncio
import functools
import os
import subprocess
from typing import Any, Dict, IO, Optional, Sequence, Union

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
    env: Optional[Dict[str, str]] = None,
    encoding: Optional[str] = None,
    errors: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """
    Run subprocess.run(...) in a dedicated executor.

    Hard constraint: do not use asyncio.to_thread for subprocess.run; always use
    the shared dedicated executor to keep capacity predictable.

    If env is set, it is merged onto os.environ (values coerced to str) so the child
    inherits the rest of the process environment.
    """
    loop = asyncio.get_running_loop()
    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "timeout": timeout,
        "stdout": stdout,
        "stderr": stderr,
        "text": text,
        "shell": shell,
    }
    if encoding is not None:
        kwargs["encoding"] = encoding
    if errors is not None:
        kwargs["errors"] = errors
    if env is not None:
        merged = os.environ.copy()
        merged.update({k: str(v) for k, v in env.items()})
        kwargs["env"] = merged
    fn = functools.partial(subprocess.run, cmd, **kwargs)
    return await loop.run_in_executor(subprocess_executor, fn)

