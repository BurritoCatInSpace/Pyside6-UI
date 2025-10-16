import os
import sys
import subprocess
import logging


logger = logging.getLogger(__name__)


def _detect_distribution_id() -> str:
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('ID='):
                    return line.split('=', 1)[1].strip().strip('"').lower()
    except FileNotFoundError:
        pass

    if os.path.exists('/etc/debian_version'):
        return 'debian'
    return 'unknown'


def _run(cmd, env=None, timeout=600):
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env or os.environ.copy(),
            timeout=timeout,
            check=False,
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return '', 'Command timed out', -1
    except Exception as e:
        return '', str(e), -1


def _probe_qt_xcb_in_subprocess() -> tuple:
    python_exe = sys.executable or 'python3'
    code = (
        'import os; os.environ["QT_QPA_PLATFORM"] = "xcb"; '
        'from PySide6.QtWidgets import QApplication; '
        'app = QApplication([]); print("OK")'
    )
    env = os.environ.copy()
    env.setdefault('QT_DEBUG_PLUGINS', '0')
    stdout, stderr, rc = _run([python_exe, '-c', code], env=env, timeout=30)
    ok = (rc == 0 and 'OK' in (stdout or ''))
    return ok, stderr


def _install_qt_xcb_dependencies_debian() -> bool:
    apt_packages = [
        'libxcb-cursor0',
        'libxcb-xinerama0',
        'libxcb-icccm4',
        'libxcb-image0',
        'libxcb-keysyms1',
        'libxcb-render-util0',
        'libxkbcommon-x11-0',
        'qtwayland5',
    ]

    try:
        from app.utils.elevation_linux import run_command_as_admin_interactive as run_command_as_admin
    except Exception:
        def run_command_as_admin(cmd, description=""):
            return subprocess.run(cmd, capture_output=True, text=True)

    env = os.environ.copy()
    env['DEBIAN_FRONTEND'] = 'noninteractive'

    logger.info('Updating apt package lists to prepare Qt dependency installation...')
    result = run_command_as_admin(['apt-get', 'update'])
    if getattr(result, 'returncode', 1) != 0:
        logger.error(f"Failed to update package lists: {getattr(result, 'stderr', '')}")

    install_cmd = ['apt-get', 'install', '-y', '--no-install-recommends'] + apt_packages
    logger.info('Installing missing Qt xcb dependencies via apt...')
    result = run_command_as_admin(['/usr/bin/env', 'DEBIAN_FRONTEND=noninteractive'] + install_cmd)
    if getattr(result, 'returncode', 1) != 0:
        logger.error(f"Failed to install Qt dependencies: {getattr(result, 'stderr', '')}")
        return False
    return True


def ensure_qt_xcb_dependencies_installed() -> bool:
    ok, stderr = _probe_qt_xcb_in_subprocess()
    if ok:
        return True

    logger.warning('Qt xcb platform initialization failed; attempting to install required system libraries...')
    if stderr:
        logger.debug(f"Initial Qt error: {stderr}")

    distro = _detect_distribution_id()
    installed = False
    if distro in ('debian', 'ubuntu', 'linuxmint'):
        installed = _install_qt_xcb_dependencies_debian()
    else:
        logger.error(f"Automatic installation not implemented for distribution '{distro}'. Please install Qt xcb dependencies manually.")
        return False

    if not installed:
        return False

    ok, stderr = _probe_qt_xcb_in_subprocess()
    if not ok and stderr:
        logger.error(f"Qt still failed to initialize xcb after installation: {stderr}")
    return ok


