import os
import subprocess
import pwd
import grp


def is_admin():
    try:
        return os.geteuid() == 0
    except AttributeError:
        try:
            return os.getuid() == 0
        except AttributeError:
            return False


def prompt_for_admin_immediately():
    if is_admin():
        return True

    print("This application requires root privileges to function properly.")

    if check_pkexec_available():
        print("Using pkexec for authentication...")
        try:
            result = subprocess.run(['pkexec', 'true'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Admin privileges obtained successfully via pkexec.")
                return True
            else:
                print("pkexec authentication failed or was cancelled.")
                return False
        except Exception as e:
            print(f"Error with pkexec: {e}")

    if check_sudo_available():
        print("Falling back to sudo for authentication...")
        try:
            result = subprocess.run(['sudo', '-n', 'true'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Admin privileges available via sudo.")
                return True
            else:
                print("Please enter your password when prompted...")
                result = subprocess.run(['sudo', '-v'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Admin privileges obtained successfully via sudo.")
                    return True
                else:
                    print("Failed to obtain admin privileges via sudo.")
                    return False
        except Exception as e:
            print(f"Error obtaining admin privileges via sudo: {e}")
            return False
    else:
        print("Error: Neither pkexec nor sudo is available on this system.")
        print("Please run the application as root manually.")
        return False


def ensure_root_privileges():
    if is_admin():
        return True
    return prompt_for_admin_immediately()


def run_command_as_admin(command, description="This operation"):
    if is_admin():
        return subprocess.run(command, capture_output=True, text=True)

    if check_pkexec_available():
        try:
            pkexec_command = ['pkexec'] + command
            return subprocess.run(pkexec_command, capture_output=True, text=True)
        except Exception as e:
            print(f"pkexec failed, falling back to sudo: {e}")

    if check_sudo_available():
        sudo_command = ['sudo'] + command
        return subprocess.run(sudo_command, capture_output=True, text=True)
    else:
        raise Exception("Neither pkexec nor sudo is available for privilege escalation")


def run_command_as_admin_interactive(command, description="This operation"):
    if is_admin():
        return subprocess.run(command, text=True)

    if check_pkexec_available():
        try:
            pkexec_command = ['pkexec'] + command
            return subprocess.run(pkexec_command, text=True)
        except Exception as e:
            print(f"pkexec failed, falling back to sudo: {e}")

    if check_sudo_available():
        sudo_command = ['sudo'] + command
        return subprocess.run(sudo_command, text=True)
    else:
        raise Exception("Neither pkexec nor sudo is available for privilege escalation")


def check_sudo_available():
    try:
        result = subprocess.run(['which', 'sudo'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_pkexec_available():
    try:
        result = subprocess.run(['which', 'pkexec'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_current_user():
    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except (KeyError, AttributeError):
        return os.getenv('USER', 'unknown')


def get_current_group():
    try:
        return grp.getgrgid(os.getgid()).gr_name
    except (KeyError, AttributeError):
        return os.getenv('GROUP', 'unknown')


def can_elevate():
    if check_pkexec_available():
        return True
    if not check_sudo_available():
        return False
    try:
        result = subprocess.run(['sudo', '-n', 'true'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return True


def prompt_for_elevation(operation_description="this operation"):
    print(f"\n{operation_description} requires root privileges.")
    print("The application will prompt for your password when needed.")
    return True


def get_sudo_status():
    return {
        'is_admin': is_admin(),
        'current_user': get_current_user(),
        'current_group': get_current_group(),
        'sudo_available': check_sudo_available(),
        'pkexec_available': check_pkexec_available(),
        'can_elevate': can_elevate() if (check_sudo_available() or check_pkexec_available()) else False,
    }


