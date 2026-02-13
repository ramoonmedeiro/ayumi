"""
Ayumi - Background process management.

Permite executar comandos em background de forma que sobrevivam
ao fechamento da sessao SSH/terminal (via setsid/start_new_session).
"""

import os
import sys
import signal
import subprocess
import glob
from datetime import datetime

from colorama import Fore, Style

# Data directory for Ayumi background management
DATA_DIR = os.path.expanduser("~/.ayumi")


def _get_dirs() -> tuple:
    """Return (log_dir, pid_dir) and ensure they exist."""
    log_dir = os.path.join(DATA_DIR, "logs")
    pid_dir = os.path.join(DATA_DIR, "bg")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(pid_dir, exist_ok=True)
    return log_dir, pid_dir


def _make_label(args) -> str:
    """
    Generate a label from the command arguments.
    e.g.: 'recon -ds example.com' -> 'recon_ds'
    """
    parts = []
    if hasattr(args, 'command') and args.command:
        parts.append(args.command)

    # Try to extract the main action flag
    args_dict = vars(args) if hasattr(args, '__dict__') else {}
    for key, val in args_dict.items():
        if key in ('command', 'verbose', 'bg', 'cookie', 'header', 'method', 'o'):
            continue
        if val and val is not True:
            parts.append(key.replace('_', '').replace('-', ''))
            break

    return "_".join(parts) if parts else "ayumi"


def run_in_background(args=None) -> None:
    """
    Re-execute the current command as a fully detached background process.

    - Removes --bg from sys.argv
    - Launches with start_new_session=True (setsid) so the process
      survives terminal/SSH disconnect
    - Redirects stdout+stderr to a timestamped log file
    - Saves PID to a pidfile
    - Exits the current (parent) process immediately
    """
    log_dir, pid_dir = _get_dirs()

    # Build command without --bg
    argv = [a for a in sys.argv if a != "--bg"]

    # Generate label
    label = _make_label(args) if args else "ayumi"

    # Timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{label}_{timestamp}.log")
    pid_file = os.path.join(pid_dir, f"{label}.pid")

    # Open log file for the child process
    log_fd = open(log_file, "w")

    # Launch detached process
    proc = subprocess.Popen(
        [sys.executable] + argv,
        stdout=log_fd,
        stderr=subprocess.STDOUT,
        start_new_session=True,  # setsid - sobrevive ao SIGHUP
        close_fds=True,
        cwd=os.getcwd(),
    )

    # Save PID
    with open(pid_file, "w") as f:
        f.write(str(proc.pid))

    print(f"\n{Fore.GREEN}Processo iniciado em background!{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}Label:{Style.RESET_ALL}    {label}")
    print(f"  {Fore.CYAN}PID:{Style.RESET_ALL}      {proc.pid}")
    print(f"  {Fore.CYAN}Log:{Style.RESET_ALL}      {log_file}")
    print(f"  {Fore.CYAN}PID file:{Style.RESET_ALL} {pid_file}")
    print(f"\n{Fore.WHITE}Pode desconectar do SSH tranquilo. Use 'python3 ayumi.py bg status' para verificar.{Style.RESET_ALL}")

    sys.exit(0)


def _is_process_alive(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _read_pid_file(pid_file: str):
    """Read PID from a pidfile, return None if invalid."""
    try:
        with open(pid_file, "r") as f:
            return int(f.read().strip())
    except (ValueError, FileNotFoundError, OSError):
        return None


def _get_latest_log(log_dir: str, label: str):
    """Find the most recent log file for a given label."""
    pattern = os.path.join(log_dir, f"{label}_*.log")
    files = sorted(glob.glob(pattern), reverse=True)
    return files[0] if files else None


def get_bg_status() -> list:
    """
    List all background processes and their status.
    Returns list of dicts with keys: label, pid, alive, pid_file, log_file
    """
    log_dir, pid_dir = _get_dirs()
    results = []

    if not os.path.isdir(pid_dir):
        return results

    for pid_file in sorted(glob.glob(os.path.join(pid_dir, "*.pid"))):
        label = os.path.basename(pid_file).replace(".pid", "")
        pid = _read_pid_file(pid_file)

        if pid is None:
            continue

        alive = _is_process_alive(pid)
        log_file = _get_latest_log(log_dir, label)

        results.append({
            "label": label,
            "pid": pid,
            "alive": alive,
            "pid_file": pid_file,
            "log_file": log_file,
        })

    return results


def print_bg_status() -> None:
    """Print status of background processes."""
    statuses = get_bg_status()

    if not statuses:
        print(f"{Fore.YELLOW}Nenhum processo background registrado.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}{'Label':<20} {'PID':>8} {'Status':<12} Log{Style.RESET_ALL}")
    print("-" * 80)

    for s in statuses:
        if s["alive"]:
            status_text = f"{Fore.GREEN}RODANDO{Style.RESET_ALL}"
        else:
            status_text = f"{Fore.RED}PARADO{Style.RESET_ALL} "

        log_display = s["log_file"] or "-"
        print(f"  {s['label']:<18} {s['pid']:>8} {status_text}  {log_display}")

    dead = [s for s in statuses if not s["alive"]]
    if dead:
        print(f"\n{Fore.WHITE}Dica: {len(dead)} processo(s) parado(s). Use 'bg stop --cleanup' para limpar.{Style.RESET_ALL}")


def tail_bg_log(label: str = None, lines: int = 50) -> None:
    """Show the last N lines of a background process log."""
    log_dir, _ = _get_dirs()

    if label:
        log_file = _get_latest_log(log_dir, label)
    else:
        # Get most recent log overall
        all_logs = sorted(glob.glob(os.path.join(log_dir, "*.log")), reverse=True)
        log_file = all_logs[0] if all_logs else None

    if not log_file or not os.path.isfile(log_file):
        suffix = f" para '{label}'" if label else ""
        print(f"{Fore.RED}Nenhum log encontrado{suffix}.{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}Log:{Style.RESET_ALL} {log_file}")
    print(f"{Fore.CYAN}Ultimas {lines} linhas:{Style.RESET_ALL}\n")

    try:
        with open(log_file, "r", errors="replace") as f:
            all_lines = f.readlines()
            tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
            for line in tail:
                print(line.rstrip())
    except OSError as e:
        print(f"{Fore.RED}Erro ao ler log: {e}{Style.RESET_ALL}")


def stop_bg_process(label: str = None, cleanup_dead: bool = False) -> None:
    """
    Stop a background process by label, or cleanup all dead pidfiles.
    Sends SIGTERM first, then SIGKILL if needed.
    """
    _, pid_dir = _get_dirs()

    if cleanup_dead:
        statuses = get_bg_status()
        cleaned = 0
        for s in statuses:
            if not s["alive"]:
                try:
                    os.unlink(s["pid_file"])
                    cleaned += 1
                except OSError:
                    pass
        print(f"{Fore.GREEN}{cleaned} pidfile(s) de processos mortos removido(s).{Style.RESET_ALL}")
        return

    if not label:
        print(f"{Fore.RED}Especifique o label do processo (--label).{Style.RESET_ALL}")
        return

    pid_file = os.path.join(pid_dir, f"{label}.pid")
    pid = _read_pid_file(pid_file)

    if pid is None:
        print(f"{Fore.RED}Nenhum processo encontrado com label '{label}'.{Style.RESET_ALL}")
        return

    if not _is_process_alive(pid):
        print(f"{Fore.YELLOW}Processo '{label}' (PID {pid}) ja esta parado.{Style.RESET_ALL}")
        try:
            os.unlink(pid_file)
        except OSError:
            pass
        return

    # Send SIGTERM
    print(f"{Fore.CYAN}Enviando SIGTERM para '{label}' (PID {pid})...{Style.RESET_ALL}")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        print(f"{Fore.YELLOW}Processo ja finalizou.{Style.RESET_ALL}")
        try:
            os.unlink(pid_file)
        except OSError:
            pass
        return

    # Wait a bit and check
    import time
    time.sleep(2)

    if _is_process_alive(pid):
        print(f"{Fore.YELLOW}Processo ainda vivo, enviando SIGKILL...{Style.RESET_ALL}")
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    # Cleanup pidfile
    try:
        os.unlink(pid_file)
    except OSError:
        pass

    print(f"{Fore.GREEN}Processo '{label}' (PID {pid}) finalizado.{Style.RESET_ALL}")
