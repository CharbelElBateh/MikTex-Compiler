"""Low-level wrapper around MiKTeX CLI tools (mpm.exe, initexmf.exe)."""

import re
from pathlib import Path

from src.core.logging_config import get_logger
from src.utils.process_utils import run_miktex_command

log = get_logger("packages.miktex_bridge")


class MiKTeXBridge:
    """Interface to mpm.exe and initexmf.exe for package management."""

    def __init__(self, miktex_bin_dir: Path) -> None:
        self._bin = miktex_bin_dir
        self._mpm = str(miktex_bin_dir / "mpm.exe")
        self._initexmf = str(miktex_bin_dir / "initexmf.exe")

    @property
    def available(self) -> bool:
        return Path(self._mpm).is_file()

    def list_packages(self) -> list[dict]:
        """List all packages via mpm --list.

        Returns list of dicts with keys: name, installed, title.
        """
        result = run_miktex_command(
            [self._mpm, "--list"],
            self._bin,
            timeout=60,
        )
        if result.returncode != 0:
            log.error("mpm --list failed: %s", result.stderr)
            return []

        packages = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            # mpm --list format: "i package_name - Package Title"
            # or "  package_name - Package Title" (not installed)
            match = re.match(r'^(i| )\s+(\S+)\s+-\s+(.*)', line)
            if match:
                packages.append({
                    "name": match.group(2),
                    "installed": match.group(1) == "i",
                    "title": match.group(3).strip(),
                })
        log.debug("Listed %d packages", len(packages))
        return packages

    def package_info(self, name: str) -> dict:
        """Get detailed info about a specific package."""
        result = run_miktex_command(
            [self._mpm, "--print-package-info", name],
            self._bin,
            timeout=30,
        )
        info = {"name": name}
        if result.returncode != 0:
            log.error("mpm --print-package-info %s failed: %s", name, result.stderr)
            return info

        for line in result.stdout.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                info[key] = value
        return info

    def install(self, name: str) -> tuple[bool, str]:
        """Install a package. Returns (success, message)."""
        log.info("Installing package: %s", name)
        result = run_miktex_command(
            [self._mpm, "--install", name],
            self._bin,
            timeout=300,
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        if not success:
            log.error("Install %s failed: %s", name, output)
        return success, output.strip()

    def uninstall(self, name: str) -> tuple[bool, str]:
        """Uninstall a package. Returns (success, message)."""
        log.info("Uninstalling package: %s", name)
        result = run_miktex_command(
            [self._mpm, "--uninstall", name],
            self._bin,
            timeout=120,
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output.strip()

    def update(self, name: str | None = None) -> tuple[bool, str]:
        """Update a specific package or all packages."""
        args = [self._mpm, "--update"]
        if name:
            args.append(name)
        log.info("Updating: %s", name or "all packages")
        result = run_miktex_command(args, self._bin, timeout=600)
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output.strip()

    def update_db(self) -> tuple[bool, str]:
        """Update the MiKTeX package database."""
        log.info("Updating package database")
        result = run_miktex_command(
            [self._mpm, "--update-db"],
            self._bin,
            timeout=120,
        )
        success = result.returncode == 0
        return success, (result.stdout + result.stderr).strip()

    def fndb_refresh(self) -> tuple[bool, str]:
        """Refresh the MiKTeX filename database."""
        log.info("Refreshing FNDB")
        result = run_miktex_command(
            [self._initexmf, "--update-fndb"],
            self._bin,
            timeout=120,
        )
        success = result.returncode == 0
        return success, (result.stdout + result.stderr).strip()
