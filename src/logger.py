from colorama import Fore, Style

class Logger:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def info(self, msg, color=Fore.MAGENTA):
        if self.verbose:
            print(f"{color}{msg}{Style.RESET_ALL}")
    
    def success(self, msg):
        print(f"{Fore.GREEN}[+] {msg}{Style.RESET_ALL}")

    def error(self, msg):
        print(f"{Fore.RED}[!] {msg}{Style.RESET_ALL}")