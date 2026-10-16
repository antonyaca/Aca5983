"""Télécharge et stocke les historiques M1 Dukascopy dans data/.

Un fichier par instrument et par année : data/<NOM>/<NOM>_M1_<ANNEE>.csv.gz
Les années passées déjà présentes ne sont pas retéléchargées.
L'année en cours est toujours rafraîchie (mise à jour incrémentale).

Variables d'environnement (optionnelles) :
  INSTRUMENTS  liste séparée par des virgules (ex: "XAUUSD,EURUSD"), défaut = tous
  START_YEAR   première année à télécharger, défaut = 2020
  FORCE        "1" pour tout retélécharger
"""
import datetime as dt
import glob
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

# Nom lisible -> code instrument Dukascopy
INSTRUMENTS = {
    "XAUUSD": "xauusd",
    "EURUSD": "eurusd",
    "SP500": "usa500idxusd",
    "NASDAQ100": "usatechidxusd",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def download(code, date_from, date_to, out_dir):
    cmd = [
        "npx", "-y", "dukascopy-node@1.50.0",
        "-i", code, "-from", date_from, "-to", date_to,
        "-t", "m1", "-p", "bid", "-v", "-f", "csv",
        "-dir", out_dir, "-r", "5", "-rp", "2000", "-bs", "8", "-bp", "500", "-s",
    ]
    print("  >", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    files = glob.glob(os.path.join(out_dir, "*.csv"))
    if not files:
        raise RuntimeError(f"Aucun fichier produit pour {code} {date_from}->{date_to}")
    return max(files, key=os.path.getmtime)


def count_rows(path_gz):
    with gzip.open(path_gz, "rt") as f:
        lines = f.readlines()
    if len(lines) < 2:
        return 0, None, None
    first = lines[1].split(",")[0]
    last = lines[-1].split(",")[0]
    return len(lines) - 1, first, last


def main():
    wanted = os.environ.get("INSTRUMENTS", "").strip()
    names = [n.strip().upper() for n in wanted.split(",") if n.strip()] or list(INSTRUMENTS)
    start_year = int(os.environ.get("START_YEAR") or 2020)
    force = os.environ.get("FORCE") == "1"
    today = dt.date.today()

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
            date_from = f"{year}-01-01"
            date_to = f"{year + 1}-01-01" if year < today.year else "now"
            with tempfile.TemporaryDirectory() as tmp:
                try:
                    csv_path = download(code, date_from, date_to, tmp)
                except Exception as exc:  # on continue avec les autres années
                    print(f"  {year}: ÉCHEC ({exc})", file=sys.stderr)
                    continue
                with open(csv_path, "rb") as src, gzip.open(target, "wb", compresslevel=9) as dst:
                    shutil.copyfileobj(src, dst)
            print(f"  {year}: OK -> {os.path.relpath(target, ROOT)}", flush=True)

    # Inventaire lisible des données stockées
    manifest = {}
    for path in sorted(glob.glob(os.path.join(DATA, "*", "*.csv.gz"))):
        rows, first, last = count_rows(path)
        manifest[os.path.relpath(path, DATA)] = {"bougies": rows, "debut": first, "fin": last}
    with open(os.path.join(DATA, "manifest.json"), "w") as f:
        json.dump({"maj": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                   "fichiers": manifest}, f, indent=2, ensure_ascii=False)
    print("Inventaire écrit dans data/manifest.json")


if __name__ == "__main__":
    main()
