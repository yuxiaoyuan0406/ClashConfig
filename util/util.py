import yaml

'''
Utilities for downloading and post-processing Clash/Mihomo subscription configs.

The provider may return different subscription formats depending on the
User-Agent. In particular, newer subscriptions may include Hysteria2 nodes,
while old Clash cores usually only support traditional proxy types such as
Trojan. This module therefore:

1. sends a Clash-like User-Agent instead of Python requests' default UA;
2. accepts normal Clash YAML directly;
3. accepts base64 subscription content containing trojan:// links;
4. filters unsupported proxy types before editing groups.
'''

from __future__ import annotations

import base64
import os
from copy import deepcopy
from typing import Iterable
from urllib.parse import parse_qs, unquote, urlparse

import yaml

# default proxy group
default_proxy_switch_group = {
    "name": "default-switch",
    "type": "url-test",
    "url": "http://www.gstatic.com/generate_204",
    "interval": 300,
    "proxies": [],
}
default_proxy_select_group = {"name": "default-select", "type": "select", "proxies": []}

# Keep this default conservative. A legacy Clash UA normally makes the provider
# filter nodes that old Clash cannot use, e.g. hysteria2.
DEFAULT_SUBSCRIPTION_USER_AGENT = os.environ.get(
    "CLASH_SUBSCRIPTION_UA", "ClashforWindows/0.20.39"
)

# This project historically handled Trojan Clash YAML. Keep only types that are
# broadly supported by Clash-like clients. Add "hysteria2" here only if the
# downstream client/core is Mihomo or another core that supports it.
SUPPORTED_PROXY_TYPES = {
    "trojan",
    "ss",
    "ssr",
    "vmess",
    "http",
    "socks5",
}

BASE_CONFIG = {
    "port": 7890,
    "socks-port": 7891,
    "allow-lan": False,
    "mode": "Rule",
    "log-level": "silent",
    "external-controller": "127.0.0.1:9090",
    "secret": "",
    "dns": {
        "enable": True,
        "ipv6": False,
        "nameserver": [
            "223.5.5.5",
            "180.76.76.76",
            "119.29.29.29",
            "117.50.11.11",
            "117.50.10.10",
            "114.114.114.114",
            "https://dns.alidns.com/dns-query",
            "https://doh.360.cn/dns-query",
        ],
        "fallback": [
            "8.8.8.8",
            "tls://dns.rubyfish.cn:853",
            "tls://1.0.0.1:853",
            "tls://dns.google:853",
            "https://dns.rubyfish.cn/dns-query",
            "https://cloudflare-dns.com/dns-query",
            "https://dns.google/dns-query",
        ],
        "fallback-filter": {
            "geoip": True,
            "ipcidr": ["240.0.0.0/4", "0.0.0.0/32", "127.0.0.1/32"],
            "domain": [
                "+.google.com",
                "+.facebook.com",
                "+.youtube.com",
                "+.xn--ngstr-lra8j.com",
                "+.google.cn",
                "+.googleapis.cn",
                "+.gvt1.com",
            ],
        },
    },
    "proxies": [],
    "proxy-groups": [
        {"name": "Proxy", "type": "select", "proxies": []},
        {"name": "DIRECT", "type": "select", "proxies": ["DIRECT"]},
    ],
    "rules": ["MATCH,Proxy"],
}

def download_config(url: str, user_agent: str | None = None) -> dict:
    """Download a subscription and return a Clash-compatible config dict.

    The old implementation assumed the response was always Clash YAML. That is
    no longer safe: providers now often inspect User-Agent and may return
    base64 URI subscriptions or include newer protocols. This function handles
    both YAML and base64 Trojan subscriptions and filters unsupported nodes.
    """
    import requests

    if not url:
        raise ValueError("Subscription url is required.")

    headers = {
        "User-Agent": user_agent or DEFAULT_SUBSCRIPTION_USER_AGENT,
        "Accept": "application/yaml,text/yaml,text/plain,*/*",
    }

    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("Connection timeout while downloading subscription.") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Request exception while downloading subscription: {exc}") from exc

    text = response.text.strip()
    if not text:
        raise RuntimeError("Subscription response is empty.")

    config = _parse_subscription_text(text)
    _filter_unsupported_proxies(config)

    if not config.get("proxies"):
        raise RuntimeError(
            "No supported proxies found. Use the provider's 'only Trojan' subscription link, "
            "or run this script with a User-Agent matching your actual client/core."
        )

    _ensure_config_shape(config)
    return config


def _parse_subscription_text(text: str) -> dict:
    yaml_config = _try_parse_yaml(text)
    if yaml_config is not None:
        return yaml_config

    decoded = _try_base64_decode(text)
    if decoded:
        yaml_config = _try_parse_yaml(decoded)
        if yaml_config is not None:
            return yaml_config
        proxies = _parse_uri_subscription(decoded.splitlines())
        if proxies:
            config = deepcopy(BASE_CONFIG)
            config["proxies"] = proxies
            config["proxy-groups"][0]["proxies"] = [p["name"] for p in proxies]
            return config

    proxies = _parse_uri_subscription(text.splitlines())
    if proxies:
        config = deepcopy(BASE_CONFIG)
        config["proxies"] = proxies
        config["proxy-groups"][0]["proxies"] = [p["name"] for p in proxies]
        return config

    raise RuntimeError("Subscription is neither valid Clash YAML nor supported URI subscription.")


def _try_parse_yaml(text: str) -> dict | None:
    try:
        config = yaml.safe_load(text)
    except yaml.YAMLError:
        return None
    if isinstance(config, dict) and isinstance(config.get("proxies"), list):
        return config
    return None


def _try_base64_decode(text: str) -> str | None:
    compact = "".join(text.split())
    if not compact:
        return None
    padding = "=" * (-len(compact) % 4)
    try:
        raw = base64.b64decode(compact + padding, validate=False)
        decoded = raw.decode("utf-8", errors="ignore").strip()
    except Exception:
        return None
    if "://" in decoded or "proxies:" in decoded:
        return decoded
    return None


def _parse_uri_subscription(lines: Iterable[str]) -> list[dict]:
    proxies: list[dict] = []
    used_names: set[str] = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        proxy = _parse_trojan_uri(line)
        if not proxy:
            continue
        proxy["name"] = _dedupe_name(proxy["name"], used_names)
        proxies.append(proxy)
    return proxies


def _parse_trojan_uri(uri: str) -> dict | None:
    if not uri.startswith("trojan://"):
        return None
    parsed = urlparse(uri)
    if not parsed.hostname or not parsed.port or not parsed.username:
        return None

    query = parse_qs(parsed.query)
    name = unquote(parsed.fragment) if parsed.fragment else parsed.hostname
    proxy = {
        "name": name,
        "type": "trojan",
        "server": parsed.hostname,
        "port": parsed.port,
        "password": unquote(parsed.username),
        "skip-cert-verify": _query_bool(query, "allowInsecure", default=True),
    }

    sni = _query_first(query, "sni") or _query_first(query, "peer")
    if sni:
        proxy["sni"] = sni
    alpn = _query_first(query, "alpn")
    if alpn:
        proxy["alpn"] = [item for item in alpn.split(",") if item]
    network = _query_first(query, "type")
    if network and network != "tcp":
        proxy["network"] = network
    return proxy


def _query_first(query: dict[str, list[str]], key: str) -> str | None:
    value = query.get(key)
    return value[0] if value else None


def _query_bool(query: dict[str, list[str]], key: str, default: bool = False) -> bool:
    value = _query_first(query, key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _dedupe_name(name: str, used: set[str]) -> str:
    base = name or "proxy"
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def _filter_unsupported_proxies(config: dict) -> None:
    proxies = config.get("proxies") or []
    supported = [p for p in proxies if p.get("type") in SUPPORTED_PROXY_TYPES]
    supported_names = {p.get("name") for p in supported}
    config["proxies"] = supported

    for group in config.get("proxy-groups") or []:
        if isinstance(group.get("proxies"), list):
            group["proxies"] = [
                name
                for name in group["proxies"]
                if name in supported_names or name in {"DIRECT", "REJECT"}
            ]


def _ensure_config_shape(data: dict) -> None:
    data.setdefault("proxies", [])
    data.setdefault("proxy-groups", [])
    data.setdefault("rules", ["MATCH,DIRECT"])
    if not data["proxy-groups"]:
        data["proxy-groups"] = deepcopy(BASE_CONFIG["proxy-groups"])
    proxy_names = [p["name"] for p in data["proxies"] if "name" in p]
    if data["proxy-groups"] and not data["proxy-groups"][0].get("proxies"):
        data["proxy-groups"][0]["proxies"] = proxy_names


def edit_config(data: dict) -> None:
    if not data:
        raise ValueError("Empty config cannot be edited.")
    group_proxy_by_name(data)

    add_rule(data)

    # change allow lan
    data["allow-lan"] = True
    # change log level
    data["log-level"] = "debug"


def add_rule(data: dict) -> None:
    data.setdefault("rules", [])
    rule = "DOMAIN,s.trojanflare.com,DIRECT"
    if rule not in data["rules"]:
        data["rules"].insert(0, rule)


def group_proxy_by_name(data: dict) -> None:
    proxies = data.get("proxies") or []
    proxy_names = [proxy["name"] for proxy in proxies if proxy.get("name")]
    if not proxy_names:
        raise ValueError("No proxy names found in config.")

    # Split names with '-' to get countries/regions. Ignore status lines such as
    # 'Valid until ...' because they do not represent a real node region.
    proxy_country = [name.split("-")[0] for name in proxy_names]
    proxy_country = [s for s in proxy_country if s and " " not in s]
    proxy_country_set = sorted(set(proxy_country))

    semi_auto_switch_group = deepcopy(default_proxy_select_group)
    semi_auto_switch_group["name"] = "Semi-Auto"

    data.setdefault("proxy-groups", [])
    if not data["proxy-groups"]:
        data["proxy-groups"].append({"name": "Proxy", "type": "select", "proxies": []})

    existing_group_names = {group.get("name") for group in data["proxy-groups"]}
    for country in proxy_country_set:
        group_name = f"{country}-Auto"
        if group_name in existing_group_names:
            continue
        country_proxies = [name for name in proxy_names if name.startswith(country + "-")]
        if not country_proxies:
            continue

        group = deepcopy(default_proxy_switch_group)
        group["name"] = group_name
        group["proxies"] = country_proxies

        semi_auto_switch_group["proxies"].append(group_name)
        data["proxy-groups"].append(group)
        existing_group_names.add(group_name)

    # Insert Semi-Auto only when there are auto groups to select.
    if semi_auto_switch_group["proxies"]:
        data["proxy-groups"][0].setdefault("proxies", [])
        if semi_auto_switch_group["name"] not in data["proxy-groups"][0]["proxies"]:
            data["proxy-groups"][0]["proxies"].insert(0, semi_auto_switch_group["name"])
        if semi_auto_switch_group["name"] not in existing_group_names:
            data["proxy-groups"].insert(0, semi_auto_switch_group)
