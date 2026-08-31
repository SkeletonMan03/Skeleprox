#!/usr/bin/env python3
"""Check HTTP and SOCKS5 proxies concurrently with bounded resources."""

from __future__ import annotations

import argparse
import ipaddress
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import requests
from colorama import Fore, Style

URLS = [
    "https://icanhazip.com",
    "https://eth0.me",
    "https://ifconfig.me",
    "https://ipinfo.io/ip",
    "https://wtfismyip.com/text",
    "https://ifconfig.io",
    "https://ipecho.net/plain",
    "https://api.ipify.org",
    "https://whatismyip.akamai.com",
    "https://am.i.mullvad.net/ip",
    "http://ip-api.com/line/?fields=query",
    "https://wgetip.com",
    "https://ipcalf.com",
    "https://ipaddy.net",
    "https://checkip.amazonaws.com",
    "https://ip.liquidweb.com",
    "https://ipaddress.sh",
    "https://ipgive.me",
    "https://gifstuffapi.com/checkip/",
]
DEFAULT_TIMEOUT = 5
_SESSION_STATE = threading.local()

ASCII = Fore.BLUE + r"""
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
""" + Style.RESET_ALL


def parse_proxy_line(line: str) -> str:
    """Return the first whitespace-delimited proxy token from a line."""
    return line.strip().split(maxsplit=1)[0] if line.strip() else ""


def extract_ip(text: str) -> Optional[str]:
    """Extract the first valid IP address from a response body."""
    for token in text.split():
        candidate = token.strip("[](),;\"'")
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            continue
    return None


def proxy_host(proxy: str) -> str:
    """Return a normalized host from a host:port proxy value."""
    host = proxy.rsplit("@", 1)[-1].rsplit(":", 1)[0].strip("[]").lower()
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        return host


def get_session() -> requests.Session:
    """Reuse one HTTP session per worker thread."""
    session = getattr(_SESSION_STATE, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": "curl/8.12.1"})
        session.max_redirects = 0
        _SESSION_STATE.session = session
    return session


def check_proxy(proxy: str, proxytype: str, timeout: float) -> tuple[str, bool]:
    """Check one proxy and return its normalized value and result."""
    proxy = parse_proxy_line(proxy)
    if not proxy:
        return proxy, False

    try:
        get_session().cookies.clear()
        target = f"{proxytype}://{proxy}"
        response = get_session().get(
            random.choice(URLS),
            proxies={"http": target, "https": target},
            timeout=timeout,
            allow_redirects=False,
        )
        observed_ip = extract_ip(response.text)
        expected_ip = proxy_host(proxy)
        return proxy, observed_ip == expected_ip
    except (requests.RequestException, ValueError):
        return proxy, False


def load_proxies(path: str) -> list[str]:
    """Load non-empty, unique proxy lines while preserving input order."""
    unique = dict.fromkeys(parse_proxy_line(line) for line in Path(path).read_text().splitlines())
    unique.pop("", None)
    return list(unique)


def write_valid(path: str, proxies: list[str]) -> None:
    """Write valid proxies once, avoiding one open/close operation per result."""
    Path(path).write_text("".join(f"{proxy}\n" for proxy in proxies), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--proxylist", type=str, help="Proxy list", required=True)
    parser.add_argument("-t", "--proxytype", choices=["http", "socks5"], help="Proxy type", required=True)
    parser.add_argument("-o", "--outfile", type=str, help="Output file", required=True)
    parser.add_argument("-n", "--processes", type=int, help="Number of worker threads", required=True)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Timeout per request in seconds")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.processes < 1:
        raise SystemExit("--processes must be at least 1")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than 0")

    proxies = load_proxies(args.proxylist)
    print(ASCII)
    print(Fore.YELLOW + "| | Loaded", len(proxies), "unique proxies" + Style.RESET_ALL)
    print(Fore.CYAN + "| | Checking proxies..." + Style.RESET_ALL)

    valid: list[str] = []
    checked = 0
    with ThreadPoolExecutor(max_workers=args.processes, thread_name_prefix="proxy-check") as pool:
        for proxy, is_valid in pool.map(
            lambda item: check_proxy(item, args.proxytype, args.timeout), proxies
        ):
            checked += 1
            if is_valid:
                valid.append(proxy)
            print(
                Fore.GREEN + "| | Good proxies:", len(valid),
                Fore.RED + "| | Bad proxies:", checked - len(valid),
                Fore.MAGENTA + "| | Checked proxies:", checked,
                Style.RESET_ALL,
                end="\r",
            )

    write_valid(args.outfile, valid)
    print(f"\nWrote {len(valid)} valid proxies to {args.outfile}")


if __name__ == "__main__":
    main()
