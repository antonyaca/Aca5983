"""Télécharge et stocke les historiques M1 (source : HistData.com, gratuite) dans data/.

Un fichier par instrument et par année : data/<NOM>/<NOM>_M1_<ANNEE>.csv.gz
Colonnes : time (UTC, ISO), open, high, low, close, volume
Les années passées déjà présentes ne sont pas retéléchargées.
L'année en cours est reconstruite mois par mois à chaque passage (mise à jour incrémentale).

Variables d'environnement (optionnelles) :
  INSTRUMENTS  liste séparée par des virgules (ex: "XAUUSD,EURUSD"), défaut = tous
  START_YEAR   première année à télécharger, défaut = 2020
  FORCE        "1" pour tout retélécharger
"""
import datetime as dt
import glob
import gzip
import http.cookiejar
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile

# Nom lisible -> code HistData
INSTRUMENTS = {
    "XAUUSD": "xauusd",
    "EURUSD": "eurusd",
    "SP500": "spxusd",
    "NASDAQ100": "nsxusd",
    "DAX": "grxeur",
    "CAC40": "frxeur",
    "EUROSTOXX50": "etxeur",
    "WTI": "wtiusd",
    "XAGUSD": "xagusd",
    "FTSE100": "ukxgbp",
    "NIKKEI225": "jpxjpy",
    "GBPUSD": "gbpusd",
    "USDJPY": "usdjpy",
    "AUDUSD": "audusd",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
BASE = "https://www.histdata.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
# HistData horodate en heure murale de New York (heure d'été incluse), malgré sa documentation « EST fixe »
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
BERLIN = ZoneInfo("Europe/Berlin")

_jar = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_jar))


def _get(url, data=None, referer=None):
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers)
    with _opener.open(req, timeout=120) as r:
        return r.read()


def download_zip(code, year, month=None):
    """Renvoie le contenu CSV brut (bytes) pour une année ou un mois, ou None si indisponible."""
    path = f"/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{code}/{year}"
    if month:
        path += f"/{month}"
    page_url = BASE + path
    html = _get(page_url).decode("utf-8", "ignore")
    fields = dict(re.findall(r'<input[^>]*id="(\w+)"[^>]*value="([^"]*)"', html))
    if "tk" not in fields:
        return None
    form = {
        "tk": fields["tk"],
        "date": fields.get("date", str(year)),
        "datemonth": fields.get("datemonth", f"{year}{month:02d}" if month else str(year)),
        "platform": "ASCII",
        "timeframe": "M1",
        "fxpair": fields.get("fxpair", code.upper()),
    }
    raw = _get(BASE + "/get.php", data=form, referer=page_url)
    if raw[:2] != b"PK":
        return None
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = next((n for n in z.namelist() if n.lower().endswith(".csv")), None)
        return z.read(name) if name else None


def convert(raw_csv):
    """'20250101 180000;o;h;l;c;v' (EST) -> lignes 'ISO_UTC,o,h,l,c,v'."""
    out = []
    for line in raw_csv.decode("utf-8", "ignore").splitlines():
        parts = line.strip().split(";")
        if len(parts) < 6:
            continue
        try:
            # Horodatage HistData = heure murale de New York AVEC heure d'été (vérifié le 17/10/2026 :
            # pic d'ouverture du Nasdaq et du NFP décalés d'1 h l'été avec un +5 h fixe).
            # Depuis 2019, l'horloge source suit l'heure d'été européenne (= heure de Berlin − 6 h).
            wall = dt.datetime.strptime(parts[0], "%Y%m%d %H%M%S")
            if wall.year >= 2019:
                t = (wall + dt.timedelta(hours=6)).replace(tzinfo=BERLIN)
            else:
                t = wall.replace(tzinfo=NY)
            t = t.astimezone(dt.timezone.utc).replace(tzinfo=None)
        except ValueError:
            continue
        out.append(f"{t:%Y-%m-%dT%H:%M:%SZ},{parts[1]},{parts[2]},{parts[3]},{parts[4]},{parts[5]}")
    return out


def write_gz(path, rows):
    rows = sorted(set(rows))
    with gzip.open(path, "wt", compresslevel=9) as f:
        f.write("time,open,high,low,close,volume\n")
        f.write("\n".join(rows) + "\n")
    return len(rows)


def main():
    wanted = os.environ.get("INSTRUMENTS", "").strip()
    names = [n.strip().upper() for n in wanted.split(",") if n.strip()] or list(INSTRUMENTS)
    start_year = int(os.environ.get("START_YEAR") or 2020)
    force = os.environ.get("FORCE") == "1"
    today = dt.date.today()
    failures = 0

    for name in names:
        if name not in INSTRUMENTS:
            print(f"Instrument inconnu ignoré : {name}")
            continue
        code = INSTRUMENTS[name]
        folder = os.path.join(DATA, name)
        os.makedirs(folder, exist_ok=True)
        print(f"== {name} ({code})", flush=True)

        for year in range(start_year, today.year + 1):
            target = os.path.join(folder, f"{name}_M1_{year}.csv.gz")
            if os.path.exists(target) and year < today.year and not force:
                print(f"  {year}: déjà présent, ignoré")
                continue
            try:
                rows = []
                if year < today.year:
                    raw = download_zip(code, year)
                    if raw is None:  # certaines années récentes ne sont publiées que par mois
                        for m in range(1, 13):
                            r = download_zip(code, year, m)
                            if r:
                                rows += convert(r)
                            time.sleep(1)
                    else:
                        rows = convert(raw)
                else:
                    for m in range(1, today.month + 1):
                        r = download_zip(code, year, m)
                        if r:
                            rows += convert(r)
                        time.sleep(1)
                if not rows:
                    raise RuntimeError("aucune donnée renvoyée")
                n = write_gz(target, rows)
                print(f"  {year}: OK, {n} bougies", flush=True)
            except Exception as exc:
                failures += 1
                print(f"  {year}: ÉCHEC ({exc})", file=sys.stderr, flush=True)
            time.sleep(2)

    # Inventaire lisible des données stockées
    manifest = {}
    for path in sorted(glob.glob(os.path.join(DATA, "*", "*.csv.gz"))):
        with gzip.open(path, "rt") as f:
            lines = f.read().splitlines()
        manifest[os.path.relpath(path, DATA)] = {
            "bougies": max(len(lines) - 1, 0),
            "debut": lines[1].split(",")[0] if len(lines) > 1 else None,
            "fin": lines[-1].split(",")[0] if len(lines) > 1 else None,
        }
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    with open(os.path.join(DATA, "manifest.json"), "w") as f:
        json.dump({"maj": now, "source": "HistData.com (M1, bid)", "fichiers": manifest},
                  f, indent=2, ensure_ascii=False)
    print(f"Inventaire écrit dans data/manifest.json ({failures} échec(s))")


if __name__ == "__main__":
    main()
