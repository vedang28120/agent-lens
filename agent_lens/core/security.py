import os
from typing import Optional


def resolve_safe_path(base_dir: str, untrusted_path: str) -> str:
    """
    Strictly resolves and validates that untrusted_path resides within base_dir.
    Guards against directory traversal (../, ..\\), symlink escapes, and null byte injection.
    
    Raises:
        ValueError: If path contains null bytes or is empty.
        PermissionError: If path escapes the base_dir boundary.
    """
    if not untrusted_path or "\x00" in untrusted_path:
        raise ValueError("Invalid path: contains null bytes or empty string.")

    base_real = os.path.realpath(os.path.abspath(base_dir))
    
    # Normalize path separators
    clean_untrusted = untrusted_path.replace("\\", "/").lstrip("/")
    joined_path = os.path.join(base_real, clean_untrusted)
    resolved_target = os.path.realpath(os.path.abspath(joined_path))

    # Verify canonical path is strictly contained within base_dir
    try:
        common = os.path.commonpath([base_real, resolved_target])
    except ValueError:
        # Raised on Windows if paths are on different drive letters
        raise PermissionError(f"Access Denied: Path escapes base root ({untrusted_path})")

    if common != base_real:
        raise PermissionError(f"Access Denied: Path traversal detected ({untrusted_path})")

    return resolved_target


def is_safe_path(base_dir: str, untrusted_path: str) -> bool:
    """Returns True if path is safely contained within base_dir, False otherwise."""
    try:
        resolve_safe_path(base_dir, untrusted_path)
        return True
    except (ValueError, PermissionError):
        return False
