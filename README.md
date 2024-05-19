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
  -o O                  output file.
```

To find out which flags can be used for the atk module, simply run the command below

```
$ python3 ayumi.py atk -h

options:
  -h, --help  show this help message and exit

```


# TODO

- [ ] Add more modules in recon
- [ ] Add more modules in atk


# DISCLAIMER

You can use this tool for good and for bad. If you use it for good, you can be sure that you will make the world a better place. Otherwise, you have all my contempt. F*ck yourself.
