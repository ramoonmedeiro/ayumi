import subprocess
from colorama import Fore, Style
from src.settings import Settings

class JSParser:
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

    def run_get_js(self, output_file=None) -> None:

        print(Fore.GREEN + "Running: " + Fore.CYAN + "getJS" + Style.RESET_ALL)

        if not output_file:
            output_file = "getJS.txt"

        command = [
            f'{self.PATH_GO}/getJS',
            '--complete',
            '--input',
            self.domains_file,
            '--output',
            output_file
        ]

        self.run_process(command)
        print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)

    def get_js_from_file(self, output_file=None) -> None:

        if not output_file:
            output_file = "filtered_js.txt"

        command = f"cat {self.domains_file} | grep -iE '\.js'| grep -iEv '(\.jsp|\.json)' | tee -a {output_file}"

        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(Fore.MAGENTA + f"Results saved in {output_file}" + Style.RESET_ALL)
