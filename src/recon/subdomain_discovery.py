import subprocess
from colorama import Fore, Style
from src.settings import Settings


class SubdomainDiscovery:
    def __init__(self, domain_file: str) -> None:
        self.domain_file = domain_file
        self.PATH_GO = Settings.PATH_GO.value

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

        print(Fore.GREEN + "Running: " + Fore.CYAN + "subfinder" + Style.RESET_ALL)

        command = [
            f'{self.PATH_GO}/subfinder',
            '-dL',
            self.domain_file,
            '-silent',
            '-all',
            '-o',
            'temp-subfinder.txt'
        ]

        self.run_process(command)

    def run_assetfinder(self) -> None:

        print(Fore.GREEN + "Running: " + Fore.CYAN + "assetfinder" + Style.RESET_ALL)

        command = f"cat {self.domain_file} | xargs -I@ sh -c 'assetfinder -subs-only @  | tee -a temp-assetfinder.txt'"
        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def run_findomain(self) -> None:

        print(Fore.GREEN + "Running: " + Fore.CYAN + "findomain" + Style.RESET_ALL)

        command = f"cat {self.domain_file} | xargs -I@ sh -c 'findomain -t @ -q | tee -a temp-findomain.txt'"

        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def parse_results(self, output_file: str) -> None:

        command = f"cat temp-subfinder.txt temp-assetfinder.txt temp-findomain.txt crt.txt | sort | {self.PATH_GO}/anew {output_file} && rm temp-subfinder.txt temp-assetfinder.txt temp-findomain.txt crt.txt"

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
        self.run_findomain()
        if not output_file:
            output_file = "subs.txt"
        self.parse_results(output_file=output_file)
        print(Fore.MAGENTA + f"\n🪷  Results saved in {output_file}" + Style.RESET_ALL)
