#!/bin/bash

echo "[+] Update and upgrade"
sudo apt-get update -y
sudo apt-get upgrade -y
echo "Update and upgrade done"

echo "[+] Install pip3"
sudo apt-get install python3-pip -y
echo "Pip3 installed"

echo "[+] Install golang"
wget https://go.dev/dl/go1.22.5.linux-amd64.tar.gz
rm -rf /usr/local/go && tar -C /usr/local -xzf go1.22.5.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
rm go1.22.5.linux-amd64.tar.gz
echo "Golang installed"

echo "[+] Install subdomain enumeration"
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/tomnomnom/assetfinder@latest
go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest
go install -v github.com/hakluke/haktrails@latest

echo "Subdomain enumeration installed"

echo "[+] Install httpx"
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
echo "Httpx installed"

echo "[+] Install crawlers"
cd ~/
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/projectdiscovery/urlfinder/cmd/urlfinder@latest
pip install .
echo "Crawlers installed"
cd ~/

echo "Install getJS"
go install github.com/003random/getJS/v2@latest

echo "[+] Install nuclei"
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
~/go/bin/nuclei -update-templates
echo "Nuclei installed"

echo "[+] Install anew"
go install -v github.com/tomnomnom/anew@latest
echo "Anew installed"

echo "[+] Passando tudo para /usr/bin"
sudo mv ~/go/bin/* /usr/bin/