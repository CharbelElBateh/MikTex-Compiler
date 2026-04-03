"""High-level package management with caching and filtering."""

from pathlib import Path

from src.core.logging_config import get_logger
from src.packages.miktex_bridge import MiKTeXBridge
from src.packages.package_model import PackageInfo

log = get_logger("packages.manager")


class PackageManager:
    """Manages the cached package list and delegates operations to MiKTeXBridge."""

    def __init__(self, miktex_bin_dir: Path) -> None:
        self._bridge = MiKTeXBridge(miktex_bin_dir)
        self._packages: list[PackageInfo] = []
        self._loaded = False

    @property
    def available(self) -> bool:
        return self._bridge.available

    def load(self) -> list[PackageInfo]:
        """Load/refresh the full package list from mpm."""
        raw = self._bridge.list_packages()
        self._packages = [
            PackageInfo(
                name=p["name"],
                title=p.get("title", ""),
                installed=p.get("installed", False),
            )
            for p in raw
        ]
        self._loaded = True
        log.info("Loaded %d packages", len(self._packages))
        return self._packages

    @property
    def packages(self) -> list[PackageInfo]:
        if not self._loaded:
            self.load()
        return self._packages

    def search(self, query: str) -> list[PackageInfo]:
        """Filter packages by name or title."""
        q = query.lower()
        return [p for p in self.packages if q in p.name.lower() or q in p.title.lower()]

    def installed(self) -> list[PackageInfo]:
        return [p for p in self.packages if p.installed]

    def not_installed(self) -> list[PackageInfo]:
        return [p for p in self.packages if not p.installed]

    def install(self, name: str) -> tuple[bool, str]:
        success, msg = self._bridge.install(name)
        if success:
            for p in self._packages:
                if p.name == name:
                    p.installed = True
                    break
        return success, msg

    def uninstall(self, name: str) -> tuple[bool, str]:
        success, msg = self._bridge.uninstall(name)
        if success:
            for p in self._packages:
                if p.name == name:
                    p.installed = False
                    break
        return success, msg

    def update(self, name: str | None = None) -> tuple[bool, str]:
        return self._bridge.update(name)

    def update_db(self) -> tuple[bool, str]:
        return self._bridge.update_db()

    def refresh_fndb(self) -> tuple[bool, str]:
        return self._bridge.fndb_refresh()
