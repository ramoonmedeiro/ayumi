import subprocess
from colorama import Fore, Style
from src.settings import Settings
import os

class NucleiClient:
    def __init__(self, _input: str, verbose=True) -> None:
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

    def run_normal_templates(self, output_file: str = None) -> None:
        if self.verbose:
            print(Fore.GREEN + "Running: " + Fore.CYAN + "nuclei-normal-templates" + Style.RESET_ALL)

        if not output_file:
            output_file = "nuclei-normal-templates-results.txt"
        
        if not self._is_file():
            input_type = "-u"
        else:
            input_type = "-list"

        command = [
            'nuclei',
            input_type, self.input,
            '-t',
            os.path.expanduser("~/nuclei-templates/http/"),
            '-o', output_file
        ]
        self.run_process(command)
        if self.verbose:
            print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)

    def run_custom_templates(self, output_file: str = None) -> None:
        if self.verbose:
            print(Fore.GREEN + "Running: " + Fore.CYAN + "nuclei-custom-templates" + Style.RESET_ALL)

        if not output_file:
            output_file = "nuclei-custom-templates-results.txt"
        
        if not self._is_file():
            input_type = "-u"
        else:
            input_type = "-list"

        command = [
            'nuclei',
            input_type, self.input,
            '-t',
            os.path.expanduser("~/nuclei-templates-do-mal/"),
            '-o', output_file
        ]
        self.run_process(command)
        if self.verbose:
            print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)

