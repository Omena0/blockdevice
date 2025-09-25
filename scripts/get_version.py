from typing import Optional
import subprocess
import re
import os


def _candidate_from_commit_messages(max_commits: int = 200) -> Optional[str]:
    """Return a commit token like '3D' if found in recent commit messages.

    Scans recent commits' first lines for a pattern '<digits><optional-letter> -'.
    """
    try:
        revs = subprocess.check_output(["git", "rev-list", f"--max-count={max_commits}", "HEAD"], text=True)
    except Exception:
        return None
    for rev in revs.splitlines():
        try:
            msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B", rev], text=True)
        except Exception:
            continue
        first = msg.splitlines()[0].strip() if msg else ""
        if "-" in first:
            candidate = first.split("-", 1)[0].strip()
            if re.match(r"^[0-9]+[A-Za-z]?$", candidate):
                return candidate
    return None


def _candidate_from_git_tags() -> Optional[str]:
    """Return a commit token like '3D' if found in recent git tags.

    Looks for the most recent tag reachable from HEAD that matches the pattern.
    """
    try:
        # Get the most recent tag reachable from HEAD
        tag_desc = subprocess.check_output(["git", "describe", "--tags"], text=True).strip()
        # Extract the tag name (before any -N-gXXXXXXX suffix)
        tag_name = tag_desc.split('-')[0]
        if re.match(r"^[0-9]+[A-Za-z]?$", tag_name):
            return tag_name
    except Exception:
        pass
    return None

def _map_candidate_to_version(candidate: str) -> tuple[str, str]:
    """Map a candidate like '3D' to (display_name, numeric_version).

    Rules: digits are major; optional letter maps to minor as A->0, B->1, etc.
    Example: '3A' -> ('3A', '3.0'), '3D' -> ('3D', '3.3').
    """
    m = re.match(r"^([0-9]+)([A-Za-z])?$", candidate)
    if not m:
        # Fall back to a PEP-440 friendly zero version
        return candidate, "0.0.0"
    major = m[1]
    letter = m[2]
    minor = (ord(letter.upper()) - ord('A')) if letter else 0
    # Use a three-segment version (patch=0) for PEP-440 compatibility
    return candidate, f"{major}.{minor}.0"

# Determine release display name and numeric version
RELEASE_DISPLAY_NAME = os.environ.get("RELEASE_DISPLAY_NAME")
BLOCKDEVICE_VERSION = os.environ.get("BLOCKDEVICE_VERSION")

if not (RELEASE_DISPLAY_NAME and BLOCKDEVICE_VERSION):
    if cand := _candidate_from_commit_messages():
        disp, num = _map_candidate_to_version(cand)
        if not RELEASE_DISPLAY_NAME:
            RELEASE_DISPLAY_NAME = disp
        if not BLOCKDEVICE_VERSION:
            BLOCKDEVICE_VERSION = num
    elif cand := _candidate_from_git_tags():
        disp, num = _map_candidate_to_version(cand)
        if not RELEASE_DISPLAY_NAME:
            RELEASE_DISPLAY_NAME = disp
        if not BLOCKDEVICE_VERSION:
            BLOCKDEVICE_VERSION = num

if not RELEASE_DISPLAY_NAME:
    RELEASE_DISPLAY_NAME = "dev"
if not BLOCKDEVICE_VERSION:
    BLOCKDEVICE_VERSION = "0.0.0"


def get_blockdevice_version() -> str:
    """Return the numeric Blockdevice version string (e.g. '3.3')."""
    return BLOCKDEVICE_VERSION


def get_release_display_name() -> str:
    """Return the human release display name (e.g. '3D')."""
    return RELEASE_DISPLAY_NAME
