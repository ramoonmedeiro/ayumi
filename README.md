# Ayumi

Ayumi is a simple framework for web hacking, which concatenates and uses its own functions to perform some reconnaissance steps and some more basic attacks for bug bounty or pentest.


<div align="center">
  <img src="/assets/imgs/banner.png" width="320px" />
</div>

# Installation

```
$ git clone https://github.com/ramoonmedeiro/ayumi.git
$ cd ayumi
$ pip3 install -r requirements.txt
```
You need to install Golang on your computer and download some GO libraries.
To do this, follow the steps below.

```
$ bash setup.sh
```

# Usage

Ayumi was built to operate in modules. It has two modules: recon and atk (attack)

```
$ python3 ayumi.py -h


usage: ayumi.py [-h] {recon,atk} ...

positional arguments:
  {recon,atk}

options:
  -h, --help   show this help message and exit
```

To find out which flags can be used for the recon module, simply run the command below

```
$ python3 ayumi.py recon -h

options:
  -h, --help            show this help message and exit
  -ds DS                Discovery subdomains.
  -sp SP                Scan ports (Rustscan).
  -rc RC                Run crawler (katana).
  -rh RH                Run history crawler (gau and waybackurls).
  -rp RP                Run Paramspider.
  -get-js GET_JS        Run getJS.
  -filter-js FILTER_JS  Filter JS files from urls file.
  -dp DP                Discover hidden parameters on URL or file of URLs (x8).
  -wl WL                Custom wordlist for parameter discovery (used with -dp).
  -o O                  output file.
```

## Recon Module - Parameter Discovery (x8)

O modulo de descoberta de parametros usa o [x8](https://github.com/sh1yo/x8) para encontrar parametros ocultos/hidden em endpoints web. Parametros ocultos podem revelar funcionalidades administrativas, flags de debug, ou superficies de ataque nao documentadas.

**Estrategia:**

1. **Deduplica por endpoint** (scheme + host + path) para evitar testes redundantes
2. **Resolve wordlist automaticamente** - procura em locais comuns (arjun, SecLists, env var)
3. **Executa x8** com `--verify` para confirmar parametros (menos falsos positivos)
4. **Parseia resultados JSON** e constroi URLs enriquecidas com os parametros descobertos
5. **URLs enriquecidas** alimentam diretamente XSS scanning, HTTP methods e outros ataques

### Exemplos de uso

```bash
# Descobrir parametros em arquivo de URLs
python3 ayumi.py recon -dp urls_alive.txt -o params.jsonl -v

# URL unica
python3 ayumi.py recon -dp "https://api.target.com/v1/users" -v

# Com wordlist customizada
python3 ayumi.py recon -dp urls.txt -wl ~/wordlists/params.txt -o params.jsonl

# Com headers de autenticacao
python3 ayumi.py -H "Authorization: Bearer token" recon -dp urls.txt -o params.jsonl -v
```

### Requisitos

- [x8](https://github.com/sh1yo/x8) instalado: `cargo install x8`
- Wordlist de parametros (auto-detectada ou via `-wl`):
  - `pipx install arjun` (usa `~/.local/share/arjun/db/large.txt`)
  - SecLists: `Discovery/Web-Content/burp-parameter-names.txt`
  - Ou defina `PARAM_WORDLIST` env var

### Formato de output

**params_discovered.jsonl** (JSONL estruturado):
```json
{"url": "https://api.target.com/users", "method": "GET", "discovered_params": ["admin", "debug", "verbose"]}
```

**urls_param_discovered.txt** (URLs enriquecidas, prontas para XSS/attacks):
```
https://api.target.com/users?admin=FUZZ&debug=FUZZ&verbose=FUZZ
```

To find out which flags can be used for the atk module, simply run the command below

```
$ python3 ayumi.py atk -h

options:
  -h, --help            show this help message and exit
  -crlf CRLF            Run crlf injection
  -st ST                Run subdomain takeover
  -cors CORS            Run CORS misconfig
  -xss XSS              Run XSS scanner (dalfox) on URL or file of URLs
  -bxss BXSS            Blind XSS callback URL (used with -xss)
  --deep-xss            Enable deep DOM XSS scanning (slower)
  -methods METHODS      Scan for dangerous HTTP methods (PUT/PATCH/DELETE) on URL or file of URLs
  -o O                  output file.
```

## Attack Module - XSS Scanner (dalfox)

O modulo de XSS usa o [dalfox](https://github.com/hahwul/dalfox) de forma inteligente para encontrar vulnerabilidades de Cross-Site Scripting. A estrategia inclui:

- **Pre-filtragem**: descarta URLs sem query parameters (sem `?param=value` = sem reflected XSS), economizando tempo massivamente
- **Deduplicacao por padrao**: agrupa URLs pelo mesmo path + nomes de parametros, evitando testar `/search?q=foo` e `/search?q=bar` separadamente
- **Flags otimizadas**: `--skip-bav` (foco exclusivo em XSS), `--waf-evasion`, `--only-poc v,r` (sem falsos positivos de grep)
- **Output estruturado**: resultados em JSONL com classificacao de severidade (verified=high, reflected=medium, grep=info)

### Exemplos de uso

```bash
# Scan de XSS em arquivo de URLs
python3 ayumi.py atk -xss urls_com_params.txt -o xss_results.jsonl -v

# Scan de URL unica
python3 ayumi.py atk -xss "https://target.com/search?q=test" -v

# Com blind XSS callback
python3 ayumi.py atk -xss urls.txt -bxss https://your-callback.xss.ht -o results.jsonl

# Com deep DOM XSS (mais lento, mais profundo)
python3 ayumi.py atk -xss urls.txt --deep-xss -v

# Com headers e cookies customizados
python3 ayumi.py -H "Authorization: Bearer token123" -C "session=abc" atk -xss urls.txt -o results.jsonl

# Combinando flags
python3 ayumi.py -v -H "Authorization: Bearer token" atk -xss urls.txt -bxss https://callback.com --deep-xss -o xss_full.jsonl
```

### Requisitos

- [dalfox](https://github.com/hahwul/dalfox) instalado: `go install github.com/hahwul/dalfox/v2@latest`

### Formato de output (JSONL)

Cada linha do arquivo de output e um JSON com os seguintes campos:

```json
{
  "url": "https://target.com/page?q=payload",
  "poc": "https://target.com/page?q=%3Cscript%3Ealert(1)%3C/script%3E",
  "type": "verified",
  "param": "q",
  "severity": "high",
  "payload": "<script>alert(1)</script>",
  "evidence": "DOM object found",
  "cwe": "CWE-79",
  "inject_type": "inHTML-none"
}
```

## Attack Module - HTTP Methods Scanner (PUT/PATCH/DELETE)

O modulo de HTTP Methods detecta endpoints com metodos HTTP perigosos habilitados. Se um servidor aceita PUT, PATCH ou DELETE, isso pode permitir modificacao ou exclusao de recursos sem autorizacao.

**Estrategia:**

1. Envia **OPTIONS** para cada URL e verifica o header `Allow` / `Access-Control-Allow-Methods`
2. Para cada metodo perigoso encontrado, **confirma com request direto**
3. Se nao houver header Allow, **testa PUT, PATCH e DELETE diretamente**
4. Classifica como vulneravel se o status **nao for 405 (Method Not Allowed) ou 501 (Not Implemented)**
5. **Deduplica por origin** (scheme + host + path) para evitar testes redundantes

**Classificacao de severidade:**
- `high` - DELETE retornando 200/204, PUT/PATCH retornando 200/201/204
- `medium` - Metodos retornando 200/201/202/204 em geral
- `low` - Outros status codes que nao sao 405/501

### Exemplos de uso

```bash
# Scan de metodos HTTP em arquivo de URLs
python3 ayumi.py atk -methods urls_alive.txt -o methods_results.jsonl -v

# Scan de URL unica
python3 ayumi.py atk -methods "https://api.target.com/users" -v

# Com headers de autenticacao
python3 ayumi.py -H "Authorization: Bearer token123" atk -methods urls.txt -o results.jsonl

# Com cookies
python3 ayumi.py -C "session=abc123" atk -methods urls.txt -o results.jsonl -v
```

### Formato de output (JSONL)

```json
{
  "url": "https://api.target.com/users",
  "method": "DELETE",
  "status_code": 200,
  "severity": "high",
  "evidence": "DELETE https://api.target.com/users -> HTTP 200",
  "content_length": 42,
  "server": "nginx"
}
```

# TODO

- [ ] Add more modules in recon
- [ ] Add more modules in atk


# DISCLAIMER

You can use this tool for good and for bad. If you use it for good, you can be sure that you will make the world a better place. Otherwise, you have all my contempt. F*ck yourself.
