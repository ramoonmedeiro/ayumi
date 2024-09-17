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

# src libs
from src.recon.subdomain_discovery import SubdomainDiscovery
from src.recon.crawlers import Crawlers
from src.recon.js_parser import JSParser
from src.recon.extractor import LinkExtractor
from src.recon.tech_detect import TechDetect

print(Fore.LIGHTRED_EX + Settings.BANNER.value + Style.RESET_ALL)


parser = argparse.ArgumentParser()
parser.add_argument('-C', '--cookie', required=False, help='Cookie to use in requests.', default=None)
parser.add_argument('-H', '--header', required=False, help='Header to use in requests.', default=None)
parser.add_argument("-m", "--method", required=False, help="HTTP method to use in requests.", default="GET")

subparsers = parser.add_subparsers(dest='command')


# Cria o subparser para o comando 'recon'
subs_parser = subparsers.add_parser('recon')
subs_parser.add_argument('-ds', required=False, help='Discovery subdomains.')
subs_parser.add_argument('-rc', required=False, help='Run crawler (katana).')
subs_parser.add_argument('-rh', required=False, help='Run history crawler (gau and waybackurls).')
subs_parser.add_argument('-rp', required=False, help='Run Paramspider.')
subs_parser.add_argument('-el', required=False, help='Extract links from a url')
subs_parser.add_argument('-td', required=False, help='Tech detect from a url or filename.')
subs_parser.add_argument('-get-js', required=False, help='Run getJS.')
subs_parser.add_argument('-filter-js', required=False, help='Filter JS files from urls file.')
subs_parser.add_argument('-o', required=False, help='output file.')

# Cria o subparser para o comando 'atk'
atk_parser = subparsers.add_parser('atk')
# atk_parser.add_argument('-file', required=True, help='Nome do arquivo de entrada')

# Analisa os argumentos da linha de comando
args = parser.parse_args()

if args.command not in ['recon', 'atk']:
    parser.error("Comando inválido. Os comandos válidos são 'recon' e 'atk'.")

if args.command == 'recon':
    print(Fore.LIGHTMAGENTA_EX + "🌸 RECON MODE" + Style.RESET_ALL)
    if args.ds:
        print(Fore.MAGENTA + "🌿 Running subdomain discovery\n" + Style.RESET_ALL)
        subdomain_discovery = SubdomainDiscovery(domain_file=args.ds)
        subdomain_discovery.run_all(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Subdomain discovery finished" + Style.RESET_ALL)
        exit(0)

    if args.rc:
        print(Fore.MAGENTA + "🌿 Running crawler\n" + Style.RESET_ALL)
        crawler = Crawlers(domains_file=args.rc)
        crawler.run_katana(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Crawler finished" + Style.RESET_ALL)
        exit(0)

    if args.rh:
        print(Fore.MAGENTA + "🌿 Running history crawler\n" + Style.RESET_ALL)
        crawler = Crawlers(domains_file=args.rh)
        crawler.run_history(output_file=args.o)
        print(Fore.MAGENTA + "🌿 History crawler finished" + Style.RESET_ALL)
        exit(0)

    if args.rp:
        print(Fore.MAGENTA + "🌿 Running Paramspider\n" + Style.RESET_ALL)
        crawler = Crawlers(domains_file=args.rp)
        crawler.run_paramspider(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Paramspider finished" + Style.RESET_ALL)
        exit(0)

    if args.get_js:
        print(Fore.MAGENTA + "🌿 Gettings JS files\n" + Style.RESET_ALL)
        js_parser = JSParser(domains_file=args.get_js)
        js_parser.run_get_js(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Finished" + Style.RESET_ALL)
        exit(0)

    if args.filter_js:
        print(Fore.MAGENTA + "🌿 Filtering JS files\n" + Style.RESET_ALL)
        js_parser = JSParser(domains_file=args.filter_js)
        js_parser.get_js_from_file(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Finished" + Style.RESET_ALL)
        exit(0)

    if args.el:
        print(Fore.MAGENTA + "🌿 Extracting links\n" + Style.RESET_ALL + "\n")
        if "https://" in args.el or "http://" in args.el:
            le = LinkExtractor(url=args.el.strip(), method=args.method)
            links_extracted = le.extract(args.cookie, args.header)
            if args.o is not None:
                with open(args.o, 'w') as f:
                    for link in links_extracted:
                        f.write(link + '\n')
            else:
                for link in links_extracted:
                    print(link)
        else:
            with open(args.el, 'r') as f:
                urls = f.readlines()
                for url in tqdm(urls):
                    url = url.strip()
                    if validators.url(url): 
                        le = LinkExtractor(url=url, method=args.method)
                        links_extracted = le.extract(args.cookie, args.header)
                        if args.o is None:
                            args.o = 'links_extracted.txt'
                        with open(args.o, 'a') as f:
                            f.write(f"*-* Links extracted from {url}\n")
                            for link in links_extracted:
                                f.write(link + '\n')
                            f.write('\n')
                    else:
                        print(f"Ignoring invalid URL: {url}")
        print("\n"+Fore.MAGENTA + f"Results saved in {args.o}" + Style.RESET_ALL)   
        print(Fore.MAGENTA + "🌿 Finished" + Style.RESET_ALL)
        exit(0)

    if args.td:
        print(Fore.MAGENTA + "🌿 Tech detect\n" + Style.RESET_ALL + "\n")

        td = TechDetect()
        if "https://" in args.td or "http://" in args.td:
            _ = td.td_single(url=args.td)
        else:
            td.td_multi(file_name=args.td, output=args.o)
        
        print(Fore.MAGENTA + "🌿 Finished" + Style.RESET_ALL)

