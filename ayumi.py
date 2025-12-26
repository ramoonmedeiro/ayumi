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

# atk libs
from src.atk.crlf import CRLFAtk
from src.atk.subdomain_takeover import SubdomainTakeover

print(Fore.LIGHTRED_EX + Settings.BANNER.value + Style.RESET_ALL)


parser = argparse.ArgumentParser()
parser.add_argument('-C', '--cookie', required=False, help='Cookie to use in requests.', action='append', default=None)
parser.add_argument('-H', '--header', required=False, help='Header to use in requests.', action='append', default=None)
parser.add_argument("-m", "--method", required=False, help="HTTP method to use in requests.", default="GET")

subparsers = parser.add_subparsers(dest='command')


# Cria o subparser para o comando 'recon'
subs_parser = subparsers.add_parser('recon')
subs_parser.add_argument('-ds', required=False, help='Discovery subdomains.')
subs_parser.add_argument('-rc', required=False, help='Run crawler (katana).')
subs_parser.add_argument('-rh', required=False, help='Run history crawler (urlfinder).')
subs_parser.add_argument('-el', required=False, help='Extract links from a url')
subs_parser.add_argument('-ek', required=False, help='Extract keys from a url')
subs_parser.add_argument('-td', required=False, help='Tech detect from a url or filename.')
subs_parser.add_argument('-get-js', required=False, help='Run getJS.')
subs_parser.add_argument('-filter-js', required=False, help='Filter JS files from urls file.')
subs_parser.add_argument('-o', required=False, help='output file.')

# Cria o subparser para o comando 'atk'
atk_parser = subparsers.add_parser('atk')
atk_parser.add_argument('-crlf', required=False, help='Run crlf injection')
atk_parser.add_argument('-st', required=False, help='Run subdomain takeover')
atk_parser.add_argument('-o', required=False, help='output file.')



# Analisa os argumentos da linha de comando
args = parser.parse_args()

if args.command not in ['recon', 'atk']:
    parser.error("Comando inválido. Os comandos válidos são 'recon' e 'atk'.")

if args.command == 'recon':
    print(Fore.LIGHTMAGENTA_EX + "🌸 RECON MODE" + Style.RESET_ALL)
    if args.ds:
        print(Fore.MAGENTA + "🌿 Running subdomain discovery\n" + Style.RESET_ALL)
        subdomain_discovery = SubdomainDiscovery(_input=args.ds)
        subdomain_discovery.run_all(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Subdomain discovery finished" + Style.RESET_ALL)
        exit(0)

    if args.rc:
        print(Fore.MAGENTA + "🌿 Running crawler\n" + Style.RESET_ALL)
        crawler = Crawlers(_input=args.rc)
        crawler.run_katana(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Crawler finished" + Style.RESET_ALL)
        exit(0)

    if args.rh:
        print(Fore.MAGENTA + "🌿 Running history crawler\n" + Style.RESET_ALL)
        crawler = Crawlers(_input=args.rh)
        crawler.run_urlfinder(output_file=args.o)
        print(Fore.MAGENTA + "🌿 History crawler finished" + Style.RESET_ALL)
        exit(0)

    if args.get_js:
        print(Fore.MAGENTA + "🌿 Gettings JS files\n" + Style.RESET_ALL)
        js_parser = JSParser(
            _input=args.get_js,
            headers=args.header,
            cookies=args.cookie,
            method=args.method
        )
        js_parser.run_get_js(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Finished" + Style.RESET_ALL)
        exit(0)

    if args.filter_js:
        print(Fore.MAGENTA + "🌿 Filtering JS files\n" + Style.RESET_ALL)
        js_parser = JSParser(_input=args.filter_js)
        js_parser.get_js_from_file(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Finished" + Style.RESET_ALL)
        exit(0)

    if args.el:
        print(Fore.MAGENTA + "🌿 Extracting links\n" + Style.RESET_ALL)
        le = LinkExtractor(_input=args.el)
        le.run(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Extract link finished" + Style.RESET_ALL)
        exit(0)
    
    if args.ek:
        print(Fore.MAGENTA + "🌿 Extracting keys from links\n" + Style.RESET_ALL)
        jke = JuiceKeysExtractor(_input=args.ek)
        jke.run(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Extract keys finished" + Style.RESET_ALL)
        exit(0)

    if args.td:
        print(Fore.MAGENTA + "🌿 Tech detect\n" + Style.RESET_ALL + "\n")

        td = TechDetect()
        if "https://" in args.td or "http://" in args.td:
            _ = td.td_single(url=args.td)
        else:
            td.td_multi(file_name=args.td, output=args.o)
        
        print(Fore.MAGENTA + "🌿 Finished" + Style.RESET_ALL)

if args.command == 'atk':
    print(Fore.LIGHTMAGENTA_EX + "🍁 ATTACK MODE" + Style.RESET_ALL)
    if args.crlf:
        crlf = CRLFAtk(args.crlf)
        crlf.run_all()
    #print(Fore.MAGENTA + "🍂 Finished" + Style.RESET_ALL)
    if args.st:
        print(Fore.MAGENTA + "🍂 Running subdomain takeover analysis" + Style.RESET_ALL)
        st_client = SubdomainTakeover(args.st)
        st_client.run_all(output_file=args.o)
        print(Fore.MAGENTA + "🍂 Subdomain takeover analysis finished" + Style.RESET_ALL)
