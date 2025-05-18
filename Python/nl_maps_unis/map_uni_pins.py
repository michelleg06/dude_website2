
import svgwrite
from bs4 import BeautifulSoup
import lxml
import copy

# Load base SVG map of the Netherlands
with open("nl.svg", "r") as file:
    base_svg = BeautifulSoup(file.read(), "lxml-xml")

# Define viewBox and geographic bounds (as used in your base SVG)
viewbox = [150.26527331189712, 1.120499932, 337.5361736334405, 380.96997688]
lat_range = (50.75, 53.5)
lon_range = (3.4, 7.2)

def latlon_to_svg_coords(lat, lon, viewbox, lat_range, lon_range):
    x_min, y_min, width, height = viewbox
    lon_min, lon_max = lon_range
    lat_min, lat_max = lat_range

    x = x_min + (lon - lon_min) / (lon_max - lon_min) * width
    y = y_min + (lat_max - lat) / (lat_max - lat_min) * height
    return x, y

# List of cities and coordinates
cities = [
    {"name": "Tilburg", "lat": 51.5555, "lon": 5.0916},
    {"name": "Wageningen", "lat": 51.9692, "lon": 5.6650},
    {"name": "Maastricht", "lat": 50.8514, "lon": 5.6900},
    {"name": "Nijmegen", "lat": 51.8224, "lon": 5.8641},
    {"name": "Groningen", "lat": 53.2194, "lon": 6.5665},
    {"name": "Amsterdam", "lat": 52.3340, "lon": 4.8657},
    {"name": "Utrecht", "lat": 52.0907, "lon": 5.1214},
]

# Theme color for the base map fill
theme_fill = "#cfcdcc"

# Create one SVG per city
for city in cities:
    svg_copy = copy.deepcopy(base_svg)
    lat, lon = city["lat"], city["lon"]
    x, y = latlon_to_svg_coords(lat, lon, viewbox, lat_range, lon_range)

    # Recolor all <path> elements in the base map
    for path in svg_copy.find_all("path"):
        path["fill"] = theme_fill

    # Load and position the red pin
    with open("redpin.svg", "r") as file:
        pin_svg = BeautifulSoup(file.read(), "xml")

    max_y = viewbox[1] + viewbox[3] - 20
    adjusted_y = min(y, max_y - 16)

    pin_svg.svg['x'] = str(x - 8)
    pin_svg.svg['y'] = str(adjusted_y)
    pin_svg.svg['width'] = "42"
    pin_svg.svg['height'] = "42"

    # Append the pin to the map
    svg_copy.svg.append(pin_svg.svg)

    # Save the new file
    filename = f"map_{city['name'].lower()}.svg"
    with open(filename, "w") as f:
        f.write(str(svg_copy))
