# -------------------------------------------------------------------------------------- #
# Title: Make and save an event-specific thumbnail
# Author: Michelle González Amador (replication of work by Dax Kellie, Olivia Torresan)
# Date: May 6, 2025
# Version: R 4.4.1, Positron: 2025.04.0 (Universal) build 250, OS: Darwin arm64 24.4.0
# -------------------------------------------------------------------------------------- #


#------------ Edit these parameters for specific event ---------------------#

event <- "14th Dutch Development Economics Network (DuDE) Workshop Program"
location <- "Tinbergen Institute"
main_colour <- "#FFEDCF" 
text_colour <- "#C44D34" 
line_colour <- "#EB9D07"

#------------ Make and save thumbnail ---------------------------------------#

# load libraries
library(ggtext)
library(extrafont)
library(ggplot2)
library(here)
library(scales)
library(glue)
library(showtext)

source(here("R", "functions_thumbnail.R"))

# load font
font_add_google("Poppins", bold.wt = 500)
showtext_auto(enable = TRUE)


#-------------------------------------------------------------------------------#
# When happy with thumbnail, copy/paste thumbnail.png into specific event folder
#-------------------------------------------------------------------------------#

make_paper_thumbnail(event, location, main_colour, text_colour, line_colour)

# file goes to events/images