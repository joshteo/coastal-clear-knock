"""Turn an Overpass export into the compact area.json the site loads.

Keeps house-like buildings (with their street address where OpenStreetMap
has one) and named streets for search.
"""
import json
import sys

src, out = sys.argv[1], sys.argv[2]
with open(src, encoding="utf-8") as f:
    data = json.load(f)


def r(v):
    return round(v, 6)


SKIP = {
    "garage", "garages", "shed", "roof", "carport", "industrial", "warehouse",
    "retail", "commercial", "school", "church", "construction", "greenhouse",
    "service", "hut", "parking", "kindergarten", "office", "supermarket",
}

houses, streets, addrs = [], [], []
for e in data["elements"]:
    t = e.get("tags", {})
    if e["type"] == "node":
        addrs.append((e["lat"], e["lon"], (t.get("addr:housenumber", "") + " " + t.get("addr:street", "")).strip()))
    elif "building" in t and "geometry" in e:
        if t["building"] in SKIP:
            continue
        g = [[r(p["lat"]), r(p["lon"])] for p in e["geometry"]]
        if len(g) > 2 and g[0] == g[-1]:
            g = g[:-1]
        if len(g) < 3:
            continue
        a = (t.get("addr:housenumber", "") + " " + t.get("addr:street", "")).strip()
        c = [sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g)]
        houses.append({"id": "w%d" % e["id"], "g": g, "a": a, "c": c})
    elif "highway" in t and "geometry" in e and t.get("name"):
        streets.append({"n": t["name"], "g": [[r(p["lat"]), r(p["lon"])] for p in e["geometry"]]})

# Give address-less buildings the nearest LINZ address point within ~30 m.
CELL = 0.001
grid = {}
for h in houses:
    grid.setdefault((int(h["c"][0] // CELL), int(h["c"][1] // CELL)), []).append(h)

matched = 0
LIMIT = 0.0003 ** 2
for lat, lon, label in addrs:
    if not label:
        continue
    ki, kj = int(lat // CELL), int(lon // CELL)
    best, bd = None, 1e9
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for h in grid.get((ki + dx, kj + dy), []):
                if h["a"]:
                    continue
                d2 = (h["c"][0] - lat) ** 2 + (h["c"][1] - lon) ** 2
                if d2 < bd:
                    best, bd = h, d2
    if best is not None and bd < LIMIT:
        best["a"] = label
        matched += 1

for h in houses:
    del h["c"]

with open(out, "w", encoding="utf-8") as f:
    json.dump({"houses": houses, "streets": streets}, f, separators=(",", ":"), ensure_ascii=False)

print("houses=%d streets=%d address_points=%d matched=%d with_address=%d"
      % (len(houses), len(streets), len(addrs), matched, sum(1 for h in houses if h["a"])))
if len(houses) < 1000:
    sys.exit("Too few houses in the export; Overpass probably returned an error.")
