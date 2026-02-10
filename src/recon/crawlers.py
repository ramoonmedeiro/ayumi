import subprocess
from colorama import Fore, Style
from src.settings import Settings
import os


class Crawlers:
    def __init__(self, _input: str, verbose: bool) -> None:
        self.input = _input
        self.verbose = verbose
    
    def _is_file(self):
        if os.path.isfile(self.input):
            return True
        return False

    def run_process(self, command) -> None:

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                print(f"Error on exec command: {result.stderr}")
                return

        except Exception as e:
            print(f"Error on trying running command: {str(e)}")

    def run_katana(self, output_file=None) -> None:

        if self.verbose:
            print(Fore.GREEN + "Running: " + Fore.CYAN + "katana" + Style.RESET_ALL)

        if not output_file:
            output_file = "crawler.txt"
        if not self._is_file():
            input_type = "-d"
        else:
            input_type = "-list"

        command = [
            f'katana',
            input_type,
            self.input,
            '-o',
            output_file
        ]

        self.run_process(command)
        if self.verbose:
            print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)

    def run_urlfinder(self, output_file=None) -> None:
        if self.verbose:
            print(Fore.GREEN + "Running: " + Fore.CYAN + "Urlfinder" + Style.RESET_ALL)

        if not output_file:
            output_file = "crawler-history.txt"
        
        if not self._is_file():
            input_type = "-d"
        else:
            input_type = "-list"

        command = [
            f'urlfinder',
            input_type,
            self.input,
            '-o',
            output_file,
            '-all'
        ]

        self.run_process(command)
        if self.verbose:
            print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)