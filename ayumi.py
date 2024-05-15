# colors lib
from colorama import Fore, Style

# cli libs
import argparse

# lib settings
from src.settings import Settings

# src libs
from src.recon.subdomain_discovery import SubdomainDiscovery


print(Fore.RED + Settings.BANNER.value + Style.RESET_ALL)


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')


# Cria o subparser para o comando 'recon'
subs_parser = subparsers.add_parser('recon')
subs_parser.add_argument('-ss', required=True, help='scan subdomains')
subs_parser.add_argument('-o', required=False, help='output file.')  # Adicionado aqui

# Cria o subparser para o comando 'atk'
atk_parser = subparsers.add_parser('atk')
# atk_parser.add_argument('-file', required=True, help='Nome do arquivo de entrada')

# Analisa os argumentos da linha de comando
args = parser.parse_args()

# if not args.no_banner:
#    print(Fore.RED + Settings.BANNER.value + Style.RESET_ALL)

if args.command not in ['recon', 'atk']:
    parser.error("Comando inválido. Os comandos válidos são 'recon' e 'atk'.")

if args.command == 'recon':
    print(Fore.LIGHTMAGENTA_EX + "🌸 RECON MODE" + Style.RESET_ALL)
    if args.ss:
        print(Fore.MAGENTA + "🌿 Running subdomain discovery\n" + Style.RESET_ALL)
        subdomain_discovery = SubdomainDiscovery(domain_file=args.ss)
        subdomain_discovery.run_all(output_file=args.o)
        print(Fore.MAGENTA + "🌿 Subdomain discovery finished" + Style.RESET_ALL)
        exit(0)
