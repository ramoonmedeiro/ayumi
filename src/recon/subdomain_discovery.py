import subprocess
from colorama import Fore, Style
from src.settings import Settings
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


class SubdomainDiscovery:
    def __init__(self, _input: str, verbose: bool = True) -> None:
        self.input = _input
        self.verbose = verbose
        self.chaos_api_key = os.getenv("CHAOS_API_KEY")
    
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

    def run_subfinder(self) -> None:
        if self.verbose:
            print(Fore.GREEN + "Running: " + Fore.CYAN + "subfinder" + Style.RESET_ALL)
        
        if not self._is_file():
            input_type = "-d"
        else:
            input_type = "-dL"

        command = [
            'subfinder',
            input_type,
            self.input,
            '-silent',
            '-all',
            '-o',
            'temp-subfinder.txt'
        ]

        self.run_process(command)

    def run_assetfinder(self) -> None:

        if self.verbose:
            print(Fore.GREEN + "Running: " + Fore.CYAN + "assetfinder" + Style.RESET_ALL)
        if not self._is_file():
            input_type = f"echo {self.input}"
        else:
            input_type = f"cat {self.input}"

        command = f"{input_type} | xargs -I@ sh -c 'assetfinder -subs-only @  | tee -a temp-assetfinder.txt'"
        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def run_chaos(self) -> None:
        if self.verbose:    
            print(Fore.GREEN + "Running: " + Fore.CYAN + "chaos" + Style.RESET_ALL)
        if not self._is_file():
            input_type = "-d"
        else:
            input_type = "-dL"

        command = [
            'chaos',
            input_type,
            self.input,
            '-key',
            self.chaos_api_key,
            '-o',
            'temp-chaos.txt'
    ]

        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def run_crtsh(self) -> None:
        if self.verbose:
            print(Fore.GREEN + "Running: " + Fore.CYAN + "crt.sh" + Style.RESET_ALL)
        if not self._is_file():
            input_type = f"echo {self.input}"
        else:
            input_type = f"cat {self.input}"

        command = f"{input_type} | xargs -I@ -sh c 'curl -s \"https://crt.sh/?q=%25.@&output=json\"" + \
            " | jq -r '.[].name_value' | sed 's/\\*\\.//g' | anew temp-crtsh.txt'"

        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def parse_results(self, output_file: str) -> None:

        command = f"cat temp-subfinder.txt temp-assetfinder.txt temp-chaos.txt temp-crtsh.txt" + \
        " | " + \
        "sort" + \
        " | " + \
        f"anew {output_file} && rm temp-subfinder.txt temp-assetfinder.txt chaos.txt temp-crtsh.txt"

        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def run_all(self, output_file: str = None) -> None:
        self.run_subfinder()
        self.run_assetfinder()
        self.run_chaos()
        self.run_crtsh()
        if not output_file:
            output_file = "subs.txt"
        self.parse_results(output_file=output_file)
        if self.verbose:
            print(Fore.MAGENTA + f"\n🪷  Results saved in {output_file}" + Style.RESET_ALL)
