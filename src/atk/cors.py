import subprocess
import os
import requests
from colorama import Fore, Style

class CorsAnalyzer:
    def __init__(self, _input: str, verbose: bool) -> None:
        self.input = _input
        self.verbose = verbose
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    def _is_file(self) -> bool:
        return os.path.isfile(self.input)

    def test_cors(self, url: str, output_file: str) -> None:
        evil_origins = [
            "https://evil.com",
            "https://attacker.com",
            "null"
        ]

        if self.verbose:
            print(f"{Fore.YELLOW}Testing: {Fore.WHITE}{url}{Style.RESET_ALL}")

        for origin in evil_origins:
            current_headers = self.headers.copy()
            current_headers["Origin"] = origin
            
            try:
                # Timeout adicionado para evitar que o script trave
                r = requests.get(url, headers=current_headers, timeout=10, verify=False)
                cors_header = r.headers.get("Access-Control-Allow-Origin")
                credentials_header = r.headers.get("Access-Control-Allow-Credentials")

                # Verifica vulnerabilidade
                is_vulnerable = False
                if cors_header and (cors_header == origin or cors_header == "*"):
                    is_vulnerable = True

                if is_vulnerable:
                    result_msg = f"[!] CORS Misconfiguration: {url} | Origin: {origin} | Reflected: {cors_header}"
                    print(f"{Fore.RED}{result_msg}{Style.RESET_ALL}")
                    
                    if credentials_header == "true":
                        print(f"{Fore.RED}{Style.BRIGHT}    [CRITICAL] Credentials allowed!{Style.RESET_ALL}")
                        result_msg += " [CREDENTIALS ENABLED]"

                    # Salva no arquivo de output
                    with open(output_file, "a") as f:
                        f.write(result_msg + "\n")
                    
                    break

            except Exception as e:
                if self.verbose:
                    print(f"{Fore.RED}Error connecting to {url}: {str(e)}{Style.RESET_ALL}")
                pass

    def run_all(self, output_file: str = None) -> None:
        if self.verbose:
            print(Fore.GREEN + "Running: " + Fore.CYAN + "CORS Misconfiguration Analysis" + Style.RESET_ALL)

        if not output_file:
            output_file = "cors_results.txt"

        # Lógica para tratar arquivo ou URL única
        if self._is_file():
            with open(self.input, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            for url in urls:
                self.test_cors(url, output_file)
        else:
            # Garante que a URL tenha protocolo
            url = self.input if self.input.startswith("http") else f"https://{self.input}"
            self.test_cors(url, output_file)

        if self.verbose:
            print(Fore.MAGENTA + f"\n🌹 Analysis finished. Results saved in {output_file}" + Style.RESET_ALL)