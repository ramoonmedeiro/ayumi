import subprocess
from colorama import Fore, Style
from src.settings import Settings
import os

class JSParser:
    def __init__(
        self, 
        _input: str, 
        headers=None, 
        cookies=None,
        method="GET",
        verbose=True
    ) -> None:
        self.input = _input
        self.headers = headers
        self.cookies = cookies
        self.method = method
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

    def run_get_js(self, output_file: str = None) -> None:
        if self.verbose:
            print(Fore.GREEN + "Running: " + Fore.CYAN + "getJS" + Style.RESET_ALL)

        if not output_file:
            output_file = "getJS.txt"
        
        if not self._is_file():
            input_type = "-url"
        else:
            input_type = "-input"

        command = [
            'getJS',
            '-complete',
            input_type, self.input,
            '-output', output_file,
            '-method', self.method
        ]

        if self.headers:
            for h in self.headers:
                if h:
                    command.extend(['-header', str(h)])

        if self.cookies:
            for c in self.cookies:
                if c:
                    command.extend(['-header', f'Cookie: {c}'])
        self.run_process(command)
        if self.verbose:
            print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)

    def get_js_from_file(self, output_file: str = "filtered_js.txt") -> None:

        command = f"cat {self.input} | grep -iE '\.js'| grep -iEv '(\.jsp|\.json)' | tee -a {output_file}"

        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if self.verbose:
            print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)
