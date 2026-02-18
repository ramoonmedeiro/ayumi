from src.atk.utils import run_process
from colorama import Fore, Style


class CRLFAtk:
    def __init__(self, domain_file):
        self.domain_file = domain_file

    def run_crlfuzz(self):
        print(Fore.GREEN + "Running: " + Fore.CYAN + "crlfuzz" + Style.RESET_ALL)

        command = [
            'crlfuzz',
            '-l',
            self.domain_file,
            '-o',
            'output-crlfuzz.txt',
            '-s'
        ]

        run_process(command)

    def run_all(self) -> None:
        self.run_crlfuzz()
