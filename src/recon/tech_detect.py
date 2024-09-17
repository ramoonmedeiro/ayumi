from builtwith import builtwith
from colorama import Fore, Style
import json
from tqdm import tqdm


class TechDetect:
    def __init__(self):
        pass

    def td_single(self, url: str):
        try:
            techs = builtwith(url)
        except UnicodeDecodeError:
            print(Fore.RED + f"Erro de codificação ao tentar acessar {url}" + Style.RESET_ALL)
            return {}

        print(Fore.GREEN + url + Style.RESET_ALL)
        for key, value in techs.items():
            print(f"{key}: {value}")
        print("\n")
        
        return techs

    def td_multi(
        self, 
        file_name: str, 
        output: str
    ):

        if output is None:
            output = "output-td.txt"
        with open(file_name, "r") as arquivo:
            urls = arquivo.readlines()
        
        for url in tqdm(urls):
            url = url.strip()
            techs = self.td_single(url=url)
            techs_str = json.dumps(techs, indent=4)
            
            with open(output, "a") as arquivo2:
                arquivo2.write(f"*** {url} ***\n")
                arquivo2.write(techs_str + "\n\n")
        
        return
