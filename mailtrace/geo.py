"""IP hosting context. Demo pins stay exact; everything else uses MMDB then cache/live."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from ipaddress import ip_address
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE_PATH = DATA / "geo_cache.json"
DEFAULT_MMDB = DATA / "GeoLite2-City.mmdb"
DEFAULT_ASN_MMDB = DATA / "GeoLite2-ASN.mmdb"

# Fixture IPs from sample .eml files. Tests pin these exact values.
DEMO_GEO = {
    "18.184.10.20": {"city": "Frankfurt", "isp": "AWS", "kind": "cloud", "lat": 50.1109, "lon": 8.6821},
    "52.94.76.10": {"city": "Dublin", "isp": "AWS", "kind": "cloud", "lat": 53.3498, "lon": -6.2603},
    "8.8.8.8": {"city": "unknown", "isp": "public-dns", "kind": "other", "lat": None, "lon": None},
    "103.25.60.12": {"city": "Chandigarh", "isp": "campus-like", "kind": "org", "lat": 30.7333, "lon": 76.7794},
    "185.199.108.153": {"city": "unknown", "isp": "fastly", "kind": "cdn", "lat": None, "lon": None},
}

_CLOUD_RE = re.compile(
    r"amazon|aws|google|gcp|azure|microsoft|digitalocean|linode|hetzner|ovh|oracle cloud|alibaba",
    re.I,
)
_CDN_RE = re.compile(r"cloudflare|fastly|akamai|cloudfront|edgecast", re.I)
_PROXY_RE = re.compile(r"\b(tor|vpn|proxy|anonymiz)\b", re.I)

_city_reader = None
_asn_reader = None
_cache: dict[str, Any] | None = None


def _truthy(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def _private(ip: str) -> bool:
    try:
        obj = ip_address(ip)
    except ValueError:
        return True
    return bool(obj.is_private or obj.is_loopback or obj.is_link_local or obj.is_multicast or obj.is_reserved)


def _kind(isp: str, org: str = "") -> str:
    blob = f"{isp} {org}"
    if _PROXY_RE.search(blob):
        return "proxy"
    if _CDN_RE.search(blob):
        return "cdn"
    if _CLOUD_RE.search(blob):
        return "cloud"
    if isp and isp not in {"unknown", "public-dns"}:
        return "org"
    return "other"


def _blank(ip: str, *, source: str, status: str) -> dict[str, Any]:
    return {
        "ip": ip,
        "city": "unknown",
        "isp": "unknown",
        "kind": "internal" if not ip or _private(ip) else "unknown",
        "lat": None,
        "lon": None,
        "asn": None,
        "org": "",
        "country": "unknown",
        "source": source,
        "status": status,
    }


def status() -> dict[str, Any]:
    city_db = Path(os.getenv("MAILTRACE_GEOIP_DB", "") or DEFAULT_MMDB)
    asn_db = Path(os.getenv("MAILTRACE_GEOIP_ASN_DB", "") or DEFAULT_ASN_MMDB)
    return {
        "live": _truthy("MAILTRACE_LIVE_GEO"),
        "city_mmdb": str(city_db) if city_db.is_file() else None,
        "asn_mmdb": str(asn_db) if asn_db.is_file() else None,
        "cache": CACHE_PATH.is_file(),
        "note": "Hosting/infrastructure context for public hops, not a person's GPS.",
    }


def _load_cache() -> dict[str, Any]:
    global _cache
    if _cache is None:
        if CACHE_PATH.is_file():
            try:
                _cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                _cache = {}
        else:
            _cache = {}
    return _cache


def _save_cache() -> None:
    if _cache is None:
        return
    DATA.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(_cache, indent=2, sort_keys=True), encoding="utf-8")


def _readers() -> tuple[Any, Any]:
    global _city_reader, _asn_reader
    try:
        import maxminddb
    except ImportError:
        return None, None
    city_db = Path(os.getenv("MAILTRACE_GEOIP_DB", "") or DEFAULT_MMDB)
    asn_db = Path(os.getenv("MAILTRACE_GEOIP_ASN_DB", "") or DEFAULT_ASN_MMDB)
    if _city_reader is None:
        _city_reader = maxminddb.open_database(str(city_db)) if city_db.is_file() else False
    if _asn_reader is None:
        _asn_reader = maxminddb.open_database(str(asn_db)) if asn_db.is_file() else False
    city = None if _city_reader is False else _city_reader
    asn = None if _asn_reader is False else _asn_reader
    return city, asn


def _from_mmdb(ip: str) -> dict[str, Any] | None:
    city_reader, asn_reader = _readers()
    if not city_reader:
        return None
    try:
        rec = city_reader.get(ip)
    except Exception:
        return None
    if not rec:
        return None
    city = ((rec.get("city") or {}).get("names") or {}).get("en") or "unknown"
    country = ((rec.get("country") or {}).get("names") or {}).get("en") or "unknown"
    loc = rec.get("location") or {}
    lat = loc.get("latitude")
    lon = loc.get("longitude")
    isp = "unknown"
    org = ""
    asn = None
    if asn_reader:
        try:
            asn_rec = asn_reader.get(ip) or {}
            asn = asn_rec.get("autonomous_system_number")
            org = asn_rec.get("autonomous_system_organization") or ""
            isp = org or isp
        except Exception:
            pass
    return {
        "ip": ip,
        "city": city,
        "isp": isp,
        "kind": _kind(isp, org),
        "lat": lat,
        "lon": lon,
        "asn": asn,
        "org": org,
        "country": country,
        "source": "maxmind-mmdb",
        "status": "known" if city != "unknown" or lat is not None or (isp not in {"", "unknown"}) else "unknown",
    }


def _from_ip_api(ip: str) -> dict[str, Any] | None:
    if not _truthy("MAILTRACE_LIVE_GEO"):
        return None
    url = f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,isp,org,as,query"
    try:
        with urllib.request.urlopen(url, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    if data.get("status") != "success":
        return None
    isp = data.get("isp") or "unknown"
    org = data.get("org") or ""
    return {
        "ip": ip,
        "city": data.get("city") or "unknown",
        "isp": isp,
        "kind": _kind(isp, org),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "asn": data.get("as"),
        "org": org,
        "country": data.get("country") or "unknown",
        "source": "ip-api",
        "status": "known",
    }


def lookup_ip(ip: str) -> dict[str, Any]:
    ip = (ip or "").strip("[]").strip()
    if not ip:
        return _blank("", source="none", status="unknown")
    if ip in DEMO_GEO:
        return {"ip": ip, "asn": None, "org": "", "country": "unknown", "source": "offline-demo-table", "status": "known", **DEMO_GEO[ip]}
    if _private(ip):
        return _blank(ip, source="rfc1918", status="unknown")

    cache = _load_cache()
    if ip in cache:
        row = dict(cache[ip])
        row.setdefault("ip", ip)
        row["source"] = str(row.get("source") or "cache")
        return row

    row = _from_mmdb(ip)
    if not row:
        row = _from_ip_api(ip)
    if not row:
        row = _blank(ip, source="unresolved", status="unknown")
    if row.get("status") == "known":
        cache[ip] = row
        _save_cache()
    return row
