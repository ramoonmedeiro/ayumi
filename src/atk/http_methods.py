import os
import json
import requests
from urllib.parse import urlparse
from colorama import Fore, Style


# Metodos HTTP perigosos que indicam misconfiguration
DANGEROUS_METHODS = ["PUT", "PATCH", "DELETE"]

# Status codes que confirmam que o metodo esta habilitado
# (qualquer coisa que NAO seja 405 Method Not Allowed ou 501 Not Implemented)
BLOCKED_STATUS_CODES = {405, 501}


class HTTPMethodScanner:
    """
    Scanner de metodos HTTP perigosos (PUT, PATCH, DELETE).

    Estrategia:
    1. Envia OPTIONS para descobrir header Allow com metodos aceitos
    2. Para cada metodo perigoso encontrado no Allow, confirma com request direto
    3. Se nao tiver Allow, testa os 3 metodos diretamente
    4. Classifica como vulneravel se o server responder com status != 405/501

    Output JSONL com cada finding contendo URL, metodo, status_code, evidencia.
    """

    def __init__(
        self,
        _input: str,
        verbose: bool = False,
        headers: list = None,
        cookies: str = None,
    ) -> None:
        self.input = _input
        self.verbose = verbose
        self.custom_headers = headers or []
        self.cookies = cookies
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/119.0.0.0 Safari/537.36"
        }

    def _is_file(self) -> bool:
        return os.path.isfile(self.input)

    def _load_urls(self) -> list:
        """Carrega URLs do input (arquivo ou URL unica)."""
        if self._is_file():
            with open(self.input, "r") as f:
                return [line.strip() for line in f if line.strip()]
        else:
            url = self.input if self.input.startswith("http") else f"https://{self.input}"
            return [url]

    def _build_headers(self) -> dict:
        """Monta headers com os customizados."""
        headers = self.base_headers.copy()
        for h in self.custom_headers:
            if ":" in h:
                key, val = h.split(":", 1)
                headers[key.strip()] = val.strip()
        return headers

    def _build_cookies(self) -> dict:
        """Monta dict de cookies."""
        if not self.cookies:
            return None
        cookie_dict = {}
        for part in self.cookies.split(";"):
            part = part.strip()
            if "=" in part:
                key, val = part.split("=", 1)
                cookie_dict[key.strip()] = val.strip()
        return cookie_dict if cookie_dict else None

    def _get_allowed_methods_from_options(self, url: str, headers: dict, cookies: dict) -> list:
        """
        Envia OPTIONS request e parseia o header Allow.
        Retorna lista de metodos perigosos encontrados no Allow.
        """
        try:
            r = requests.options(
                url, headers=headers, cookies=cookies,
                timeout=10, verify=False, allow_redirects=True,
            )
            allow_header = r.headers.get("Allow", "")
            if not allow_header:
                # Tenta tambem Access-Control-Allow-Methods (CORS preflight)
                allow_header = r.headers.get("Access-Control-Allow-Methods", "")

            if allow_header:
                methods_in_allow = [m.strip().upper() for m in allow_header.split(",")]
                dangerous_found = [m for m in DANGEROUS_METHODS if m in methods_in_allow]
                return dangerous_found

        except Exception as e:
            if self.verbose:
                print(f"{Fore.RED}  OPTIONS error for {url}: {e}{Style.RESET_ALL}")

        return []

    def _test_method_directly(self, url: str, method: str, headers: dict, cookies: dict) -> dict:
        """
        Testa um metodo HTTP diretamente contra a URL.
        Retorna finding dict se o metodo estiver habilitado, None caso contrario.
        """
        try:
            r = requests.request(
                method, url,
                headers=headers, cookies=cookies,
                timeout=10, verify=False, allow_redirects=True,
                data="",  # body vazio
            )

            status = r.status_code

            # Se nao retornou 405/501, o metodo esta habilitado
            if status not in BLOCKED_STATUS_CODES:
                # Determinar severidade baseado no metodo e status
                if method == "DELETE" and status in (200, 204):
                    severity = "high"
                elif method in ("PUT", "PATCH") and status in (200, 201, 204):
                    severity = "high"
                elif status in (200, 201, 204, 202):
                    severity = "medium"
                else:
                    severity = "low"

                return {
                    "url": url,
                    "method": method,
                    "status_code": status,
                    "severity": severity,
                    "evidence": f"{method} {url} -> HTTP {status}",
                    "content_length": len(r.content),
                    "server": r.headers.get("Server", ""),
                }

        except Exception as e:
            if self.verbose:
                print(f"{Fore.RED}  {method} error for {url}: {e}{Style.RESET_ALL}")

        return None

    def _deduplicate_by_origin(self, urls: list) -> list:
        """
        Deduplica URLs por origin (scheme + host + path base).
        Testa metodos uma vez por endpoint, nao por variacao de query param.
        """
        seen = {}
        for url in urls:
            try:
                parsed = urlparse(url)
                # Chave: scheme + netloc + path (ignora query params)
                key = (parsed.scheme, parsed.netloc, parsed.path)
                if key not in seen:
                    seen[key] = url
            except Exception:
                seen[url] = url
        return list(seen.values())

    def test_url(self, url: str, headers: dict, cookies: dict) -> list:
        """
        Testa uma URL para metodos HTTP perigosos.
        Retorna lista de findings.
        """
        findings = []

        if self.verbose:
            print(f"{Fore.YELLOW}[*] Testing: {Fore.WHITE}{url}{Style.RESET_ALL}")

        # 1. Tentar OPTIONS primeiro para descobrir metodos permitidos
        options_methods = self._get_allowed_methods_from_options(url, headers, cookies)

        if options_methods:
            if self.verbose:
                print(
                    f"{Fore.CYAN}    OPTIONS Allow: {', '.join(options_methods)}{Style.RESET_ALL}"
                )
            # Confirmar cada metodo perigoso com request direto
            methods_to_test = options_methods
        else:
            # Sem Allow header -> testar todos os 3 diretamente
            methods_to_test = DANGEROUS_METHODS

        # 2. Testar cada metodo diretamente
        for method in methods_to_test:
            finding = self._test_method_directly(url, method, headers, cookies)
            if finding:
                findings.append(finding)
                color = Fore.RED if finding["severity"] in ("high", "medium") else Fore.YELLOW
                print(
                    f"{color}[!] {method} habilitado: {url} "
                    f"-> HTTP {finding['status_code']}{Style.RESET_ALL}"
                )

        return findings

    def run_all(self, output_file: str = None) -> None:
        """
        Entry point principal.

        Pipeline:
        1. Carrega URLs
        2. Deduplica por origin
        3. Testa cada URL para metodos perigosos
        4. Escreve output JSONL estruturado
        """
        if not output_file:
            output_file = "http_methods_results.jsonl"

        print(
            Fore.GREEN + "Running: " + Fore.CYAN
            + "HTTP Dangerous Methods Scanner (PUT/PATCH/DELETE)"
            + Style.RESET_ALL
        )

        # 1. Carregar URLs
        urls = self._load_urls()
        total_input = len(urls)

        if self.verbose:
            print(f"{Fore.YELLOW}[*] URLs carregadas: {total_input}{Style.RESET_ALL}")

        if not urls:
            print(f"{Fore.RED}[!] Nenhuma URL encontrada no input{Style.RESET_ALL}")
            return

        # 2. Deduplicar por origin (path base, sem query params)
        deduped = self._deduplicate_by_origin(urls)

        if self.verbose:
            removed = total_input - len(deduped)
            print(
                f"{Fore.YELLOW}[*] URLs apos deduplicacao: {len(deduped)} "
                f"({removed} duplicatas removidas){Style.RESET_ALL}"
            )

        # Preparar headers e cookies
        headers = self._build_headers()
        cookies = self._build_cookies()

        # 3. Testar cada URL
        all_findings = []
        for url in deduped:
            findings = self.test_url(url, headers, cookies)
            all_findings.extend(findings)

        # 4. Escrever output JSONL
        with open(output_file, "w") as f:
            for finding in all_findings:
                f.write(json.dumps(finding) + "\n")

        # Resumo
        put_count = sum(1 for f in all_findings if f["method"] == "PUT")
        patch_count = sum(1 for f in all_findings if f["method"] == "PATCH")
        delete_count = sum(1 for f in all_findings if f["method"] == "DELETE")

        print(f"\n{Fore.GREEN}[+] Scan finalizado!{Style.RESET_ALL}")
        print(
            f"{Fore.GREEN}    Resultados: "
            f"{Fore.RED}{delete_count} DELETE{Fore.GREEN}, "
            f"{Fore.YELLOW}{put_count} PUT{Fore.GREEN}, "
            f"{Fore.CYAN}{patch_count} PATCH{Style.RESET_ALL}"
        )
        print(
            f"{Fore.GREEN}    Total: {len(all_findings)} metodos perigosos encontrados "
            f"em {len(deduped)} URLs testadas{Style.RESET_ALL}"
        )

        if all_findings:
            print(
                Fore.MAGENTA
                + f"\n🔓 Resultados salvos em {output_file}"
                + Style.RESET_ALL
            )
        else:
            print(
                Fore.GREEN
                + "\n✅ Nenhum metodo perigoso encontrado."
                + Style.RESET_ALL
            )
