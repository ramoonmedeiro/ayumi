import re
import requests
import os
import random
import urllib3
from colorama import Fore, Style
from typing import Set
from tqdm import tqdm
import concurrent.futures
from concurrent import futures
from typing import Dict, List

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LinkExtractor:
    def __init__(self, _input: str, verbose: bool):
        self.input = _input
        self.verbose = verbose
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/119.0"
        ]
        
        # Regex profissional compilado
        self.regex_str = re.compile(r"""
            (?:"|')                               
            (
                ((?:[a-zA-Z]{1,10}://|//)         
                [^"'/]{1,}\.                      
                [a-zA-Z]{2,}[^"']{0,})            
                |
                ((?:/|\.\./|\./)                  
                [^"'><,;| *()(%%$^/\\\[\]]
                [^"'><,;|()]{1,})
                |
                ([a-zA-Z0-9_\-/]{1,}/             
                [a-zA-Z0-9_\-/.]{1,}\.(?:[a-zA-Z]{1,4}|action)(?:[\?|#][^"|']{0,}|))
                |
                ([a-zA-Z0-9_\-/]{1,}/[a-zA-Z0-9_\-/]{3,}(?:[\?|#][^"|']{0,}|))
                |
                ([a-zA-Z0-9_\-]{1,}\.(?:php|asp|aspx|jsp|json|action|html|js|txt|xml)(?:[\?|#][^"|']{0,}|))
            )
            (?:"|')                               
        """, re.VERBOSE)

    def _get_headers(self) -> dict:
        return {"User-Agent": random.choice(self.user_agents)}

    def extract(self, url: str) -> Set[str]:
        """Faz o download e extrai os links únicos."""
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=10, verify=False)
            if res.status_code == 200:
                matches = self.regex_str.findall(res.text)
                return {m[0] for m in matches if m[0]}
            return {f"ERRO_STATUS_{res.status_code}"}
        except Exception as e:
            return {f"ERRO_CONEXAO: {str(e)}"}

    def run(self, output_file: str = None):
        """Processa entrada (URL ou arquivo) e salva no TXT."""
        if not output_file:
            output_file = "extracted_links.txt"
        
        if os.path.isfile(self.input):
            with open(self.input, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        else:
            urls = [self.input]

        with open(output_file, "w", encoding="utf-8") as f_out:
            for url in tqdm(urls, desc="Extraindo links", ascii=True, colour="#290f75"):
                links = self.extract(url)
                
                header = f"URL: {url}\n"
                f_out.write(header)

                for link in links:
                    f_out.write(f"{link}\n")
                
                f_out.write("\n" + "="*50 + "\n\n")
        if self.verbose:
            print(Fore.MAGENTA + f"\n🪷  Results saved in {output_file}" + Style.RESET_ALL)


class JuiceKeysExtractor:
    def __init__(self, _input: str, verbose: bool):
        self.input = _input
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.regex_file = os.path.join(current_dir, "regex-patterns", "regex-keys.txt")

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/119.0"
        ]
        self.keys_patterns = self._load_regexes()

    def _load_regexes(self) -> Dict[str, re.Pattern]:
        """Lê o arquivo de regex e compila cada linha."""
        patterns = {}
        if not os.path.exists(self.regex_file):
            if self.verbose:
                print(Fore.RED + f"[-] Erro: Arquivo {self.regex_file} não encontrado!")
            return {}
        
        with open(self.regex_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        patterns[line] = re.compile(line, re.MULTILINE)
                    except Exception as e:
                        if self.verbose:
                            print(Fore.YELLOW + f"[!] Regex inválido ignorado: {line} -> {e}")
        return patterns

    def _get_headers(self) -> dict:
        return {"User-Agent": random.choice(self.user_agents)}

    def scan_url(self, url: str) -> List[Dict]:
        """Baixa o conteúdo e testa todos os regexes."""
        found_matches = []
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=15, verify=False)
            if res.status_code == 200:
                content = res.text
                for pattern_str, compiled_re in self.keys_patterns.items():
                    matches = compiled_re.finditer(content)
                    for match in matches:
                        found_matches.append({
                            "url": url,
                            "regex": pattern_str,
                            "match": match.group(),
                            "start": match.start(),
                            "end": match.end()
                        })
        except Exception as e:
            pass
        return found_matches

    def run(self, output_file: str = None):
        """Gerencia o processamento paralelo e salvamento."""
        if not self.keys_patterns:
            return

        if not output_file:
            output_file = "leaked_keys.txt"

        if os.path.isfile(self.input):
            with open(self.input, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        else:
            urls = [self.input]
        if self.verbose:
            print(Fore.CYAN + f"[*] Iniciando busca por chaves em {len(urls)} URLs...")
        
        with open(output_file, "a", encoding="utf-8") as f_out:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self.scan_url, url): url for url in urls}
                
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(urls), desc="Scanning Keys", ascii=True, colour="#e01b24", disable=not self.verbose):
                    results = future.result()
                    
                    if results:
                        for item in results:
                            if self.verbose:
                                print(f"\n{Fore.WHITE}[Target]: {item['url']}")
                                print(f"{Fore.GREEN}[+] Regex: {Fore.YELLOW}{item['regex']}")
                                print(f"{Fore.RED}[!] Match: {Fore.WHITE}{item['match']}{Style.RESET_ALL}")
                                
                            log_entry = (
                                f"URL: {item['url']}\n"
                                f"Regex: {item['regex']}\n"
                                f"Match: {item['match']}\n"
                                f"{'='*50}\n"
                            )
                            f_out.write(log_entry)
                            f_out.flush()
        if self.verbose:
            print(Fore.MAGENTA + f"\n✨ Scan finalizado! Resultados salvos em: {output_file}")