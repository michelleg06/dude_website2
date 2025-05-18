
import svgwrite
from bs4 import BeautifulSoup
import lxml

# Define map fill color
theme_fill = "#cfcdcc"

# Load base SVG of the Netherlands
with open("nl.svg", "r") as file:
    soup = BeautifulSoup(file.read(), "lxml-xml")

# Define SVG viewBox and geographic bounds
viewbox = [150.26527331189712, 0, 337.5361736334405, 400]
lat_range = (50.75, 53.5)
lon_range = (3.4, 7.2)

def latlon_to_svg_coords(lat, lon, viewbox, lat_range, lon_range):
    x_min, y_min, width, height = viewbox
    lon_min, lon_max = lon_range
    lat_min, lat_max = lat_range

    x = x_min + (lon - lon_min) / (lon_max - lon_min) * width
    y = y_min + (lat_max - lat) / (lat_max - lat_min) * height  # invert Y
    return x, y

# Maastricht coordinates
lat, lon = 50.8514, 5.6900
x, y = latlon_to_svg_coords(lat, lon, viewbox, lat_range, lon_range)

# 🎨 Recolor all map paths to the theme fill
for path in soup.find_all("path"):
    path["fill"] = theme_fill

# Load and position the red pin SVG
with open("redpin.svg", "r") as file:
    pin_svg = BeautifulSoup(file.read(), "xml")

pin_svg.svg['x'] = str(x - 10)       # X offset for centering
pin_svg.svg['y'] = str(y - 60)       # Y offset for visual alignment
pin_svg.svg['width'] = "42"
pin_svg.svg['height'] = "42"

# Append pin to base map
soup.svg.append(pin_svg.svg)

# Save the updated SVG
with open("merit.svg", "w") as f:
    f.write(str(soup))
