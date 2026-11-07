"""IP and address geolocation via ipinfo.io and ArcGIS, with parallel, rate-limit-aware lookups."""
import os
import re
import threading
import time
from collections import OrderedDict
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed

import pandas
import requests
import streamlit as st

IPINFO_URL = "https://ipinfo.io/{ip}/json"
ARCGIS_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
REQUEST_TIMEOUT = 10
LOOKUP_WORKERS = 8
CACHE_TTL_SECONDS = 86400
CACHE_MAX_ENTRIES = 5000
FREE_DAILY_IP_LIMIT = 1000


class GeoLookupRateLimited(Exception):
    pass


class LookupResult:
    """Attribute access over a lookup's JSON (mirrors the fields the geocoder package exposed)."""

    def __init__(self, data: dict):
        self.json = data
        for key, value in data.items():
            if value is not None and key != "json":
                setattr(self, key, value)

    @property
    def latlng(self):
        return [self.json["lat"], self.json["lng"]]


class _TTLCache:
    """Thread-safe, size-bounded cache of successful lookups shared across sessions."""

    def __init__(self, max_entries: int, ttl: float):
        self._data, self._lock = OrderedDict(), threading.Lock()
        self._max, self._ttl = max_entries, ttl

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item is None or time.monotonic() - item[0] > self._ttl:
                self._data.pop(key, None)
                return None
            self._data.move_to_end(key)
            return item[1]

    def set(self, key, value):
        with self._lock:
            self._data[key] = (time.monotonic(), value)
            self._data.move_to_end(key)
            while len(self._data) > self._max:
                self._data.popitem(last=False)


_ip_cache = _TTLCache(CACHE_MAX_ENTRIES, CACHE_TTL_SECONDS)
_address_cache = _TTLCache(1000, CACHE_TTL_SECONDS)
_thread_local = threading.local()


def _http() -> requests.Session:
    # requests.Session is not guaranteed thread-safe, so each worker thread keeps its own.
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers["User-Agent"] = "Fetch-Analysis-Tool/5.4"
        _thread_local.session = session
    return session


def _secret(name: str):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def _get_json(url: str, params: dict) -> dict:
    try:
        response = _http().get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        raise LookupError(f"Request failed ({type(e).__name__})") from e
    if response.status_code == 429:
        raise GeoLookupRateLimited("Lookup service rate limit reached (HTTP 429). Please try again later.")
    if not response.ok:
        raise LookupError(f"No result (HTTP {response.status_code})")
    try:
        return response.json()
    except ValueError as e:
        raise LookupError("No result (invalid response)") from e


def fetch_ipinfo(ip: str, token=None) -> dict:
    """Look up one IP; raises GeoLookupRateLimited on HTTP 429 and LookupError when there is no location."""
    raw = _get_json(IPINFO_URL.format(ip=ip), {"token": token} if token else {})
    try:
        lat, lng = (float(v) for v in raw["loc"].split(","))
    except (KeyError, ValueError, AttributeError):
        raise LookupError("No result (no location for this address)")
    city, state, country = raw.get("city"), raw.get("region"), raw.get("country")
    address = ", ".join(part for part in (city, state, country) if part)
    return {
        "address": address, "city": city, "country": country, "hostname": raw.get("hostname"),
        "ip": raw.get("ip", ip), "lat": lat, "lng": lng, "ok": True, "org": raw.get("org"),
        "postal": raw.get("postal"), "raw": raw, "state": state, "status": "OK",
        "timezone": raw.get("timezone"), "provider": "ipinfo.io",
    }


def fetch_arcgis(query: str) -> dict:
    """Geocode a place name or address with the ArcGIS World Geocoding Service."""
    raw = _get_json(ARCGIS_URL, {
        "SingleLine": query, "f": "json", "maxLocations": 1,
        "outFields": "Match_addr,Addr_type,City,Region,CntryName,Postal,Score",
    })
    candidates = raw.get("candidates") or []
    if not candidates:
        raise LookupError("No result (address not found)")
    best = candidates[0]
    attrs = best.get("attributes", {})
    location = best.get("location", {})
    if location.get("x") is None or location.get("y") is None:
        raise LookupError("No result (no location for this address)")
    extent = best.get("extent") or {}
    return {
        "address": best.get("address") or attrs.get("Match_addr"),
        "bbox": {"northeast": [extent.get("ymax"), extent.get("xmax")],
                 "southwest": [extent.get("ymin"), extent.get("xmin")]} if extent else None,
        "city": attrs.get("City") or None, "country": attrs.get("CntryName") or None,
        "lat": float(location["y"]), "lng": float(location["x"]), "ok": True,
        "postal": attrs.get("Postal") or None, "quality": attrs.get("Addr_type"), "raw": best,
        "score": best.get("score", attrs.get("Score")), "state": attrs.get("Region") or None,
        "status": "OK", "provider": "ArcGIS",
    }


def cached_ip_lookup(ip: str) -> dict:
    """Cached single IP lookup (failures are not cached, so they can be retried)."""
    hit = _ip_cache.get(ip)
    if hit is None:
        hit = fetch_ipinfo(ip, _secret("IPINFO_TOKEN"))
        _ip_cache.set(ip, hit)
    return hit


def cached_ipinfo_result(ip: str) -> LookupResult:
    return LookupResult(cached_ip_lookup(ip))


def cached_arcgis_result(query: str) -> LookupResult:
    hit = _address_cache.get(query)
    if hit is None:
        hit = fetch_arcgis(query)
        _address_cache.set(query, hit)
    return LookupResult(hit)


IPV4_REGEX = re.compile(r'(?:\d{1,3}\.){3}\d{1,3}\b')


IPV6_REGEX = re.compile(r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))')


invalid_ips = ['0', '10.', '127.0.0.1','172.16', '172.17', '172.18', '172.19', '172.2',  '172.21', '172.22', '172.23', '172.24', '172.25',
            '172.26', '172.27', '172.28', '172.29', '172.30',  '172.31', '192.168', '169.254', "255.255" ,"fc00"]


def parse_text_for_IPs(text):  #used to map ips
    # Use precompiled regex objects for performance
    ipv4_addresses = IPV4_REGEX.findall(text)
    ipv6_addresses = IPV6_REGEX.findall(text)
    
    ipv6_list = []
    ip_list = list(set(ipv4_addresses))

    for address in ipv6_addresses:
        clean_ipv6 = [item for item in address if len(item) > 16]
        if clean_ipv6:      # checks for empty lists
            ipv6_list.append(clean_ipv6)
    unique_ip6_list = [str(inner_list[0]) for inner_list in ipv6_list]
    unique_ip6_list = list(set(unique_ip6_list))
    ip_list.extend(unique_ip6_list)
    return ip_list


def lookup_ips(ips, workers: int = LOOKUP_WORKERS, progress=None):
    """Look up many IPs concurrently, in input order.

    Returns (results, failed_count, rate_limited). On HTTP 429 the remaining lookups are
    cancelled; results gathered so far are kept. `progress(done, total)` is called from the
    calling thread only.
    """
    ips = list(ips)
    token = _secret("IPINFO_TOKEN")
    results, pending = {}, []
    for ip in ips:
        hit = _ip_cache.get(ip)
        if hit is not None:
            results[ip] = hit
        else:
            pending.append(ip)
    failed, rate_limited = 0, False
    stop = threading.Event()

    def task(ip):
        if stop.is_set():
            return ip, None
        return ip, fetch_ipinfo(ip, token)

    done = len(results)
    if progress:
        progress(done, len(ips))
    if pending:
        with ThreadPoolExecutor(max_workers=max(1, min(workers, len(pending)))) as pool:
            futures = [pool.submit(task, ip) for ip in pending]
            for future in as_completed(futures):
                try:
                    ip, data = future.result()
                    if data is not None:
                        _ip_cache.set(ip, data)
                        results[ip] = data
                except GeoLookupRateLimited:
                    rate_limited = True
                    stop.set()
                    for other in futures:
                        other.cancel()
                except LookupError:
                    failed += 1
                except CancelledError:
                    pass
                done += 1
                if progress:
                    progress(done, len(ips))
    return [results[ip] for ip in ips if ip in results], failed, rate_limited


def get_IP_locale(invalidList, IPs):
    """Geolocate public IPs (private/reserved prefixes in invalidList are skipped) in parallel."""
    valid_only = [address for address in IPs if not any(address.startswith(inval) for inval in invalidList)]
    if not valid_only:
        return []
    bar = st.progress(0.0, text=f"Looking up {len(valid_only)} IP address(es)...")

    def report(done, total):
        bar.progress(done / total if total else 1.0, text=f"Looked up {done} of {total} IP address(es)")

    results, failed, rate_limited = lookup_ips(valid_only, progress=report)
    bar.empty()
    if rate_limited:
        st.error(f"🚫 IP lookup limit reached (Error 429). Daily free limit ~{FREE_DAILY_IP_LIMIT}. "
                 f"Showing {len(results)} of {len(valid_only)} results. Try later or consider sponsored expansion.")
    if failed:
        st.warning(f"⚠️ {failed} IP address(es) returned no location.")
    return results


def geo_ip_to_Dataframe(geo_list):  #used to map ips
    df = pandas.json_normalize(geo_list)
    df = df.dropna(how='all') #removes entirely empty rows
    columns = df.columns
    columnnamelist = []
    for name in columns:
        columnnamelist.append(name.upper())
    df.columns = columnnamelist
    df.rename(columns={"IP": 'IP ADDRESS','LAT': 'LATITUDE', 'LNG': "LONGITUDE", 'ORG': "SERVICE PROVIDER"}, inplace=True)
    return (df)
