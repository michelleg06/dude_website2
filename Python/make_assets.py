"""Regenerate every derived brand asset from the two masters in images/sources/.

    python3 Python/make_assets.py

Masters (never edited by this script):
    images/sources/logo-master.png            full logo, transparent background
    images/sources/hero-workshop-original.jpg the hero photo, uncropped

Everything else under images/ (logo variants, favicons, hero crops, social card) and the event thumbnails are generated here, so a colour or wording change is a one-line edit plus a re-run.

Note: the social card and the event thumbnail are typeset in Avenir Next, which ships with macOS. On another OS pick a different FONT_PATH below.
"""

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "images" / "sources"
LOGO_MASTER = SOURCES / "logo-master.png"
HERO_MASTER = SOURCES / "hero-workshop-original.jpg"

# brand palette — keep in sync with the :root tokens in theme.css
NAVY = (13, 39, 87)
ORANGE = (244, 127, 9)
SAND = (250, 246, 241)
BLUE_50 = (238, 243, 250)
ORANGE_INK = (180, 83, 11)
MUTED = (75, 85, 104)

# the hero crop, found by matching the framing we were given against the
# original photo (2500x1667): full width, 938px tall starting at y=485
HERO_CROP = (0, 485, 2500, 1423)

FONT_PATH = "/System/Library/Fonts/Avenir Next.ttc"
FONT_DEMI, FONT_REGULAR = 2, 7


def font(size, index=FONT_DEMI):
    return ImageFont.truetype(FONT_PATH, size, index=index)


def save(img, relative_path, **kwargs):
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, **kwargs)
    print(f"  {relative_path}  {img.size[0]}x{img.size[1]}  {path.stat().st_size // 1024} KB")


# --------------------------------------------------------------------------
# logo variants
# --------------------------------------------------------------------------

def split_master():
    """Return (full lockup, symbol only), both trimmed to their ink."""
    master = Image.open(LOGO_MASTER).convert("RGBA")
    full = master.crop(master.getchannel("A").getbbox())

    # the symbol and the wordmark are separated by the widest empty column run
    alpha = full.getchannel("A")
    columns = [max(alpha.crop((x, 0, x + 1, full.height)).getdata()) for x in range(full.width)]
    gaps, start = [], None
    for x, ink in enumerate(columns + [1]):
        if ink <= 8 and start is None:
            start = x
        elif ink > 8 and start is not None:
            gaps.append((start, x))
            start = None
    split_at = max(gaps, key=lambda g: g[1] - g[0])[0]

    symbol = full.crop((0, 0, split_at, full.height))
    return full, symbol.crop(symbol.getchannel("A").getbbox())


def knockout(img):
    """Recolour for dark backgrounds: ink becomes white, the orange node stays.

    The artwork carries emphasis in lightness — deep navy strokes read strong,
    pale blue ones read quiet. Painting every stroke solid white would flip that
    hierarchy, so a stroke's original lightness is traded for transparency.
    """
    out = img.copy()
    pixels = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if r > 150 and b < 110 and r - b > 90:  # the orange node
                continue
            luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            weight = min(1.0, max(0.30, 1.18 - 1.2 * luma))  # navy -> solid white, pale blue -> ~35%
            pixels[x, y] = (255, 255, 255, int(round(a * weight)))
    return out


def resized(img, height=None, width=None):
    if height:
        width = round(img.width * height / img.height)
    else:
        height = round(img.height * width / img.width)
    return img.resize((width, height), Image.LANCZOS)


def icon_tile(symbol, size):
    """The white symbol centred on a navy tile with softly rounded corners."""
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle([0, 0, size - 1, size - 1], radius=round(size * 0.18), fill=NAVY + (255,))
    mark = resized(knockout(symbol), height=round(size * 0.68))
    tile.paste(mark, ((size - mark.width) // 2, (size - mark.height) // 2), mark)
    return tile


def build_logos():
    print("logos")
    full, symbol = split_master()

    save(resized(symbol, height=320), "images/logos/logo-mark.png", optimize=True)
    save(resized(knockout(symbol), height=320), "images/logos/logo-mark-white.png", optimize=True)
    save(resized(full, width=1000), "images/logos/logo-full.png", optimize=True)
    save(resized(knockout(full), width=1000), "images/logos/logo-full-white.png", optimize=True)

    # Icons put the white symbol on a navy tile. On its own the symbol is mostly
    # thin pale strokes, which disappear at tab size; reversed on navy it still
    # reads as a network, and the orange node survives as a spot of colour.
    save(icon_tile(symbol, 64), "images/favicon.png", optimize=True)
    save(icon_tile(symbol, 180), "images/apple-touch-icon.png", optimize=True)

    return full, symbol


# --------------------------------------------------------------------------
# hero photo
# --------------------------------------------------------------------------

def build_hero():
    print("hero")
    photo = Image.open(HERO_MASTER).convert("RGB").crop(HERO_CROP)
    save(resized(photo, width=2400), "images/hero-workshop@2x.jpg", quality=78, optimize=True, progressive=True)
    save(resized(photo, width=1400), "images/hero-workshop.jpg", quality=80, optimize=True, progressive=True)
    return photo


def build_social_card(photo, logo_full):
    """1200x630 link preview: white logo on a navy panel, photo alongside it.

    The logo sits on flat navy rather than on the photo — over the sunlit wall
    the white wordmark would wash out at the size these previews are shown.
    """
    print("social card")
    width, height, panel = 1200, 630, 690

    card = resized(photo, height=height)  # cover-crop, keeping the speaker clear of the panel edge
    left = max(0, (card.width - width) // 2 - 180)
    card = card.crop((left, 0, left + width, height)).convert("RGBA")

    scrim = Image.new("RGBA", (width, height), NAVY + (0,))
    draw = ImageDraw.Draw(scrim)
    for x in range(width):
        if x < panel - 160:
            alpha = 255
        elif x < panel:
            alpha = int(255 - 175 * (x - panel + 160) / 160)  # fade the panel into the photo
        else:
            alpha = 80  # a light veil over the photo ties the two halves together
        draw.line([(x, 0), (x, height)], fill=NAVY + (alpha,))
    card = Image.alpha_composite(card, scrim)

    logo = resized(knockout(logo_full), width=500)
    card.paste(logo, (76, (height - logo.height) // 2 - 20), logo)
    ImageDraw.Draw(card).rectangle([76, height - 150, 76 + 96, height - 142], fill=ORANGE + (255,))
    save(card.convert("RGB"), "images/social-card.png", optimize=True)


# --------------------------------------------------------------------------
# event thumbnails
# --------------------------------------------------------------------------

def wrapped(draw, text, fnt, max_width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line]


# Each event's listing card: (folder, kind, month and year, edition, venue).
WS = "Dutch Development Economics Network Workshop"
PHD = "Dutch Development Economics Network PhD Workshop"
EVENTS = [
    ("2010_workshop_tilburg",        "Workshop",     "April 2010",    f"1st {WS}",  "Tilburg University"),
    ("2013_workshop_tilburg",        "Workshop",     "June 2013",     f"4th {WS}",  "Tilburg University"),
    ("2015_workshop_wageningen",     "Workshop",     "March 2015",    f"6th {WS}",  "Wageningen University"),
    ("2016_workshop_tilburg",        "Workshop",     "March 2016",    f"7th {WS}",  "Tilburg University"),
    ("2017_workshop_wageningen",     "Workshop",     "May 2017",      f"8th {WS}",  "Wageningen University"),
    ("2018_workshop_wageningen",     "Workshop",     "April 2018",    f"9th {WS}",  "Wageningen University"),
    ("2019_workshop_tinbergen",      "Workshop",     "June 2019",     f"10th {WS}", "Tinbergen Institute"),
    ("2022_workshop_maastricht",     "Workshop",     "April 2022",    f"11th {WS}", "UNU-MERIT, Maastricht"),
    ("2023_workshop_groningen",      "Workshop",     "April 2023",    f"12th {WS}", "University of Groningen"),
    ("2024_workshop_utrecht",        "Workshop",     "April 2024",    f"13th {WS}", "Utrecht University"),
    ("2025_workshop_tinbergen",      "Workshop",     "March 2025",    f"14th {WS}", "Tinbergen Institute"),
    ("2026_workshop_nijmegen",       "Workshop",     "March 2026",    f"15th {WS}", "Radboud University"),
    ("2027_workshop_wageningen",     "Workshop",     "April 2027",    f"16th {WS}", "Wageningen University"),
    ("2023_phd_workshop_utrecht",    "PhD Workshop", "November 2023", f"1st {PHD}", "Utrecht University"),
    ("2024_phd_workshop_wageningen", "PhD Workshop", "October 2024",  f"2nd {PHD}", "Wageningen University"),
    ("2025_phd_workshop_tinbergen",  "PhD Workshop", "October 2025",  f"3rd {PHD}", "Tinbergen Institute"),
    ("2026_phd_workshop_tinbergen",  "PhD Workshop", "November 2026", f"4th {PHD}", "Tinbergen Institute"),
]

# Colour variants for the cards, all drawn from the brand palette and all at
# 4.5:1 or better for every line of text. "mark" says which version of the
# logo symbol sits on the card: full colour on light grounds, white on dark
# ones, and solid navy on orange, where the orange node would disappear.
VARIANTS = [
    dict(bg=NAVY,            title=(255, 255, 255), kicker=ORANGE,          venue=(185, 198, 222), mark="white", bar=ORANGE),
    dict(bg=SAND,            title=NAVY,            kicker=ORANGE_INK,      venue=MUTED,           mark="color", bar=ORANGE),
    dict(bg=(43, 85, 151),   title=(255, 255, 255), kicker=(255, 210, 161), venue=(220, 228, 242), mark="white", bar=ORANGE),
    dict(bg=BLUE_50,         title=NAVY,            kicker=(154, 74, 6),    venue=MUTED,           mark="color", bar=ORANGE),
    dict(bg=ORANGE,          title=NAVY,            kicker=(8, 26, 61),     venue=(8, 26, 61),     mark="navy",  bar=NAVY),
]


def tinted(img, color):
    """The artwork in one solid colour, keeping its shape and anti-aliasing."""
    solid = Image.new("RGBA", img.size, color + (255,))
    solid.putalpha(img.getchannel("A"))
    return solid


def build_event_thumbnail(kind, when, title, venue, out_path, symbol, variant, size=1200):
    """Square card used as the event's thumbnail in listings and link previews."""
    card = Image.new("RGB", (size, size), variant["bg"])
    draw = ImageDraw.Draw(card)

    margin = round(size * 0.085)
    leading = round(size * 0.098)
    kicker_font = font(round(size * 0.036))
    title_font, venue_font = font(round(size * 0.077)), font(round(size * 0.045), FONT_REGULAR)
    lines = wrapped(draw, title, title_font, size - 2 * margin)

    kicker_gap = round(size * 0.075)
    block = kicker_gap + len(lines) * leading + round(size * 0.09)
    y = (size - block) // 2 - round(size * 0.03)
    draw.text((margin, y), f"{kind.upper()}  ·  {when.upper()}", font=kicker_font, fill=variant["kicker"])
    y += kicker_gap
    for line in lines:
        draw.text((margin, y), line, font=title_font, fill=variant["title"])
        y += leading

    draw.text((margin, y + round(size * 0.03)), venue, font=venue_font, fill=variant["venue"])

    art = {"color": symbol, "white": knockout(symbol), "navy": tinted(symbol, NAVY)}[variant["mark"]]
    mark = resized(art, height=round(size * 0.1))
    card.paste(mark, (margin, size - round(size * 0.055) - mark.height - round(size * 0.05)), mark)
    draw.rectangle([0, size - round(size * 0.055), size, size - round(size * 0.043)], fill=variant["bar"])

    save(card, out_path, optimize=True, quality=90)


def build_event_thumbnails(symbol):
    """Cycle the colour variants in the order the events listing shows the
    cards (newest first), so neighbouring cards never share a colour."""
    print("event thumbnails")
    newest_first = sorted(EVENTS, key=lambda e: datetime.strptime(e[2], "%B %Y"), reverse=True)
    for i, (folder, kind, when, title, venue) in enumerate(newest_first):
        variant = VARIANTS[i % len(VARIANTS)]
        build_event_thumbnail(kind, when, title, venue, f"events/{folder}/thumbnail.jpg", symbol, variant)



# --------------------------------------------------------------------------
# homepage: photo strip, member portraits, network map
# --------------------------------------------------------------------------

STRIP_PHOTOS = ["img1.jpg", "img2.jpg", "img3.jpeg", "img4.jpg", "img5.jpg"]


def build_homepage_images():
    """Web-sized copies for the homepage strips. The originals run to 4080px
    and 2.3 MB; the strip shows them about 240px tall."""
    print("homepage photos")
    for name in STRIP_PHOTOS:
        photo = Image.open(ROOT / "images/homepage" / name).convert("RGB")
        if photo.height > 560:
            photo = resized(photo, height=560)
        save(photo, f"images/homepage/strip/{Path(name).stem}.jpg", quality=80, optimize=True, progressive=True)

    print("member portraits")
    people = ROOT / "images/people"
    people.mkdir(parents=True, exist_ok=True)
    for src in sorted((ROOT / "members/members/photos").glob("*.jpg")):
        face = Image.open(src).convert("RGB")
        side = min(face.size)
        # square crop, biased upwards so faces stay in frame on portrait photos
        top = max(0, int((face.height - side) * 0.3))
        left = (face.width - side) // 2
        face = face.crop((left, top, left + side, top + side)).resize((200, 200), Image.LANCZOS)
        face.save(people / src.name, quality=82, optimize=True)
    print(f"  images/people/  {len(list(people.glob('*.jpg')))} portraits, 200x200")


# The network's universities: node id, city label, campus coordinates, and
# where the label sits relative to the dot.
NETWORK_NODES = [
    ("groningen",  "Groningen",  53.2192, 6.5629, "left"),
    ("amsterdam",  "Amsterdam",  52.3336, 4.8654, "left"),
    ("utrecht",    "Utrecht",    52.0851, 5.1804, "below"),
    ("rotterdam",  "Rotterdam",  51.9175, 4.5250, "left"),
    ("wageningen", "Wageningen", 51.9853, 5.6656, "right"),
    ("nijmegen",   "Nijmegen",   51.8190, 5.8560, "below"),
    ("tilburg",    "Tilburg",    51.5632, 5.0435, "left"),
    ("maastricht", "Maastricht", 50.8540, 5.6910, "left"),
]
# event folder suffix -> node (the Tinbergen Institute is in Amsterdam)
HOST_NODE = {"tinbergen": "amsterdam"}


def build_network_map():
    """Inline-ready SVG for the homepage: the eight universities as nodes, and
    lines tracing the annual workshop from host to host, read from the event
    folders (so a new workshop page extends the line on the next run)."""
    import json, math
    print("network map")
    geo = json.loads((ROOT / "Python/nl_maps_unis/nl_provinces_2025.geojson").read_text())

    def merc(lon, lat):
        return math.radians(lon), math.asinh(math.tan(math.radians(lat)))

    rings = []
    for f in geo["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            for ring in poly:
                rings.append([merc(lon, lat) for lon, lat in ring])
    xs = [x for r in rings for x, _ in r]; ys = [y for r in rings for _, y in r]
    W, PAD = 520.0, 16.0
    scale = (W - 2 * PAD) / (max(xs) - min(xs))
    H = (max(ys) - min(ys)) * scale + 2 * PAD

    def xy(x, y):
        return PAD + (x - min(xs)) * scale, PAD + (max(ys) - y) * scale

    country = []
    for r in rings:
        pts = [xy(x, y) for x, y in r]
        thin = [pts[0]] + [p for a, p in zip(pts, pts[1:]) if abs(p[0] - a[0]) + abs(p[1] - a[1]) >= 0.6]
        country.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in thin) + "Z")

    pos = {nid: xy(*merc(lon, lat)) for nid, _, lat, lon, _ in NETWORK_NODES}

    # workshop hosts in date order -> consecutive, distinct hops. Only editions
    # that have taken place: an announced workshop joins the route once it's held.
    def held(folder):
        for line in (ROOT / "events" / folder / "index.qmd").read_text().splitlines():
            if line.startswith("date:"):
                return datetime.strptime(line.split(":", 1)[1].strip(), "%Y-%m-%d") <= datetime.now()
        return True

    hosts = []
    for folder in sorted(p.name for p in (ROOT / "events").glob("20*_workshop_*") if "_phd_" not in p.name and held(p.name)):
        node = HOST_NODE.get(folder.rsplit("_", 1)[-1], folder.rsplit("_", 1)[-1])
        if not hosts or hosts[-1] != node:
            hosts.append(node)
    hops, seen = [], set()
    for a, b in zip(hosts, hosts[1:]):
        if frozenset((a, b)) not in seen:
            seen.add(frozenset((a, b)))
            hops.append((a, b))
    latest = hosts[-1]

    def arc(a, b, i):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        # a gentle curve like the lines in the logo, bending alternately left
        # and right so hops that leave the same city fan out instead of overlapping
        bend = 0.18 if i % 2 == 0 else -0.18
        return f"M{x1:.1f} {y1:.1f}Q{mx - dy * bend:.1f} {my + dx * bend:.1f} {x2:.1f} {y2:.1f}"

    label_at = {"left": (-13, 5, "end"), "right": (13, 5, "start"), "above": (0, -15, "middle"), "below": (0, 25, "middle")}
    edges = "".join(f'<path class="nm-edge" pathLength="1" style="--i:{i}" d="{arc(a, b, i)}"/>' for i, (a, b) in enumerate(hops))
    nodes = ""
    for nid, label, _, _, where in NETWORK_NODES:
        x, y = pos[nid]
        dx, dy, anchor = label_at[where]
        latest_cls = " is-latest" if nid == latest else ""
        nodes += (f'<g class="nm-node{latest_cls}" data-node="{nid}" transform="translate({x:.1f} {y:.1f})" tabindex="0" role="button" aria-label="{label}">'
                  f'<circle class="nm-halo" r="15"/><circle class="nm-dot" r="7"/>'
                  f'<text class="nm-label" x="{dx}" y="{dy}" text-anchor="{anchor}">{label}</text></g>')

    svg = (f'<svg class="network-map" viewBox="0 0 {W:.0f} {H:.0f}" role="group" aria-label="Map of the network\'s universities">'
           f'<path class="nm-country" d="{"".join(country)}"/>'
           f'<g class="nm-edges">{edges}</g><g class="nm-nodes">{nodes}</g></svg>\n')
    out = ROOT / "images/network-map.svg"
    out.write_text(svg)
    print(f"  images/network-map.svg  {len(hops)} hops: {' > '.join(hosts)}  (latest: {latest})")



# --------------------------------------------------------------------------
# the "event is in the future" card, and its layers for the animation
# --------------------------------------------------------------------------

def build_future_event():
    """The card shown on the page of an event that hasn't happened yet.

    Also saved as separate transparent layers (background, 404, rule,
    headline, subline, logo) that stack into exactly the same image: the
    page reveals them one by one while the R code beside them is highlighted.
    """
    print("future-event card")
    W, H = 1200, 760
    big, head, sub = font(260, 0), font(58, FONT_DEMI), font(36, FONT_REGULAR)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def text_layer(y, text, fnt, fill):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        x = (W - probe.textlength(text, font=fnt)) / 2
        ImageDraw.Draw(layer).text((x, y), text, font=fnt, fill=fill)
        return layer

    rule = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(rule).rectangle([W / 2 - 48, 420, W / 2 + 48, 428], fill=ORANGE)
    logo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mark = Image.open(ROOT / "images/logos/logo-mark.png").convert("RGBA")
    mark = resized(mark, height=70)
    logo.paste(mark, ((W - mark.width) // 2, 640), mark)

    layers = {
        "bg": Image.new("RGBA", (W, H), BLUE_50 + (255,)),
        "404": text_layer(110, "404", big, NAVY),
        "rule": rule,
        "headline": text_layer(462, "This event is in the future", head, NAVY),
        "subline": text_layer(548, "Check back after it has taken place.", sub, MUTED),
        "logo": logo,
    }
    card = Image.new("RGBA", (W, H))
    for name, layer in layers.items():
        save(layer, f"events/future-event/{name}.png", optimize=True)
        card = Image.alpha_composite(card, layer)
    save(card.convert("RGB"), "events/future-event.png", optimize=True)

if __name__ == "__main__":
    logo_full, symbol = build_logos()
    photo = build_hero()
    build_social_card(photo, logo_full)
    build_event_thumbnails(symbol)
    build_homepage_images()
    build_network_map()
    build_future_event()
