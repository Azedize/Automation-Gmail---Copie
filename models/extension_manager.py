import sys
import json
import shutil
from pathlib import Path
import os
import traceback

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from config import Settings
except ImportError as e:
    print(f"❌ Erreur d'importation dans file {__file__}: {e}")
    sys.exit(1)  


class ExtensionManager:

    # =========================
    # PUBLIC API
    # =========================

    



extension_manager = ExtensionManager()
