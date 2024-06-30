import subprocess
from colorama import Fore, Style
from src.settings import Settings


class Crawlers:
    def __init__(self, domains_file: str) -> None:
        self.domains_file = domains_file
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

    def run_katana(self, output_file=None) -> None:

        print(Fore.GREEN + "Running: " + Fore.CYAN + "katana" + Style.RESET_ALL)

        if not output_file:
            output_file = "crawler.txt"

        command = [
            f'katana',
            '-list',
            self.domains_file,
            '-o',
            output_file
        ]

        self.run_process(command)
        print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)

    def run_gau(self) -> None:

        print(Fore.GREEN + "Running: " + Fore.CYAN + "gau" + Style.RESET_ALL)

        command = f"cat {self.domains_file} | gau | tee -a gau.txt"

        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def run_waybackurls(self) -> None:

        print(Fore.GREEN + "Running: " + Fore.CYAN + "waybackurls" + Style.RESET_ALL)

        command = f"cat {self.domains_file} | waybackurls | tee -a waybackurls.txt"

        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def parse_results(self, output_file) -> None:

        command = f"cat gau.txt waybackurls.txt | sort | anew {output_file} && rm gau.txt waybackurls.txt"
        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def run_history(self, output_file=None) -> None:

        self.run_gau()
        self.run_waybackurls()
        if not output_file:
            output_file = "urls-history.txt"
        self.parse_results(output_file)
        print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)

    def run_paramspider(self, output_file=None) -> None:
        command = [
            'paramspider',
            '-l',
            self.domains_file,
            '-p',
            'AYUMI'
        ]

        self.run_process(command)

        if not output_file:
            output_file = "paramspider.txt"

        command = f"cat results/* | sort | anew {output_file} && rm -rf results/"
        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)
