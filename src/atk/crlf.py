from src.atk.utils import run_process
from colorama import Fore, Style
import os

class CRLFAtk:
    def __init__(self, domain_file):
        self.domain_file = domain_file
        self.template_path = os.path.expanduser('~/nuclei-templates-do-mal/cRlf.yaml')
    def run_nuclei_coffin(self):
        print(Fore.GREEN + "Running: " + Fore.CYAN + "crlf-coffin-nuclei" + Style.RESET_ALL)

        command = [
            'nuclei',
            '-l',
            self.domain_file,
            '-t',
            self.template_path,
            '-o',
            'output-nuclei-crlf.txt',
            '-dast',
            '-silent'
        ]

        run_process(command)

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
        self.run_nuclei_coffin()
        self.run_crlfuzz()
