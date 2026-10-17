"""2e correction (17/10/2026). Constat : à partir des fichiers 2019, HistData suit l'heure d'été EUROPÉENNE
(horodatage = heure de Berlin − 6 h), pas l'heure d'été américaine. Preuve : pendant les ~3 semaines par an où les
changements d'heure US et UE ne coïncident pas, la pause quotidienne du Nasdaq (16:15 NY) apparaît à 15:15, celle de
l'or (17:00 NY) à 16:00 — en 2019-2026 uniquement ; 2011-2018 est correct.
Méthode pour les fichiers ≥ 2019 : on retrouve l'horodatage source (UTC actuel → heure de New York, naïf), puis
UTC vrai = (horodatage source + 6 h) localisé en Europe/Berlin. Ne change que les semaines de décalage.
Marqueur data/TZ_FIXED2 : exécution unique.
"""
import glob, os, re, sys
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mark = os.path.join(ROOT, "data", "TZ_FIXED2")
if os.path.exists(mark) or not os.path.exists(os.path.join(ROOT, "data", "TZ_FIXED")):
    sys.exit("déjà corrigé ou 1re correction absente")
logp = os.path.join(ROOT, "data", "TZ_FIXED2.log")   # fichiers déjà traités (reprise sûre)
done = set(open(logp).read().split()) if os.path.exists(logp) else set()
for p in sorted(glob.glob(os.path.join(ROOT, "data", "*", "*.csv.gz"))):
    if int(re.search(r"_(\d{4})\.csv\.gz$", p).group(1)) < 2019 or os.path.relpath(p, ROOT) in done:
        continue
    df = pd.read_csv(p, dtype=str)
    utc = pd.to_datetime(df["time"], utc=True)
    src = utc.dt.tz_convert("America/New_York").dt.tz_localize(None)
    new = (src + pd.Timedelta(hours=6)).dt.tz_localize("Europe/Berlin", ambiguous=True, nonexistent="shift_forward").dt.tz_convert("UTC")
    changed = int((new != utc).sum())
    df["time"] = new.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df = df.drop_duplicates("time").sort_values("time")
    df.to_csv(p, index=False, compression={"method": "gzip", "compresslevel": 6})
    open(logp, "a").write(os.path.relpath(p, ROOT) + "\n")
    print(os.path.relpath(p, ROOT), "barres déplacées :", changed, flush=True)
open(mark, "w").write("2e correction (heure d'été européenne pour 2019+) appliquée le 17/10/2026\n")
