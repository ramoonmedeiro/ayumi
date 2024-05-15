# colors lib
from colorama import Fore, Style

# cli libs
import argparse

# lib settings
from src.settings import Settings

# src libs
from src.recon.subdomain_discovery import SubdomainDiscovery
from src.recon.crawlers import Crawlers


print(Fore.RED + Settings.BANNER.value + Style.RESET_ALL)


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')


# Cria o subparser para o comando 'recon'
subs_parser = subparsers.add_parser('recon')
subs_parser.add_argument('-ds', required=False, help='Discovery subdomains.')
subs_parser.add_argument('-rc', required=False, help='Run crawler (katana).')
subs_parser.add_argument('-rh', required=False, help='Run history crawler (gau and waybackurls).')
subs_parser.add_argument('-rp', required=False, help='Run Paramspider.')
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
