
import svgwrite
from bs4 import BeautifulSoup
import lxml

# Define fill color for the map
theme_fill = "#cfcdcc"

# Load original SVG
with open("nl.svg", "r") as file:
    soup = BeautifulSoup(file.read(), "lxml-xml")

# SVG bounds and geographic range
viewbox = [150.26527331189712, 1.120499932, 337.5361736334405, 380.96997688]
lat_range = (50.75, 53.5)
lon_range = (3.4, 7.2)

# Convert lat/lon to SVG coordinates
def latlon_to_svg_coords(lat, lon, viewbox, lat_range, lon_range):
    x_min, y_min, width, height = viewbox
    lon_min, lon_max = lon_range
    lat_min, lat_max = lat_range

    x = x_min + (lon - lon_min) / (lon_max - lon_min) * width
    y = y_min + (lat_max - lat) / (lat_max - lat_min) * height  # invert Y
    return x, y

# Target coordinates for Tilburg
lat, lon = 51.5555, 5.0916
x, y = latlon_to_svg_coords(lat, lon, viewbox, lat_range, lon_range)

# 🟠 Recolor all paths in the base SVG
for path in soup.find_all("path"):
    path["fill"] = theme_fill

# Load pin icon SVG
with open("redpin.svg", "r") as file:
    pin_svg = BeautifulSoup(file.read(), "xml")

# Position and resize pin
pin_svg.svg['x'] = str(x - 8)
pin_svg.svg['y'] = str(y - 16)
pin_svg.svg['width'] = "42"
pin_svg.svg['height'] = "42"

# Append pin to map
soup.svg.append(pin_svg.svg)

# Save updated SVG
with open("tilburg.svg", "w") as f:
    f.write(str(soup))
