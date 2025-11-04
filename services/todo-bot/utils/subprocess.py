"""
Subprocess utility functions
"""

import subprocess
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


def run_command(
    cmd: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = 300,
    check: bool = True
) -> subprocess.CompletedProcess:
    """
    Execute a shell command using subprocess.run with sensible defaults.

    Args:
        cmd: Command and arguments as a list (e.g., ['git', 'status'])
        cwd: Working directory for the command
        env: Environment variables (merged with current env)
        timeout: Command timeout in seconds (default: 300)
        check: Raise exception if command fails (default: True)

    Returns:
        CompletedProcess instance with returncode, stdout, stderr

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
        subprocess.TimeoutExpired: If command exceeds timeout

    Example:
        >>> result = run_command(['echo', 'hello'])
        >>> print(result.stdout)
        'hello'
    """
    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check
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
