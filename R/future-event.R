# -------------------------------------------------------------------------- #
# The page of an event that hasn't happened yet: a save-the-date panel built
# from the event's own front matter (title, date, event-dates, host), with a
# map on which every university in the network draws a line to the host city.
# Called from events/_future-event.qmd, so it runs inside events/<folder>/.
# -------------------------------------------------------------------------- #

library(htmltools)

# event folder suffix -> node on the network map (see HOST_NODE in Python/make_assets.py)
HOST_NODE <- c(tinbergen = "amsterdam")

future_event <- function(page = "index.qmd", map = "../../images/network-map.svg") {
  meta <- rmarkdown::yaml_front_matter(page)
  date <- as.Date(meta$date)
  when <- if (is.null(meta$`event-dates`)) format(date, "%e %B %Y") else meta$`event-dates`
  nodes <- map_nodes(map)
  node <- sub(".*_", "", basename(getwd()))
  if (node %in% names(HOST_NODE)) node <- HOST_NODE[[node]]
  host <- nodes[nodes$id == node, ]
  place <- meta$host
  if (nrow(host) && !grepl(host$city, place, fixed = TRUE)) place <- paste0(place, ", ", host$city)

  # "21–23 April 2027" -> "21–23" on the calendar tile
  day <- regmatches(when, regexpr("^[0-9]+(\\s*[–-]\\s*[0-9]+)?(?=\\s)", when, perl = TRUE))
  if (!length(day)) day <- format(date, "%d")

  icon <- function(name) tags$i(class = paste0("fa-solid fa-", name), `aria-hidden` = "true")

  div(class = "future-event", `data-date` = format(date),
    div(class = "fe-text",
      tags$p(class = "fe-kicker", "Save the date"),
      tags$h1(class = "fe-title", sub("^[0-9]{4}:\\s*", "", meta$title)),
      div(class = "fe-when",
        # the tile's pages flip from today's month to the event's (see the page script)
        div(class = "fe-cal", `aria-hidden` = "true",
          div(class = "fe-page",
            tags$span(class = "fe-cal-month", month.abb[as.integer(format(date, "%m"))]),
            tags$span(class = "fe-cal-day", gsub("\\s", "", day)),
            tags$span(class = "fe-cal-year", format(date, "%Y")))),
        div(class = "fe-facts",
          tags$p(class = "fe-fact", icon("calendar"), when),
          tags$p(class = "fe-fact", icon("location-dot"), place),
          # filled in by the page script, which knows the visitor's date
          tags$p(class = "fe-countdown", hidden = NA,
                 tags$span(class = "fe-count"), " ", tags$span(class = "fe-unit"))
        )
      ),
      div(class = "fe-details",
        tags$p(class = "fe-details-head", "More details to follow",
               tags$span(class = "fe-dots", `aria-hidden` = "true", tags$span(), tags$span(), tags$span())),
        tags$p("The programme, venue and practical details will be posted on this page once they are confirmed."),
        tags$p(tags$a(href = "#contact", "Questions in the meantime? Get in touch"))
      )
    ),
    if (nrow(host)) div(class = "fe-map", converging_map(map, nodes, node))
  )
}

# the universities on the homepage's network map: id, city, position, label placement
map_nodes <- function(map) {
  svg <- paste(readLines(map, warn = FALSE), collapse = "")
  pattern <- paste0('data-node="([a-z]+)" transform="translate\\(([0-9.]+) ([0-9.]+)\\)"[^>]*aria-label="([^"]+)">',
                    '.*?<text class="nm-label" x="([-0-9.]+)" y="([-0-9.]+)" text-anchor="([a-z]+)"')
  hits <- regmatches(svg, gregexpr(pattern, svg, perl = TRUE))[[1]]
  parts <- do.call(rbind, regmatches(hits, regexec(pattern, hits, perl = TRUE)))
  data.frame(id = parts[, 2], x = as.numeric(parts[, 3]), y = as.numeric(parts[, 4]), city = parts[, 5],
             lx = as.numeric(parts[, 6]), ly = as.numeric(parts[, 7]), anchor = parts[, 8])
}

# the country and its universities, with a line from each one to the host
converging_map <- function(map, nodes, node) {
  svg <- paste(readLines(map, warn = FALSE), collapse = "")
  box <- sub('.*viewBox="([^"]+)".*', "\\1", svg)
  country <- sub('.*<path class="nm-country" d="([^"]+)".*', "\\1", svg)
  host <- nodes[nodes$id == node, ]
  others <- nodes[nodes$id != node, ]
  # farthest first, so the lines arrive at the host one after another
  others <- others[order(-((others$x - host$x)^2 + (others$y - host$y)^2)), ]

  # a gentle curve like the lines in the logo, all bending the same way so
  # the lines swirl into the host instead of crossing
  arc <- function(x1, y1, x2, y2, bend = 0.16) {
    mx <- (x1 + x2) / 2; my <- (y1 + y2) / 2
    sprintf("M%.1f %.1fQ%.1f %.1f %.1f %.1f", x1, y1, mx - (y2 - y1) * bend, my + (x2 - x1) * bend, x2, y2)
  }
  label <- function(n, cls) {
    sprintf('<text class="%s" x="%.1f" y="%.1f" text-anchor="%s">%s</text>', cls, n$x + n$lx, n$y + n$ly, n$anchor, n$city)
  }

  i <- seq_len(nrow(others)) - 1
  routes <- sprintf('<path id="fe-route-%d" class="fe-route" pathLength="1" style="--i:%d" d="%s"/>',
                    i, i, arc(others$x, others$y, host$x, host$y))
  # a traveller runs along each line now and then, once the lines are drawn
  travellers <- sprintf(paste0(
    '<circle class="fe-traveller" r="3.5" opacity="0">',
    '<animateMotion dur="5s" begin="%.1fs" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.4;1" calcMode="linear">',
    '<mpath href="#fe-route-%d"/></animateMotion>',
    '<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.34;0.4;1" dur="5s" begin="%.1fs" repeatCount="indefinite"/>',
    '</circle>'), 3.4 + i * 0.7, i, 3.4 + i * 0.7)
  dots <- sprintf('<circle class="fe-node" style="--i:%d" cx="%.1f" cy="%.1f" r="6"/>', i, others$x, others$y)

  HTML(paste0(
    sprintf('<svg viewBox="%s" role="img" aria-label="Map of the Netherlands with a line from each of the network\'s universities to %s">', box, host$city),
    sprintf('<path class="fe-country" d="%s"/>', country),
    '<g class="fe-routes">', paste(routes, collapse = ""), '</g>',
    '<g class="fe-travellers">', paste(travellers, collapse = ""), '</g>',
    '<g class="fe-nodes">', paste(dots, collapse = ""), paste(label(others, "fe-label"), collapse = ""), '</g>',
    sprintf('<g class="fe-host"><circle class="fe-halo" cx="%.1f" cy="%.1f" r="16"/><circle class="fe-halo fe-halo-2" cx="%.1f" cy="%.1f" r="16"/>',
            host$x, host$y, host$x, host$y),
    sprintf('<circle class="fe-node" cx="%.1f" cy="%.1f" r="9"/>', host$x, host$y),
    label(host, "fe-label fe-host-label"), '</g></svg>'
  ))
}
