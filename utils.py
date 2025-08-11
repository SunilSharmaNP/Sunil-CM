# utils.py

import os
import uuid

def make_unique_filename(prefix, ext="mp4"):
    """Return a unique filename for a temp video."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"

def ensure_folder(path):
    """Make sure a folder exists."""
    if not os.path.exists(path):
        os.makedirs(path)
