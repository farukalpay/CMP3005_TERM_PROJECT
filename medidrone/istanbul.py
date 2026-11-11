"""Real-geography MediDrone instance from OpenStreetMap health facilities.

Data (all open, cached in data/raw/):
  * osm_istanbul_health.json  -- 1026 OSM objects with amenity=hospital|clinic in the
    Istanbul bounding box, Overpass API snapshot (OSM base 2026-11-08), (c) OSM contributors, ODbL.
  * geoBoundaries-TUR-ADM2_simplified.geojson -- district polygons (geoBoundaries gbOpen,
    CC BY 4.0). The polygons follow the coastline, so the Bosphorus is a gap between the
    25 European and the 14 Asian districts.

Construction (deterministic given the team seed):
  1. keep named facilities that fall inside an Istanbul district of the urban core;
  2. side = 0 for European districts, 1 for Asian districts (point-in-polygon);
  3. sample n = 100 clinics uniformly at random (seed + 1);
  4. depot ("central lab") = hospital closest to the geometric median of the clinics;
  5. local equirectangular projection to kilometres around the depot;
  6. demands U[1,30], Q = 100, K = ceil(sum q / Q) + 1, crossing penalty P = 5 km.
Own implementation.
"""
from __future__ import annotations

import argparse
import json
import math

import numpy as np

from . import ROOT
from .generate import STUDENT_IDS, team_seed
from .vrpio import Instance, write_instance

ASIA = ["Adalar", "Ataşehir", "Beykoz", "Çekmeköy", "Kadıköy", "Kartal", "Maltepe", "Pendik", "Sancaktepe",
        "Sultanbeyli", "Şile", "Tuzla", "Ümraniye", "Üsküdar"]
EUROPE = ["Arnavutköy", "Avcılar", "Bağcılar", "Bahçelievler", "Bakırköy", "Başakşehir", "Bayrampaşa",
          "Beşiktaş", "Beylikdüzü", "Beyoğlu", "Büyükçekmece", "Çatalca", "Esenler", "Esenyurt", "Eyüpsultan",
          "Fatih", "Gaziosmanpaşa", "Güngören", "Kağıthane", "Küçükçekmece", "Sarıyer", "Silivri",
          "Sultangazi", "Şişli", "Zeytinburnu"]
CORE = (28.62, 40.84, 29.40, 41.24)     # lon_min, lat_min, lon_max, lat_max (urban core)
R_EARTH = 6371.0088                      # km (mean radius)


def load_districts():
    from shapely.geometry import shape
    gj = json.loads((ROOT / "data/raw/geoBoundaries-TUR-ADM2_simplified.geojson").read_text())
    out = []
    for f in gj["features"]:
        nm = f["properties"]["shapeName"]
        g = shape(f["geometry"])
        c = g.centroid
        if nm in ASIA + EUROPE and 27.8 < c.x < 30.0 and 40.7 < c.y < 41.7:
            out.append((nm, 1 if nm in ASIA else 0, g, f))
    return out


def facilities():
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    els = json.loads((ROOT / "data/raw/osm_istanbul_health.json").read_text())["elements"]
    dist = load_districts()
    tree = STRtree([g for _, _, g, _ in dist])
    rows, seen = [], set()
    for e in els:
        t = e.get("tags", {})
        if "name" not in t:
            continue
        lat = e.get("lat", e.get("center", {}).get("lat"))
        lon = e.get("lon", e.get("center", {}).get("lon"))
        if lat is None or not (CORE[0] <= lon <= CORE[2] and CORE[1] <= lat <= CORE[3]):
            continue
        key = (t["name"].strip().lower(), round(lat, 3), round(lon, 3))
        if key in seen:
            continue
        seen.add(key)
        p = Point(lon, lat)
        hit = [i for i in tree.query(p) if dist[i][2].contains(p)]
        if not hit:                                    # on the simplified coastline: nearest district
            i = int(tree.nearest(p))
            if dist[i][2].distance(p) > 0.015:        # ~1.5 km: drop (likely on water/islands)
                continue
            hit = [i]
        nm, side, _, _ = dist[hit[0]]
        rows.append(dict(osm=f"{e['type']}/{e['id']}", name=t["name"], kind=t.get("amenity"), lat=lat, lon=lon,
                         district=nm, side=side))
    return rows


def project(lat, lon, lat0, lon0):
    x = R_EARTH * math.radians(lon - lon0) * math.cos(math.radians(lat0))
    y = R_EARTH * math.radians(lat - lat0)
    return x, y


def build(seed: int, n: int = 100, P: float = 5.0, Q: int = 100):
    rows = facilities()
    rng = np.random.default_rng(seed + 1)
    idx = rng.choice(len(rows), size=n, replace=False)
    clinics = [rows[i] for i in idx]
    # geometric median (Weiszfeld) of the sampled clinics
    pts = np.array([[r["lon"], r["lat"]] for r in clinics])
    m = pts.mean(0)
    for _ in range(200):
        w = 1.0 / np.maximum(np.linalg.norm(pts - m, axis=1), 1e-9)
        m = (pts * w[:, None]).sum(0) / w.sum()
    hosp = [r for k, r in enumerate(rows) if r["kind"] == "hospital" and k not in set(idx)]
    depot = min(hosp, key=lambda r: (r["lon"] - m[0]) ** 2 + (r["lat"] - m[1]) ** 2)
    nodes = [depot] + clinics
    xy = np.array([project(r["lat"], r["lon"], depot["lat"], depot["lon"]) for r in nodes])
    xy = np.round(xy, 4)
    q = np.concatenate([[0], rng.integers(1, 31, size=n)])
    K = math.ceil(q.sum() / Q) + 1
    side = np.array([r["side"] for r in nodes])
    inst = Instance(name=f"MediDrone-IST-{seed}", n=n, Q=Q, K=K, xy=xy, q=q, rounded=False, P=P, side=side,
                    comment=f"Real Istanbul health facilities (OSM), depot {depot['name']}, km, seed {seed}")
    return inst, nodes, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", default=STUDENT_IDS)
    ap.add_argument("--P", type=float, default=5.0)
    a = ap.parse_args()
    seed = team_seed(a.ids)
    inst, nodes, rows = build(seed, P=a.P)
    out = ROOT / "data/istanbul"
    out.mkdir(parents=True, exist_ok=True)
    write_instance(out / f"{inst.name}.vrp", inst)
    import csv
    with open(out / f"{inst.name}_nodes.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["node", "osm", "name", "kind", "district", "side", "lat", "lon", "x_km", "y_km", "demand"])
        w.writeheader()
        for k, r in enumerate(nodes):
            w.writerow(dict(node=k, osm=r["osm"], name=r["name"], kind=r["kind"], district=r["district"], side=r["side"],
                            lat=r["lat"], lon=r["lon"], x_km=inst.xy[k, 0], y_km=inst.xy[k, 1], demand=int(inst.q[k])))
    with open(out / "eligible_facilities.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # districts of Istanbul only (for maps)
    feats = [f for _, _, _, f in load_districts()]
    for f in feats:
        f["properties"]["side"] = "Asia" if f["properties"]["shapeName"] in ASIA else "Europe"
    (out / "istanbul_districts.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    eu = int((inst.side[1:] == 0).sum())
    print(f"{inst.name}: eligible facilities={len(rows)}  n={inst.n}  Europe={eu} Asia={inst.n - eu}  "
          f"depot={nodes[0]['name']} ({nodes[0]['district']}, side={'Asia' if nodes[0]['side'] else 'Europe'})  "
          f"K={inst.K}  sum q={inst.q.sum()}")


if __name__ == "__main__":
    main()
