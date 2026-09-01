from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


class BackupService:
    def create_backup(self, db_path: Path, backup_dir: Path) -> Path:
        if not db_path.exists():
            raise FileNotFoundError(f"Datenbank nicht gefunden: {db_path}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = backup_dir / f"tacomex_menu_backup_{timestamp}.db"
        shutil.copy2(db_path, target)
        return target

    def restore_backup(self, backup_path: Path, db_path: Path) -> None:
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup nicht gefunden: {backup_path}")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, db_path)
