import subprocess
import os
import json
import tempfile
import shutil
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from colorama import Fore, Style


class XSSScanner:
    """
    Scanner de XSS inteligente usando dalfox.

    Estratégia:
    1. Pre-filtra URLs com parâmetros de query (sem params = sem reflected XSS)
    2. Deduplica por padrão (path + nomes de params) para evitar scans redundantes
    3. Usa dalfox pipe com output JSON para parsing estruturado
    4. Suporte a blind XSS, headers customizados, cookies e deep DOM XSS
    """

    def __init__(
        self,
        _input: str,
        verbose: bool = False,
        blind_url: str = None,
        headers: list = None,
        cookies: str = None,
        deep: bool = False,
    ) -> None:
        self.input = _input
        self.verbose = verbose
        self.blind_url = blind_url
        self.headers = headers or []
        self.cookies = cookies
        self.deep = deep

    def _is_file(self) -> bool:
        return os.path.isfile(self.input)

    def _load_urls(self) -> list:
        """Carrega URLs do input (arquivo ou URL única)."""
        if self._is_file():
            with open(self.input, "r") as f:
                return [line.strip() for line in f if line.strip()]
        else:
            url = self.input if self.input.startswith("http") else f"https://{self.input}"
            return [url]

    def _filter_urls_with_params(self, urls: list) -> list:
        """
        Filtra apenas URLs que possuem query parameters.
        URLs sem parâmetros não são testáveis para reflected XSS via dalfox.
        """
        filtered = []
        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.query:
                    filtered.append(url)
            except Exception:
                continue
        return filtered

    def _deduplicate_by_pattern(self, urls: list) -> list:
        """
        Agrupa URLs pelo padrão (scheme + host + path + nomes dos parâmetros).
        Mantém apenas 1 representante por padrão para evitar scans redundantes.
        Exemplo: /search?q=foo e /search?q=bar -> testa apenas 1.
        """
        seen_patterns = {}
        for url in urls:
            try:
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                # Chave: scheme + netloc + path + sorted param names
                param_names = tuple(sorted(params.keys()))
                pattern_key = (parsed.scheme, parsed.netloc, parsed.path, param_names)

                if pattern_key not in seen_patterns:
                    seen_patterns[pattern_key] = url
            except Exception:
                # Se falhar o parse, inclui a URL mesmo assim
                seen_patterns[url] = url

        return list(seen_patterns.values())

    def _build_dalfox_command(self, target_file: str, output_file: str) -> list:
        """
        Monta o comando dalfox pipe com flags otimizadas.

        Estratégia de flags:
        - pipe: processa múltiplas URLs via stdin file
        - --silence: output limpo, sem ruído visual
        - -F: follow redirects para melhor cobertura
        - --skip-bav: foco exclusivo em XSS
        - --skip-mining-dict: params já mapeados externamente
        - --worker 50: concorrência controlada
        - --delay 100: evita rate limiting / WAF
        - --waf-evasion: ajuste automático de velocidade ao detectar WAF
        - --only-poc v,r: retorna verified e reflected (sem grep noise)
        - --format jsonl: output parseável
        - --deep-domxss: (opcional) busca profunda de DOM XSS
        """
        command = [
            "dalfox", "file", target_file,
            "--silence",
            "-F",
            "--skip-bav",
            "--skip-mining-dict",
            "--worker", "50",
            "--delay", "100",
            "--waf-evasion",
            "--only-poc", "v,r",
            "--format", "json",
            "-o", output_file,
        ]

        # Blind XSS callback
        if self.blind_url:
            command.extend(["-b", self.blind_url])

        # Deep DOM XSS
        if self.deep:
            command.append("--deep-domxss")

        # Custom headers
        for header in self.headers:
            command.extend(["-H", header])

        # Custom cookies
        if self.cookies:
            command.extend(["-C", self.cookies])

        return command

    def _parse_results(self, output_file: str) -> list:
        """
        Parseia output JSON/JSONL do dalfox e classifica findings.

        Classificação de severidade:
        - [V] Verified (DOM object / headless) -> high
        - [R] Reflected -> medium
        - [G] Grep-based -> info
        """
        results = []

        if not os.path.isfile(output_file):
            return results

        with open(output_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Tenta parsear como JSON
                try:
                    data = json.loads(line)
                    finding = self._normalize_json_finding(data)
                    if finding:
                        results.append(finding)
                    continue
                except json.JSONDecodeError:
                    pass

                # Fallback: parsear output plain text do dalfox
                finding = self._parse_plain_line(line)
                if finding:
                    results.append(finding)

        return results

    def _normalize_json_finding(self, data: dict) -> dict:
        """Normaliza um finding JSON do dalfox para formato padronizado."""
        poc_type = data.get("type", "").lower()
        poc_url = data.get("data", data.get("poc", ""))
        inject_type = data.get("inject_type", "")
        param = data.get("param", "")
        payload = data.get("payload", "")
        evidence = data.get("evidence", data.get("message_str", ""))
        cwe = data.get("cwe", "")
        severity_str = data.get("severity", "")

        # Classificar severidade baseado no tipo
        if poc_type in ("verified", "v") or "verified" in str(inject_type).lower():
            severity = "high"
            finding_type = "verified"
        elif poc_type in ("reflected", "r") or "reflected" in str(inject_type).lower():
            severity = "medium"
            finding_type = "reflected"
        elif poc_type in ("grep", "g"):
            severity = "info"
            finding_type = "grep"
        else:
            severity = severity_str if severity_str else "medium"
            finding_type = poc_type or "unknown"

        if not poc_url:
            return None

        return {
            "url": poc_url,
            "poc": poc_url,
            "type": finding_type,
            "param": param,
            "severity": severity,
            "payload": payload,
            "evidence": evidence,
            "cwe": cwe,
            "inject_type": inject_type,
        }

    def _parse_plain_line(self, line: str) -> dict:
        """Parseia uma linha de output plain text do dalfox como fallback."""
        if not line.startswith("[POC]"):
            return None

        # Formato: [POC][TYPE][DETAIL] URL
        severity = "medium"
        finding_type = "reflected"

        if "[V]" in line:
            severity = "high"
            finding_type = "verified"
        elif "[R]" in line:
            severity = "medium"
            finding_type = "reflected"
        elif "[G]" in line:
            severity = "info"
            finding_type = "grep"

        # Extrair URL (último token que começa com http)
        parts = line.split()
        poc_url = ""
        for part in reversed(parts):
            if part.startswith("http"):
                poc_url = part
                break

        if not poc_url:
            return None

        return {
            "url": poc_url,
            "poc": poc_url,
            "type": finding_type,
            "param": "",
            "severity": severity,
            "payload": "",
            "evidence": line,
            "cwe": "",
            "inject_type": "",
        }

    def _write_structured_output(self, results: list, output_file: str) -> None:
        """Escreve resultados estruturados em JSONL para consumo do Kakashi."""
        with open(output_file, "w") as f:
            for finding in results:
                f.write(json.dumps(finding) + "\n")

    def run_all(self, output_file: str = None) -> None:
        """
        Entry point principal do XSS scanner.

        Pipeline:
        1. Carrega URLs
        2. Filtra URLs com parâmetros
        3. Deduplica por padrão
        4. Escreve targets em arquivo temporário
        5. Executa dalfox
        6. Parseia resultados
        7. Escreve output estruturado
        """
        if not output_file:
            output_file = "xss_results.jsonl"

        print(
            Fore.GREEN + "Running: " + Fore.CYAN + "XSS Scanner (dalfox)" + Style.RESET_ALL
        )

        # 1. Carregar URLs
        urls = self._load_urls()
        total_input = len(urls)

        if self.verbose:
            print(
                f"{Fore.YELLOW}[*] URLs carregadas: {total_input}{Style.RESET_ALL}"
            )

        if not urls:
            print(f"{Fore.RED}[!] Nenhuma URL encontrada no input{Style.RESET_ALL}")
            return

        # 2. Filtrar URLs com parâmetros
        urls_with_params = self._filter_urls_with_params(urls)

        if self.verbose:
            print(
                f"{Fore.YELLOW}[*] URLs com parâmetros: {len(urls_with_params)}/{total_input}{Style.RESET_ALL}"
            )

        if not urls_with_params:
            print(
                f"{Fore.YELLOW}[!] Nenhuma URL com parâmetros de query encontrada. "
                f"Skipping XSS scan.{Style.RESET_ALL}"
            )
            return

        # 3. Deduplicar por padrão
        deduped = self._deduplicate_by_pattern(urls_with_params)

        if self.verbose:
            removed = len(urls_with_params) - len(deduped)
            print(
                f"{Fore.YELLOW}[*] URLs após deduplicação: {len(deduped)} "
                f"({removed} duplicatas removidas){Style.RESET_ALL}"
            )

        # 4. Escrever targets em arquivo temporário
        tmp_dir = tempfile.mkdtemp(prefix="ayumi_xss_")
        target_file = os.path.join(tmp_dir, "xss_targets.txt")
        raw_output_file = os.path.join(tmp_dir, "dalfox_raw_output.json")

        try:
            with open(target_file, "w") as f:
                for url in deduped:
                    f.write(url + "\n")

            # 5. Executar dalfox
            command = self._build_dalfox_command(target_file, raw_output_file)

            if self.verbose:
                print(
                    f"{Fore.YELLOW}[*] Executando: {' '.join(command)}{Style.RESET_ALL}"
                )

            print(
                f"{Fore.CYAN}[*] Scanning {len(deduped)} URLs com dalfox...{Style.RESET_ALL}"
            )

            try:
                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=7200,  # 2 horas de timeout
                )

                if result.returncode != 0 and self.verbose:
                    print(
                        f"{Fore.RED}[!] dalfox exit code: {result.returncode}{Style.RESET_ALL}"
                    )
                    if result.stderr:
                        for err_line in result.stderr.strip().splitlines()[:5]:
                            print(f"{Fore.RED}    {err_line}{Style.RESET_ALL}")

            except FileNotFoundError:
                print(
                    f"{Fore.RED}[!] dalfox não encontrado. "
                    f"Instale com: go install github.com/hahwul/dalfox/v2@latest{Style.RESET_ALL}"
                )
                return
            except subprocess.TimeoutExpired:
                print(
                    f"{Fore.RED}[!] dalfox timeout após 2 horas{Style.RESET_ALL}"
                )

            # 6. Parsear resultados
            results = self._parse_results(raw_output_file)

            # 7. Escrever output estruturado
            self._write_structured_output(results, output_file)

            # Resumo
            verified = sum(1 for r in results if r["type"] == "verified")
            reflected = sum(1 for r in results if r["type"] == "reflected")
            grep = sum(1 for r in results if r["type"] == "grep")

            print(
                f"\n{Fore.GREEN}[+] XSS Scan finalizado!{Style.RESET_ALL}"
            )
            print(
                f"{Fore.GREEN}    Resultados: "
                f"{Fore.RED}{verified} verified{Fore.GREEN}, "
                f"{Fore.YELLOW}{reflected} reflected{Fore.GREEN}, "
                f"{Fore.CYAN}{grep} grep{Style.RESET_ALL}"
            )

            # Mostrar findings verificados/reflected
            for finding in results:
                if finding["type"] == "verified":
                    print(
                        f"{Fore.RED}{Style.BRIGHT}    [VERIFIED XSS] {finding['poc']}{Style.RESET_ALL}"
                    )
                    if finding.get("param"):
                        print(
                            f"{Fore.RED}      Param: {finding['param']}{Style.RESET_ALL}"
                        )
                elif finding["type"] == "reflected":
                    print(
                        f"{Fore.YELLOW}    [REFLECTED] {finding['poc']}{Style.RESET_ALL}"
                    )

            print(
                Fore.MAGENTA
                + f"\n🎯 Resultados salvos em {output_file}"
                + Style.RESET_ALL
            )

        finally:
            # Cleanup temp dir
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
