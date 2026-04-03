from PyQt6.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    """Application-wide event bus using Qt signals for decoupled communication."""

    # ── File events ──
    file_opened = pyqtSignal(str)  # file_path
    file_saved = pyqtSignal(str)  # file_path
    file_closed = pyqtSignal(str)  # file_path
    file_modified = pyqtSignal(str, bool)  # file_path, is_modified
    file_changed_on_disk = pyqtSignal(str)  # file_path (external change)

    # ── Editor events ──
    cursor_moved = pyqtSignal(str, int, int)  # file_path, line, column

    # ── Compilation events ──
    compilation_requested = pyqtSignal()
    compilation_started = pyqtSignal(str)  # engine_name
    compilation_output = pyqtSignal(str)  # output_line
    compilation_finished = pyqtSignal(bool, list)  # success, list[CompilationError]
    compilation_cancelled = pyqtSignal()

    # ── PDF events ──
    pdf_ready = pyqtSignal(str)  # pdf_path — emitted after successful compilation

    # ── SyncTeX events ──
    synctex_forward = pyqtSignal(str, int, int)  # file, line, col -> go to PDF
    synctex_reverse = pyqtSignal(str, int, int)  # file, line, col -> go to source

    # ── Project events ──
    project_opened = pyqtSignal(object)  # Project
    project_closed = pyqtSignal()

    # ── Package events ──
    package_operation_started = pyqtSignal(str, str)  # operation, package_name
    package_operation_finished = pyqtSignal(str, bool, str)  # operation, success, message

    # ── Settings events ──
    settings_changed = pyqtSignal(str, str, object)  # section, key, value
    theme_changed = pyqtSignal(str)  # theme_name

    # ── Plugin events ──
    plugin_loaded = pyqtSignal(str)  # plugin_name
    plugin_unloaded = pyqtSignal(str)  # plugin_name


# Module-level singleton
event_bus = EventBus()
