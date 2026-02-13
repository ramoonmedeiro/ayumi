import subprocess
import os
import json
import tempfile
import shutil
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from colorama import Fore, Style


# Locais comuns de wordlists de parametros
COMMON_WORDLISTS = [
    # Arjun built-in
    os.path.expanduser("~/.local/share/arjun/db/large.txt"),
    os.path.expanduser("~/.local/share/arjun/db/default.txt"),
    os.path.expanduser("~/.local/pipx/venvs/arjun/lib/python3.*/site-packages/arjun/db/large.txt"),
    # SecLists
    "/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt",
    os.path.expanduser("~/SecLists/Discovery/Web-Content/burp-parameter-names.txt"),
    os.path.expanduser("~/wordlists/params.txt"),
    # x8 / samlists
    os.path.expanduser("~/samlists/params.txt"),
]


class ParamDiscovery:
    """
    Descoberta de parametros ocultos usando x8.

    x8 e um fuzzer de parametros escrito em Rust que descobre parametros
    hidden/unreferenced comparando respostas HTTP linha a linha.

    Estrategia:
    1. Coleta todas as URLs (alive + sliced)
    2. Deduplica por endpoint (scheme + host + path)
    3. Executa x8 com wordlist de parametros
    4. Parseia resultados JSON
    5. Constroi URLs enriquecidas com parametros descobertos
    6. Output: JSONL estruturado + arquivo de URLs enriquecidas

    As URLs enriquecidas alimentam diretamente:
    - XSS scanning (dalfox)
    - HTTP methods scanning
    - Outros ataques baseados em parametros
    """

    def __init__(
        self,
        _input: str,
        verbose: bool = False,
        wordlist: str = None,
        headers: list = None,
        cookies: str = None,
    ) -> None:
        self.input = _input
        self.verbose = verbose
        self.wordlist = wordlist
        self.custom_headers = headers or []
        self.cookies = cookies

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

    def _resolve_wordlist(self) -> str:
        """
        Resolve o caminho da wordlist de parametros.
        Ordem de prioridade:
        1. Wordlist passada como argumento
        2. Env var PARAM_WORDLIST
        3. Locais comuns (arjun, seclists, etc)
        """
        # 1. Argumento direto
        if self.wordlist and os.path.isfile(self.wordlist):
            return self.wordlist

        # 2. Env var
        env_wl = os.environ.get("PARAM_WORDLIST", "")
        if env_wl and os.path.isfile(env_wl):
            return env_wl

        # 3. Locais comuns (com suporte a glob para paths com wildcard)
        import glob
        for wl_path in COMMON_WORDLISTS:
            if "*" in wl_path:
                matches = glob.glob(wl_path)
                if matches:
                    return matches[0]
            elif os.path.isfile(wl_path):
                return wl_path

        return None

    def _deduplicate_by_endpoint(self, urls: list) -> list:
        """
        Deduplica URLs por endpoint (scheme + host + path).
        Testa parametros uma vez por endpoint, nao por variacao de query param.
        Mantem a URL com mais parametros existentes como representante.
        """
        seen = {}
        for url in urls:
            try:
                parsed = urlparse(url)
                key = (parsed.scheme, parsed.netloc, parsed.path)
                if key not in seen:
                    seen[key] = url
                else:
                    # Manter a URL com mais parametros
                    existing_params = len(parse_qs(urlparse(seen[key]).query))
                    new_params = len(parse_qs(parsed.query))
                    if new_params > existing_params:
                        seen[key] = url
            except Exception:
                seen[url] = url
        return list(seen.values())

    def _build_x8_command(self, target_urls: list, output_file: str, wordlist: str) -> list:
        """
        Monta o comando x8 com flags otimizadas.

        Flags:
        - -u: URLs (pode receber multiplas ou arquivo)
        - -w: wordlist de parametros
        - -W 5: 5 workers concorrentes por URL
        - -c 3: 3 requests concorrentes por worker
        - -L: follow redirects
        - --verify: verificar parametros encontrados (menos falsos positivos)
        - -O json: output JSON estruturado
        - -o: arquivo de saida
        - --remove-empty: nao salvar URLs sem parametros encontrados
        - -d 100: 100ms delay entre requests
        """
        command = [
            "x8",
        ]

        # URLs - se forem muitas, usar arquivo; senao, direto
        for url in target_urls:
            command.extend(["-u", url])

        command.extend([
            "-w", wordlist,
            "-c", "3",
            "-L",
            "--verify",
            "-O", "json",
            "-o", output_file,
            "--remove-empty",
            "-d", "100",
        ])

        # Custom headers
        if self.custom_headers:
            header_args = []
            for h in self.custom_headers:
                header_args.append(h)
            if header_args:
                command.extend(["-H"] + header_args)

        # Cookies via header
        if self.cookies:
            command.extend(["-H", f"Cookie: {self.cookies}"])

        return command

    def _build_x8_file_command(self, urls_file: str, output_file: str, wordlist: str) -> str:
        """
        Monta comando x8 usando arquivo de URLs via shell pipe.
        x8 aceita URLs via -u com arquivo.
        """
        command = [
            "x8",
            "-u", urls_file,
            "-w", wordlist,
            "-c", "3",
            "-L",
            "--verify",
            "-O", "json",
            "-o", output_file,
            "--remove-empty",
            "-d", "100",
        ]

        # Custom headers
        if self.custom_headers:
            header_args = []
            for h in self.custom_headers:
                header_args.append(h)
            if header_args:
                command.extend(["-H"] + header_args)

        # Cookies
        if self.cookies:
            command.extend(["-H", f"Cookie: {self.cookies}"])

        return command

    def _parse_x8_results(self, output_file: str) -> list:
        """
        Parseia output JSON do x8.

        x8 JSON format:
        [{"url":"...","method":"GET","parameters":["param1","param2"]}]

        Tambem suporta JSONL (um JSON por linha).
        """
        results = []

        if not os.path.isfile(output_file):
            return results

        with open(output_file, "r") as f:
            content = f.read().strip()

        if not content:
            return results

        # Tentar parsear como JSON array
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for entry in data:
                    if entry.get("parameters"):
                        results.append({
                            "url": entry.get("url", ""),
                            "method": entry.get("method", "GET"),
                            "discovered_params": entry.get("parameters", []),
                        })
                return results
        except json.JSONDecodeError:
            pass

        # Fallback: tentar como JSONL
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("parameters"):
                    results.append({
                        "url": entry.get("url", ""),
                        "method": entry.get("method", "GET"),
                        "discovered_params": entry.get("parameters", []),
                    })
            except json.JSONDecodeError:
                # Tentar formato standard: "URL | param1, param2"
                if " | " in line:
                    parts = line.split(" | ", 1)
                    url = parts[0].strip()
                    params = [p.strip() for p in parts[1].split(",") if p.strip()]
                    if url and params:
                        results.append({
                            "url": url,
                            "method": "GET",
                            "discovered_params": params,
                        })

        return results

    def _build_enriched_urls(self, results: list) -> list:
        """
        Constroi URLs enriquecidas com os parametros descobertos.

        Para cada URL + parametros descobertos:
        1. Manter parametros originais da URL
        2. Adicionar os parametros descobertos com valor 'FUZZ'
        3. Gerar a URL completa

        Exemplo:
        URL: https://example.com/search?q=test
        Discovered: ['admin', 'debug']
        -> https://example.com/search?q=test&admin=FUZZ&debug=FUZZ
        """
        enriched = []

        for result in results:
            url = result["url"]
            new_params = result["discovered_params"]

            if not new_params:
                continue

            try:
                parsed = urlparse(url)
                existing_params = parse_qs(parsed.query, keep_blank_values=True)

                # Adicionar novos parametros (sem sobrescrever existentes)
                for param in new_params:
                    if param not in existing_params:
                        existing_params[param] = ["FUZZ"]

                # Reconstruir query string (flatten single values)
                flat_params = {}
                for k, v in existing_params.items():
                    flat_params[k] = v[0] if len(v) == 1 else v[0]

                new_query = urlencode(flat_params)
                enriched_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    "",
                ))
                enriched.append(enriched_url)

            except Exception as e:
                if self.verbose:
                    print(f"{Fore.RED}  Error enriching {url}: {e}{Style.RESET_ALL}")

        return enriched

    def run_all(self, output_file: str = None) -> None:
        """
        Entry point principal.

        Pipeline:
        1. Carrega URLs
        2. Deduplica por endpoint
        3. Resolve wordlist
        4. Executa x8
        5. Parseia resultados
        6. Constroi URLs enriquecidas
        7. Escreve outputs: JSONL estruturado + URLs enriquecidas
        """
        if not output_file:
            output_file = "params_discovered.jsonl"

        # Derivar arquivo de URLs enriquecidas do output principal
        base_dir = os.path.dirname(output_file) or "."
        enriched_file = os.path.join(
            base_dir, "urls_param_discovered.txt"
        )

        print(
            Fore.GREEN + "Running: " + Fore.CYAN
            + "Parameter Discovery (x8)"
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

        # 2. Deduplicar por endpoint
        deduped = self._deduplicate_by_endpoint(urls)

        if self.verbose:
            removed = total_input - len(deduped)
            print(
                f"{Fore.YELLOW}[*] URLs apos deduplicacao: {len(deduped)} "
                f"({removed} duplicatas removidas){Style.RESET_ALL}"
            )

        # 3. Resolver wordlist
        wordlist = self._resolve_wordlist()
        if not wordlist:
            print(
                f"{Fore.RED}[!] Wordlist de parametros nao encontrada.\n"
                f"    Defina PARAM_WORDLIST env var ou use -wl <path>\n"
                f"    Wordlists recomendadas:\n"
                f"      - pipx install arjun (usa ~/.local/share/arjun/db/large.txt)\n"
                f"      - SecLists: Discovery/Web-Content/burp-parameter-names.txt\n"
                f"      - https://github.com/the-xentropy/samlists{Style.RESET_ALL}"
            )
            return

        if self.verbose:
            print(f"{Fore.YELLOW}[*] Wordlist: {wordlist}{Style.RESET_ALL}")

        # 4. Executar x8
        tmp_dir = tempfile.mkdtemp(prefix="ayumi_params_")
        urls_file = os.path.join(tmp_dir, "targets.txt")
        raw_output = os.path.join(tmp_dir, "x8_output.json")

        try:
            # Escrever targets
            with open(urls_file, "w") as f:
                for url in deduped:
                    f.write(url + "\n")

            command = self._build_x8_file_command(urls_file, raw_output, wordlist)

            if self.verbose:
                print(
                    f"{Fore.YELLOW}[*] Executando: {' '.join(command)}{Style.RESET_ALL}"
                )

            print(
                f"{Fore.CYAN}[*] Fuzzing parametros em {len(deduped)} endpoints...{Style.RESET_ALL}"
            )

            try:
                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=7200,
                )

                if result.returncode != 0 and self.verbose:
                    print(
                        f"{Fore.RED}[!] x8 exit code: {result.returncode}{Style.RESET_ALL}"
                    )
                    if result.stderr:
                        for err_line in result.stderr.strip().splitlines()[:5]:
                            print(f"{Fore.RED}    {err_line}{Style.RESET_ALL}")

            except FileNotFoundError:
                print(
                    f"{Fore.RED}[!] x8 nao encontrado.\n"
                    f"    Instale com: cargo install x8\n"
                    f"    Ou: https://github.com/sh1yo/x8/releases{Style.RESET_ALL}"
                )
                return
            except subprocess.TimeoutExpired:
                print(f"{Fore.RED}[!] x8 timeout apos 2 horas{Style.RESET_ALL}")

            # 5. Parsear resultados
            results = self._parse_x8_results(raw_output)

            # 6. Construir URLs enriquecidas
            enriched_urls = self._build_enriched_urls(results)

            # 7. Escrever outputs
            # JSONL estruturado
            with open(output_file, "w") as f:
                for result in results:
                    f.write(json.dumps(result) + "\n")

            # URLs enriquecidas (prontas para XSS/attacks)
            with open(enriched_file, "w") as f:
                for url in enriched_urls:
                    f.write(url + "\n")

            # Resumo
            total_params = sum(len(r["discovered_params"]) for r in results)
            endpoints_with_params = len(results)

            print(f"\n{Fore.GREEN}[+] Parameter discovery finalizado!{Style.RESET_ALL}")
            print(
                f"{Fore.GREEN}    {total_params} parametros ocultos "
                f"em {endpoints_with_params} endpoints{Style.RESET_ALL}"
            )
            print(
                f"{Fore.GREEN}    {len(enriched_urls)} URLs enriquecidas geradas{Style.RESET_ALL}"
            )

            # Mostrar findings
            for result in results:
                params_str = ", ".join(result["discovered_params"][:10])
                suffix = "..." if len(result["discovered_params"]) > 10 else ""
                print(
                    f"{Fore.CYAN}    {result['url']}"
                    f"{Fore.YELLOW} -> [{params_str}{suffix}]{Style.RESET_ALL}"
                )

            print(
                Fore.MAGENTA
                + f"\n🔍 Parametros: {output_file}"
                + Style.RESET_ALL
            )
            print(
                Fore.MAGENTA
                + f"🔗 URLs enriquecidas: {enriched_file}"
                + Style.RESET_ALL
            )

        finally:
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
