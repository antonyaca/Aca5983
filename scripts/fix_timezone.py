"""Correction ponctuelle (17/10/2026) : les horodatages HistData sont en heure murale de New York (AVEC heure d'été),
pas en EST fixe. Les fichiers avaient été convertis avec +5 h fixe → décalage de +1 h pendant l'heure d'été US.
Ce script relit chaque fichier, retire les 5 h, localise en America/New_York (heure d'été gérée) et réécrit en vrai UTC.
Heure ambiguë (retour à l'heure d'hiver, 01:00-01:59) : traitée comme heure d'été ; doublons supprimés.
À n'exécuter qu'une fois : le marqueur data/TZ_FIXED empêche une double correction.
"""
import glob, os, sys
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mark = os.path.join(ROOT, "data", "TZ_FIXED")
if os.path.exists(mark):
    sys.exit("déjà corrigé")
for p in sorted(glob.glob(os.path.join(ROOT, "data", "*", "*.csv.gz"))):
    df = pd.read_csv(p, dtype=str)
    wall = pd.to_datetime(df["time"].str.replace("Z", ""), format="%Y-%m-%dT%H:%M:%S") - pd.Timedelta(hours=5)
    utc = wall.dt.tz_localize("America/New_York", ambiguous=True, nonexistent="shift_forward").dt.tz_convert("UTC")
    df["time"] = utc.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df = df.drop_duplicates("time").sort_values("time")
    df.to_csv(p, index=False, compression={"method": "gzip", "compresslevel": 6})
    print(os.path.relpath(p, ROOT), len(df), flush=True)
open(mark, "w").write("Horodatages corrigés en vrai UTC le 17/10/2026 (voir scripts/fix_timezone.py)\n")
