# colors lib
from colorama import Fore, Style

# bar time
from tqdm import tqdm

# validators
import validators

# cli libs
import argparse

# lib settings
from src.settings import Settings

# recon libs
from src.recon.subdomain_discovery import SubdomainDiscovery
from src.recon.crawlers import Crawlers
from src.recon.js_parser import JSParser
from src.recon.extractor import LinkExtractor, JuiceKeysExtractor
from src.recon.tech_detect import TechDetect
from src.recon.nuclei_client import NucleiClient
from src.recon.param_discovery import ParamDiscovery

# atk libs
from src.atk.crlf import CRLFAtk
from src.atk.subdomain_takeover import SubdomainTakeover
from src.atk.cors import CorsAnalyzer
from src.atk.xss import XSSScanner
from src.atk.http_methods import HTTPMethodScanner

# Logger
from src.logger import Logger

parser = argparse.ArgumentParser()
parser.add_argument('-C', '--cookie', required=False, help='Cookie to use in requests.', action='append', default=None)
parser.add_argument('-H', '--header', required=False, help='Header to use in requests.', action='append', default=None)
parser.add_argument("-m", "--method", required=False, help="HTTP method to use in requests.", default="GET")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode.")

subparsers = parser.add_subparsers(dest='command')


# Cria o subparser para o comando 'recon'
subs_parser = subparsers.add_parser('recon')
subs_parser.add_argument('-ds', required=False, help='Discovery subdomains.')
subs_parser.add_argument('-rc', required=False, help='Run crawler (katana).')
subs_parser.add_argument('-rh', required=False, help='Run history crawler (urlfinder).')
subs_parser.add_argument('-el', required=False, help='Extract links from a url')
subs_parser.add_argument('-ek', required=False, help='Extract keys from a url')
subs_parser.add_argument('-td', required=False, help='Tech detect from a url or filename.')
subs_parser.add_argument('-nt', required=False, help='Run nuclei normal templates.')
subs_parser.add_argument('-ct', required=False, help='Run nuclei custom templates.')
subs_parser.add_argument('-get-js', required=False, help='Run getJS.')
subs_parser.add_argument('-filter-js', required=False, help='Filter JS files from urls file.')
subs_parser.add_argument('-dp', required=False, help='Discover hidden parameters on URL or file of URLs (x8).')
subs_parser.add_argument('-wl', required=False, help='Custom wordlist for parameter discovery (used with -dp).')
subs_parser.add_argument('-o', required=False, help='output file.')

# Cria o subparser para o comando 'atk'
atk_parser = subparsers.add_parser('atk')
atk_parser.add_argument('-crlf', required=False, help='Run crlf injection')
atk_parser.add_argument('-st', required=False, help='Run subdomain takeover')
atk_parser.add_argument('-cors', required=False, help='Run CORS misconfig')
atk_parser.add_argument('-xss', required=False, help='Run XSS scanner (dalfox) on URL or file of URLs')
atk_parser.add_argument('-bxss', required=False, help='Blind XSS callback URL (used with -xss)')
atk_parser.add_argument('--deep-xss', action='store_true', help='Enable deep DOM XSS scanning (slower)')
atk_parser.add_argument('-methods', required=False, help='Scan for dangerous HTTP methods (PUT/PATCH/DELETE) on URL or file of URLs')
atk_parser.add_argument('-o', required=False, help='output file.')



# Analisa os argumentos da linha de comando
args = parser.parse_args()
log = Logger(verbose=args.verbose)

# Banner inicial
log.info(Settings.BANNER.value, Fore.LIGHTRED_EX)

if args.command not in ['recon', 'atk']:
    parser.error("Comando inválido. Os comandos válidos são 'recon' e 'atk'.")

# --- MODO RECON ---
if args.command == 'recon':
    log.info("🌸 RECON MODE", Fore.LIGHTMAGENTA_EX)

    if args.ds:
        log.info("🌿 Running subdomain discovery\n")
        subdomain_discovery = SubdomainDiscovery(_input=args.ds, verbose=args.verbose)
        subdomain_discovery.run_all(output_file=args.o)
        log.info("🌿 Subdomain discovery finished")
        exit(0)

    if args.rc:
        log.info("🌿 Running crawler\n")
        crawler = Crawlers(_input=args.rc, verbose=args.verbose)
        crawler.run_katana(output_file=args.o)
        log.info("🌿 Crawler finished")
        exit(0)

    if args.rh:
        log.info("🌿 Running history crawler\n")
        crawler = Crawlers(_input=args.rh, verbose=args.verbose)
        crawler.run_urlfinder(output_file=args.o)
        log.info("🌿 History crawler finished")
        exit(0)

    if args.get_js:
        log.info("🌿 Gettings JS files\n")
        js_parser = JSParser(
            _input=args.get_js,
            headers=args.header,
            cookies=args.cookie,
            method=args.method,
            verbose=args.verbose
        )
        js_parser.run_get_js(output_file=args.o)
        log.info("🌿 Finished")
        exit(0)

    if args.filter_js:
        log.info("🌿 Filtering JS files\n")
        js_parser = JSParser(_input=args.filter_js, verbose=args.verbose)
        js_parser.get_js_from_file(output_file=args.o)
        log.info("🌿 Finished")
        exit(0)

    if args.el:
        log.info("🌿 Extracting links\n")
        le = LinkExtractor(_input=args.el, verbose=args.verbose)
        le.run(output_file=args.o)
        log.info("🌿 Extract link finished")
        exit(0)
    
    if args.ek:
        log.info("🌿 Extracting keys from links\n")
        jke = JuiceKeysExtractor(_input=args.ek, verbose=args.verbose)
        jke.run(output_file=args.o)
        log.info("🌿 Extract keys finished")
        exit(0)

    if args.td:
        log.info("🌿 Tech detect\n")
        td = TechDetect(verbose=args.verbose)
        if "https://" in args.td or "http://" in args.td:
            td.td_single(url=args.td)
        else:
            td.td_multi(file_name=args.td, output=args.o)
        log.info("🌿 Finished")

    if args.nt:
        log.info("🌿 Run normal templates nuclei\n")
        nc = NucleiClient(_input=args.nt, verbose=args.verbose)
        nc.run_normal_templates(output_file=args.o)
        log.info("🌿 Run normal templates nuclei finished")
        exit(0)

    if args.ct:
        log.info("🌿 Run custom templates nuclei\n")
        nc = NucleiClient(_input=args.ct, verbose=args.verbose)
        nc.run_custom_templates(output_file=args.o)
        log.info("🌿 Run custom templates nuclei finished")
        exit(0)

    if args.dp:
        log.info("🔍 Discovering hidden parameters (x8)\n")
        cookie_str = None
        if args.cookie:
            cookie_str = "; ".join(args.cookie)

        pd = ParamDiscovery(
            _input=args.dp,
            verbose=args.verbose,
            wordlist=args.wl,
            headers=args.header or [],
            cookies=cookie_str,
        )
        pd.run_all(output_file=args.o)
        log.info("🔍 Parameter discovery finished")
        exit(0)


# --- MODO ATTACK ---
if args.command == 'atk':
    log.info("🍁 ATTACK MODE", Fore.LIGHTMAGENTA_EX)
    
    if args.crlf:
        log.info("🍂 Running CRLF injection")
        crlf = CRLFAtk(args.crlf)
        crlf.run_all()
        log.info("🍂 CRLF injection finished")

    if args.st:
        log.info("🍂 Running subdomain takeover analysis")
        st_client = SubdomainTakeover(domain_file=args.st, verbose=args.verbose)
        st_client.run_all(output_file=args.o)
        log.info("🍂 Subdomain takeover analysis finished")
    
    if args.cors: # Supondo que você criou essa flag
        log.info("🍁 CORS ANALYSIS MODE", Fore.LIGHTMAGENTA_EX)
        cors_client = CorsAnalyzer(_input=args.cors, verbose=args.verbose)
        cors_client.run_all(output_file=args.o)
        log.info("🍂 CORS analysis finished")

    if args.xss:
        log.info("🎯 XSS SCANNER MODE (dalfox)", Fore.LIGHTMAGENTA_EX)
        # Monta cookies como string a partir da lista de -C
        cookie_str = None
        if args.cookie:
            cookie_str = "; ".join(args.cookie)

        xss_client = XSSScanner(
            _input=args.xss,
            verbose=args.verbose,
            blind_url=args.bxss,
            headers=args.header or [],
            cookies=cookie_str,
            deep=args.deep_xss,
        )
        xss_client.run_all(output_file=args.o)
        log.info("🎯 XSS scan finished")

    if args.methods:
        log.info("🔓 HTTP METHODS SCANNER MODE", Fore.LIGHTMAGENTA_EX)
        cookie_str = None
        if args.cookie:
            cookie_str = "; ".join(args.cookie)

        methods_client = HTTPMethodScanner(
            _input=args.methods,
            verbose=args.verbose,
            headers=args.header or [],
            cookies=cookie_str,
        )
        methods_client.run_all(output_file=args.o)
        log.info("🔓 HTTP methods scan finished")