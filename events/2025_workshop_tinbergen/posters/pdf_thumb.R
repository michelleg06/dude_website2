library(pdftools)
library(magick)
library(here)

img <- image_read_pdf(here("events/2025_workshop_tinbergen/posters", "poster6_seimel.pdf"), density = 150)
image_write(image = img[1], path = here("events/2025_workshop_tinbergen/posters", "poster6-thumb.png"), format = "png")
