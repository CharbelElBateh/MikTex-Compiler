class MiktexCompilerError(Exception):
    """Base exception for all application errors."""


class MiKTeXNotFoundError(MiktexCompilerError):
    """MiKTeX installation could not be located."""


class CompilationError(MiktexCompilerError):
    """LaTeX compilation failed."""


class ProjectError(MiktexCompilerError):
    """Project loading or configuration error."""


class ProjectNotFoundError(ProjectError):
    """Project directory or config file does not exist."""


class SettingsError(MiktexCompilerError):
    """Settings read/write error."""


class PackageOperationError(MiktexCompilerError):
    """MiKTeX package install/uninstall/update failed."""


class PluginError(MiktexCompilerError):
    """Plugin loading or activation error."""
