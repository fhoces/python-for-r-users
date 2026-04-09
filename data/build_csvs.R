# =============================================================================
# Build the synthetic CSV files used by the Python exercises
# Run with: Rscript data/build_csvs.R
# =============================================================================

library(tidyverse)
set.seed(2026)

dir.create("data", showWarnings = FALSE)

n_drivers <- 800
drivers <- tibble(
  driver_id    = 1:n_drivers,
  signup_date  = sample(seq(as.Date("2022-01-01"), as.Date("2025-12-01"), by = "day"),
                        n_drivers, replace = TRUE),
  gender       = sample(c("M", "F"), n_drivers, replace = TRUE, prob = c(0.78, 0.22)),
  city         = sample(c("San Francisco", "Chicago", "Boston", "Seattle", "Austin"),
                        n_drivers, replace = TRUE)
)
write_csv(drivers, "data/drivers.csv")

n_riders <- 4000
riders <- tibble(
  rider_id     = 1:n_riders,
  signup_date  = sample(seq(as.Date("2022-01-01"), as.Date("2025-12-01"), by = "day"),
                        n_riders, replace = TRUE),
  city         = sample(c("San Francisco", "Chicago", "Boston", "Seattle", "Austin"),
                        n_riders, replace = TRUE),
  is_minority  = rbinom(n_riders, 1, 0.4)
)
write_csv(riders, "data/riders.csv")

n_rides <- 30000
rides <- tibble(
  ride_id      = 1:n_rides,
  rider_id     = sample(1:n_riders, n_rides, replace = TRUE),
  driver_id    = sample(1:n_drivers, n_rides, replace = TRUE),
  city         = sample(c("San Francisco", "Chicago", "Boston", "Seattle", "Austin"),
                        n_rides, replace = TRUE),
  pickup_at    = sample(seq(as.POSIXct("2025-01-01"), as.POSIXct("2025-12-31 23:59:00"), by = "5 min"),
                        n_rides, replace = TRUE),
  distance_mi  = pmax(round(rlnorm(n_rides, 1.5, 0.5), 2), 0.3),
  surge_mult   = pmax(1, round(rnorm(n_rides, 1.2, 0.3), 2)),
  rider_rating = sample(c(NA, 3, 4, 5), n_rides, replace = TRUE,
                         prob = c(0.05, 0.10, 0.25, 0.60))
)
rides <- rides |>
  mutate(
    duration_min = round(distance_mi * 3 + rnorm(n_rides, 0, 1.5), 1),
    fare_usd     = round(2.50 + 1.50 * distance_mi * surge_mult + rnorm(n_rides, 0, 1), 2),
    pickup_at    = as.character(pickup_at)
  )
write_csv(rides, "data/rides.csv")

# A/B test outcomes table for module 5
set.seed(99)
n_ab <- 5000
ab <- tibble(
  user_id   = 1:n_ab,
  treatment = rbinom(n_ab, 1, 0.5),
  city      = sample(c("San Francisco", "Chicago", "Boston", "Seattle", "Austin"),
                     n_ab, replace = TRUE),
  spend_usd = pmax(0, round(
    20 + 1.8 * rbinom(n_ab, 1, 0.5) + rnorm(n_ab, 0, 5), 2)
  )
)
ab$spend_usd <- ab$spend_usd + 1.8 * ab$treatment
write_csv(ab, "data/ab_test.csv")

cat("\nBuilt CSVs in data/:\n")
print(list.files("data", full.names = TRUE))
