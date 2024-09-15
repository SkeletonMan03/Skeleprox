#!/bin/python3
import string
import argparse
import requests
from multiprocessing import Process, Manager
import random

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--proxylist', type=str, help='Proxy list', required=True)
parser.add_argument('-t', '--proxytype', type=str, help='Proxy Type (socks5 or http)', required=True)
parser.add_argument('-o', '--outfile', type=str, help='Output file', required=True)
parser.add_argument('-n', '--processes', type=int, help='Number of processes', required=True)
args = parser.parse_args()
proxylist = args.proxylist
outfile = args.outfile
proxytype = args.proxytype
num_processes = args.processes
if proxytype !="http" and proxytype !="socks5":
    print(f"{proxytype} is not a valid proxy type!")
    parser.print_help()
    exit()
URLs = ['https://icanhazip.com', 'https://eth0.me', 'https://ifconfig.me', 'https://ipinfo.io/ip', 'https://wtfismyip.com/text', 'https://ifconfig.io', 'https://ipecho.net/plain', 'https://ipnr.dk', 'https://api.ipify.org', 'https://whatismyip.akamai.com']
to = 3

ASCII = r"""
 _
| | _____ _        _
| |/  ___| |      | |
| |\ `--.| | _____| | ___ _ __  _ __ _____  __
| | `--. \ |/ / _ \ |/ _ \ '_ \| '__/ _ \ \/ /
| |/\__/ /   <  __/ |  __/ |_) | | | (_) >  <
| |\____/|_|\_\___|_|\___| .__/|_|  \___/_/\_\
| |                      | |
| |                      |_|
| | Just a proxy checker
| |
| | "Rate-limits don't exist if you have enough proxies" 
| |"""

def check_proxy(proxy, valid_proxies, bad_proxies, good_count, bad_count, checked_count):
    try:
        session = requests.Session()
        session.headers['User-Agent'] = 'User-Agent: curl/8.9.1'
        session.max_redirects = 0
        proxy = proxy.split('\n', 1)[0]
        random_url = random.choice(URLs)
        if proxytype == "http":
            request = session.get(random_url, proxies={"http": proxy, "https": proxy}, timeout=to, allow_redirects=False)
        elif proxytype == "socks5":
            request = session.get(random_url, proxies={"http": "socks5://"+proxy, "https": "socks5://"+proxy}, timeout=to, allow_redirects=False)
        proxyip = (request.text).strip()
        onlyip = "".join(i for i in proxy if i in (string.digits + ".:")).strip(":").split(":")[0]
        if proxyip == onlyip:
            valid_proxies.put(proxy)
            validfile = open(outfile, 'a+')
            validfile.write(proxy+'\n')
            validfile.close()
            good_count.value += 1
        else:
            bad_proxies.put(proxy)
            bad_count.value += 1
    except Exception as e:
        pass
    finally:
        checked_count.value += 1

def process(proxy_list, valid_proxies, bad_proxies, good_count, bad_count, checked_count):
    for proxy in proxy_list:
        check_proxy(proxy, valid_proxies, bad_proxies, good_count, bad_count, checked_count)

if __name__ == "__main__":
    print(ASCII)

    with open(proxylist) as f:
        proxy_list = f.readlines()

    print('| | Loaded', len(proxy_list), 'proxies')
    print('| | Checking proxies...')
    manager = Manager()
    valid_proxies = manager.Queue()
    bad_proxies = manager.Queue()
    good_count = manager.Value('i', 0)
    bad_count = manager.Value('i', 0)
    checked_count = manager.Value('i', 0)

    chunk_size = len(proxy_list) // num_processes
    processes = []
    for i in range(num_processes):
        start = i * chunk_size
        end = start + chunk_size if i < num_processes - 1 else len(proxy_list)
        p = Process(target=process, args=(proxy_list[start:end], valid_proxies, bad_proxies, good_count, bad_count, checked_count))
        p.start()
        processes.append(p)

    while len(processes) > 1:
        print('| |', 'Good proxies:', good_count.value, '| |', 'Bad proxies:', checked_count.value-good_count.value, '| |', 'Checked proxies:', checked_count.value, '| |', end='\r')

    for p in processes:
        p.join()

    print('\n')
