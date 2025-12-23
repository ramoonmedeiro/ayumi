import subprocess
from colorama import Fore, Style
import os

class SubdomainTakeover:
    def __init__(self, domain_file: str) -> None:
        self.domain_file = domain_file

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

    def run_nuclei_takeover(self) -> None:

        print(Fore.GREEN + "Running: " + Fore.CYAN + "Subdomain Takeover Analysis" + Style.RESET_ALL)

        command = [
            "nuclei",
            "-l", self.domain_file,
            "-t", os.path.expanduser("~/nuclei-templates/http/takeovers"),
            "-severity", "info,low,medium,high,critical",
            "-silent",
            "-o", "nuclei_subdomain_takeover_results_temp.txt"
        ]
        self.run_process(command)
    
    def parse_results(self, output_file: str = None) -> None:

        command = f"cat nuclei_subdomain_takeover_results_temp.txt" + \
        " | " + \
        "sort" + \
        " | " + \
        f"anew {output_file} && rm nuclei_subdomain_takeover_results_temp.txt"

        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def run_all(self, output_file: str = None) -> None:
        self.run_nuclei_takeover()
        if not output_file:
            output_file = "nuclei_subdomain_takeover_results.txt"
        self.parse_results(output_file=output_file)
        print(Fore.MAGENTA + f"\n🌹  Results saved in {output_file}" + Style.RESET_ALL)
