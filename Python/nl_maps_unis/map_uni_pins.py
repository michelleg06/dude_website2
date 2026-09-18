"""Generate one SVG map of the Netherlands per member university, with a pin
on the university's actual location.

Geometry: CBS province boundaries (WGS84) from cartomap.github.io
(nl_provinces_2025.geojson, checked into this folder). Coordinates are
projected with Web Mercator, so pin positions and the country outline share
the same projection and line up exactly.

Run from this folder:  python3 map_uni_pins.py
It writes the SVGs here and prints the pin position (in % of the viewBox)
for each map — those percentages are used by the clickable pin overlays in
members/universities/index.qmd.

No third-party dependencies.
"""

import json
import math

GEOJSON = "nl_provinces_2025.geojson"

MAP_FILL = "#cfcdcc"
PIN_FILL = "#F47F09"  # the logo's orange node

# Canvas: portrait, roughly the proportions of the old maps
CANVAS_W = 340.0
PAD = 10.0          # padding around the country outline
PAD_TOP = 42.0      # extra headroom so a pin near the north edge stays inside
PIN_HEIGHT = 40.0   # pin height in SVG units

# University locations (campus coordinates) and output filenames.
# Filenames match what members/universities/index.qmd references.
UNIVERSITIES = [
    {"file": "tilburg.svg",        "name": "Tilburg University",            "lat": 51.5632, "lon": 5.0435},
    {"file": "map_wageningen.svg", "name": "Wageningen University",         "lat": 51.9853, "lon": 5.6656},
    {"file": "merit.svg",          "name": "UNU-MERIT (Maastricht)",        "lat": 50.8540, "lon": 5.6910},
    {"file": "map_groningen.svg",  "name": "University of Groningen",       "lat": 53.2192, "lon": 6.5629},
    {"file": "map_nijmegen.svg",   "name": "Radboud University Nijmegen",   "lat": 51.8190, "lon": 5.8560},
    {"file": "map_utrecht.svg",    "name": "Utrecht University",            "lat": 52.0851, "lon": 5.1804},
    {"file": "map_amsterdam.svg",  "name": "Vrije Universiteit Amsterdam",  "lat": 52.3336, "lon": 4.8654},
    {"file": "map_rotterdam.svg",  "name": "Erasmus University Rotterdam",  "lat": 51.9175, "lon": 4.5250},
]


def mercator(lon, lat):
    """Web Mercator, unscaled (x in degrees-equivalent, y grows northward)."""
    x = math.radians(lon)
    y = math.asinh(math.tan(math.radians(lat)))
    return x, y


def iter_rings(geometry):
    if geometry["type"] == "Polygon":
        yield from geometry["coordinates"]
    elif geometry["type"] == "MultiPolygon":
        for poly in geometry["coordinates"]:
            yield from poly


def main():
    data = json.load(open(GEOJSON))

    # Project every ring once, tracking the projected bounding box
    rings = []
    xs, ys = [], []
    for feature in data["features"]:
        for ring in iter_rings(feature["geometry"]):
            pts = [mercator(lon, lat) for lon, lat in ring]
            rings.append(pts)
            xs.extend(p[0] for p in pts)
            ys.extend(p[1] for p in pts)

    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    # Uniform scale so the country fits the canvas width; height follows
    scale = (CANVAS_W - 2 * PAD) / (maxx - minx)
    canvas_h = (maxy - miny) * scale + PAD + PAD_TOP

    def to_svg(x, y):
        sx = PAD + (x - minx) * scale
        sy = PAD_TOP + (maxy - y) * scale  # flip: mercator y grows north, svg y grows down
        return sx, sy

    # One shared <path> for the whole country (all province rings)
    parts = []
    for pts in rings:
        svg_pts = [to_svg(x, y) for x, y in pts]
        # light thinning: skip points closer than half an SVG unit
        thinned = [svg_pts[0]]
        for p in svg_pts[1:]:
            if abs(p[0] - thinned[-1][0]) + abs(p[1] - thinned[-1][1]) >= 0.5:
                thinned.append(p)
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in thinned) + " Z"
        parts.append(d)
    country_path = " ".join(parts)

    # Pin drawn with its TIP at (0, 0), body extending upward, then
    # translated to the projected location — the tip marks the exact spot.
    s = PIN_HEIGHT / 36.0  # the raw pin shape below is 36 units tall
    pin_template = (
        '<g transform="translate({x:.1f} {y:.1f}) scale(%.3f)">'
        '<path fill="%s" d="M 0 0 C -7.5 -13 -13 -17.4 -13 -24 '
        'A 13 13 0 1 1 13 -24 C 13 -17.4 7.5 -13 0 0 Z"/>'
        '<circle cx="0" cy="-24" r="4.6" fill="#ffffff"/>'
        "</g>"
    ) % (s, PIN_FILL)

    for uni in UNIVERSITIES:
        px, py = to_svg(*mercator(uni["lon"], uni["lat"]))
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {CANVAS_W:.0f} {canvas_h:.0f}" '
            f'role="img" aria-label="Map of the Netherlands with a pin on {uni["name"]}">'
            f'<path fill="{MAP_FILL}" stroke="{MAP_FILL}" stroke-width="0.6" '
            f'fill-rule="evenodd" d="{country_path}"/>'
            + pin_template.format(x=px, y=py)
            + "</svg>"
        )
        with open(uni["file"], "w") as f:
            f.write(svg)
        print(
            f'{uni["file"]:<20} pin at {100 * px / CANVAS_W:5.1f}% , '
            f"{100 * py / canvas_h:5.1f}%   ({uni['name']})"
        )


if __name__ == "__main__":
    main()
