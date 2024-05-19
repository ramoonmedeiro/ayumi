import subprocess
from colorama import Fore, Style
import re
import json


class PortScanner:
    def __init__(self) -> None:
        pass
        # self.domain_file = domain_file

    def replace_ips(self, new_value, output):
        regex_ipv4 = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        regex_ipv6 = r"\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b"

        if re.search(regex_ipv4, output):
            new_line = re.sub(regex_ipv4, new_value, output)
        elif re.search(regex_ipv6, output):
            new_line = re.sub(regex_ipv6, new_value, output)
        else:
            new_line = output

        return new_line

    def run_rustscan(self, subdomain) -> None:

        command = f"rustscan -a {subdomain} --ulimit 10000 -q"

        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        ports = result.stdout
        print(ports)
        return ports

    def parser_output(self, subdomain, ports_to_parse) -> None:
        ports = ports_to_parse.split(",")
        _d = {subdomain: [f"{subdomain}:{port.strip()}" for port in ports]}
        return _d

    def save_to_file(self, content, output_name) -> None:
        with open(output_name, "a") as f:
            json.dump(content, f, indent=4)

    def run(self, subdomain, output_name=None) -> None:
        ports = self.run_rustscan(subdomain=subdomain)
        parsed_output = self.parser_output(subdomain, ports)

        if not output_name:
            output_name = "output.json"
        self.save_to_file(parsed_output, output_name)


if __name__ == '__main__':
    ps = PortScanner()
    ps.run("cayena.com")
