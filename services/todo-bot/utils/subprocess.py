"""
Subprocess utility functions
"""

import subprocess
import logging
from typing import Optional, List, Dict, Union

logger = logging.getLogger(__name__)


def run_command(
    cmd: Union[List[str], str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = 300,
    check: bool = True,
    shell: bool = False
) -> subprocess.CompletedProcess:
    """
    Execute a shell command using subprocess.run with sensible defaults.

    Args:
        cmd: Command as a list (e.g., ['git', 'status']) or string (when shell=True)
        cwd: Working directory for the command
        env: Environment variables (merged with current env)
        timeout: Command timeout in seconds (default: 300)
        check: Raise exception if command fails (default: True)
        shell: Run command through shell (required for pipes, redirects, etc.)

    Returns:
        CompletedProcess instance with returncode, stdout, stderr

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
        subprocess.TimeoutExpired: If command exceeds timeout

    Examples:
        >>> # Safe mode (list)
        >>> result = run_command(['echo', 'hello'])
        >>> print(result.stdout)
        'hello'

        >>> # Shell mode (for pipes, etc.)
        >>> result = run_command('echo "hello" | grep hello', shell=True)
        >>> print(result.stdout)
        'hello'
    """
    # Format command for logging
    if isinstance(cmd, list):
        cmd_str = ' '.join(cmd)
    else:
        cmd_str = cmd

    logger.info(f"Running command: {cmd_str}")
    if shell:
        logger.warning("Running command with shell=True - ensure input is trusted")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
            shell=shell
        )

        logger.debug(f"Command completed with return code: {result.returncode}")
        if result.stdout:
            logger.debug(f"stdout: {result.stdout.strip()}")
        if result.stderr:
            logger.debug(f"stderr: {result.stderr.strip()}")

        return result

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise

    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds")
        raise
