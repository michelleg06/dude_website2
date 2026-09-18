# -------------------------------------------------------------------------- #
# Homepage building blocks. Everything here is read from the site's own pages
# at render time, so the homepage follows changes to universities, members and
# events without being edited itself.
# -------------------------------------------------------------------------- #

library(htmltools)

# Map file on the universities page -> node id on the network map
# (see NETWORK_NODES in Python/make_assets.py)
MAP_NODE <- c(
  "tilburg.svg" = "tilburg", "map_wageningen.svg" = "wageningen",
  "merit.svg" = "maastricht", "map_groningen.svg" = "groningen",
  "map_nijmegen.svg" = "nijmegen", "map_utrecht.svg" = "utrecht",
  "map_amsterdam.svg" = "amsterdam", "map_rotterdam.svg" = "rotterdam"
)

# Papers presented at the annual workshops with a published programme
# (2010-2026). Update by hand when a new programme is added.
PAPERS_PRESENTED <- 110

first_match <- function(text, pattern) {
  hit <- regmatches(text, regexpr(pattern, text, perl = TRUE))
  if (length(hit)) hit else NA_character_
}

# --- universities and coordinators ----------------------------------------

universities <- function(path = "members/universities/index.qmd") {
  txt <- paste(readLines(path, warn = FALSE), collapse = "\n")
  cards <- strsplit(txt, "::: {.card-uni}", fixed = TRUE)[[1]][-1]
  rows <- lapply(cards, function(card) {
    map_file <- basename(first_match(card, "images/[a-z_]+\\.svg"))
    photo <- sub('.*src="([^"]+)".*', "\\1",
                 first_match(card, '<img src="[^"]+" alt="[^"]*coordinator" class="profile-img"'))
    person <- first_match(card, "<strong>[^<]+</strong>, [^<]+</p>")
    list(
      node = unname(MAP_NODE[map_file]),
      university = gsub("\\*", "", first_match(card, "\\*\\*[^*]+\\*\\*")),
      # photo paths on that page are relative to members/universities/
      photo = sub("^members/universities/\\.\\./", "members/",
                  file.path("members/universities", photo)),
      coordinator = sub("<strong>([^<]+)</strong>.*", "\\1", person),
      role = sub("\\.?</p>$", "", sub(".*</strong>, ", "", person))
    )
  })
  Filter(function(u) !is.na(u$node), rows)
}

# --- events ---------------------------------------------------------------

events <- function() {
  folders <- basename(list.dirs("events", recursive = FALSE))
  folders <- sort(folders[grepl("^20", folders)])
  front <- function(f, key) {
    line <- grep(paste0("^", key, ":"), readLines(file.path("events", f, "index.qmd"), warn = FALSE), value = TRUE)[1]
    gsub('^"|"$', "", trimws(sub(paste0("^", key, ":"), "", line)))
  }
  titles <- vapply(folders, front, character(1), key = "title")
  dates <- as.Date(vapply(folders, front, character(1), key = "date"))
  node <- sub(".*_", "", folders)
  node[node == "tinbergen"] <- "amsterdam"  # the Tinbergen Institute is in Amsterdam
  data.frame(
    folder = folders, title = unname(titles), node = node,
    phd = grepl("_phd_", folders),
    year = as.integer(substr(folders, 1, 4)),
    edition = as.integer(sub(".*?(\\d+)(st|nd|rd|th) .*", "\\1", titles)),
    date = unname(dates),
    stringsAsFactors = FALSE
  )
}

# events that have taken place: announced future editions don't count yet
past_events <- function(ev = events()) ev[ev$date <= Sys.Date(), ]

network_stats <- function(ev = past_events(), unis = universities()) {
  ws <- ev[!ev$phd, ]
  list(
    workshops = max(ws$edition),
    phd = max(ev$edition[ev$phd]),
    papers = PAPERS_PRESENTED,
    universities = length(unis),
    first_year = min(ws$year), latest_year = max(ws$year),
    first_node = ws$node[which.min(ws$year)], latest_node = ws$node[which.max(ws$year)]
  )
}

# JSON for the map's coordinator card, one entry per node
network_data <- function(ev = past_events(), unis = universities()) {
  latest <- network_stats(ev, unis)$latest_node
  data <- lapply(unis, function(u) {
    n_ws <- sum(!ev$phd & ev$node == u$node)
    n_phd <- sum(ev$phd & ev$node == u$node)
    hosted <- c(
      if (n_ws) sprintf("%d workshop%s", n_ws, if (n_ws > 1) "s" else ""),
      if (n_phd) sprintf("%d PhD workshop%s", n_phd, if (n_phd > 1) "s" else "")
    )
    c(u, list(
      hosted = if (!length(hosted)) "Newest member of the network" else
        paste0("Hosted ", paste(hosted, collapse = " and "),
               # the Amsterdam editions were held at the Tinbergen Institute
               if (u$node == "amsterdam") " at the Tinbergen Institute" else ""),
      latest = identical(u$node, latest)
    ))
  })
  names(data) <- vapply(unis, `[[`, "", "node")
  tags$script(type = "application/json", id = "network-data",
              HTML(jsonlite::toJSON(data, auto_unbox = TRUE)))
}

city_of <- function(node) {
  c(tilburg = "Tilburg", wageningen = "Wageningen", maastricht = "Maastricht",
    groningen = "Groningen", nijmegen = "Nijmegen", utrecht = "Utrecht",
    amsterdam = "Amsterdam", rotterdam = "Rotterdam")[[node]]
}

# --- people and moments ---------------------------------------------------

# A marquee row: the items twice, the second copy hidden from assistive tech,
# so the loop is seamless and screen readers hear each item once.
marquee <- function(items, class, direction = "left") {
  div(class = paste("marquee", class), `data-direction` = direction,
      div(class = "marquee-track",
          tags$ul(class = "marquee-group", items),
          tags$ul(class = "marquee-group", `aria-hidden` = "true", items)))
}

photo_strip <- function() {
  photos <- list(
    c("img1", "Participants at a past network workshop"),
    c("img2", "Presentation session at a network event"),
    c("img3", "Members of the network during a workshop"),
    c("img4", "Discussion between researchers at a network event"),
    c("img5", "Group photo from a network workshop")
  )
  items <- lapply(rep(photos, 2), function(p) {
    tags$li(tags$img(src = sprintf("images/homepage/strip/%s.jpg", p[[1]]),
                     alt = p[[2]], loading = "lazy"))
  })
  marquee(items, "marquee-photos", "left")
}

# A random handful of members, drawn again on every render
people_strip <- function(n = 14, path = "members/members/index.qmd") {
  txt <- paste(readLines(path, warn = FALSE), collapse = "\n")
  cards <- regmatches(txt, gregexpr('<img class="member-photo" src="photos/[^"]+" alt="[^"]+"', txt))[[1]]
  photo <- sub('.*src="photos/([^"]+)".*', "\\1", cards)
  name <- sub('.*alt="([^"]+)".*', "\\1", cards)
  keep <- !duplicated(photo) & file.exists(file.path("images/people", photo))
  pick <- sample(which(keep), min(n, sum(keep)))
  items <- lapply(pick, function(i) {
    tags$li(tags$img(src = file.path("images/people", photo[i]), alt = "", loading = "lazy"),
            tags$span(name[i]))
  })
  marquee(items, "marquee-people", "right")
}
