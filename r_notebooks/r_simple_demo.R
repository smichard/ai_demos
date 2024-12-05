# Install necessary libraries
if (!require(quantmod)) install.packages("quantmod", repos = "http://cran.us.r-project.org")
if (!require(ggplot2)) install.packages("ggplot2", repos = "http://cran.us.r-project.org")

# Load libraries
library(quantmod)
library(ggplot2)

# Define the ticker symbol
ticker_symbol <- "^DJI"

# Fetch the data for the last 5 years
start_date <- Sys.Date() - 5 * 365
end_date <- Sys.Date()
data <- getSymbols(ticker_symbol, src = "yahoo", from = start_date, to = end_date, auto.assign = FALSE)

# Convert to a data frame for easier handling
data_df <- data.frame(Date = index(data), coredata(data))
colnames(data_df) <- c("Date", "Open", "High", "Low", "Close", "Volume", "Adjusted")

# Print the fetched data
print(head(data_df))

# Plot the data
ggplot(data = data_df, aes(x = Date, y = Adjusted)) +
  geom_line(color = "blue") +
  labs(title = paste(ticker_symbol, "(Last 5 Years)"),
       x = "Date",
       y = "Close Price") +
  theme_minimal()

# Find all-time high and all-time low
all_time_high <- max(data_df$Adjusted, na.rm = TRUE)
all_time_low <- min(data_df$Adjusted, na.rm = TRUE)
all_time_high_date <- data_df$Date[which.max(data_df$Adjusted)]
all_time_low_date <- data_df$Date[which.min(data_df$Adjusted)]

# Print all-time high and low with dates
cat(sprintf("All-Time High: %.2f on %s\n", all_time_high, all_time_high_date))
cat(sprintf("All-Time Low: %.2f on %s\n", all_time_low, all_time_low_date))

# Create data frames for all-time high and low points
all_time_high_df <- data.frame(Date = all_time_high_date, Adjusted = all_time_high)
all_time_low_df <- data.frame(Date = all_time_low_date, Adjusted = all_time_low)

# Plot the data with all-time high and low
ggplot(data = data_df, aes(x = Date, y = Adjusted)) +
  geom_line(color = "blue") +
  geom_point(data = all_time_high_df, aes(x = Date, y = Adjusted), color = "green", size = 3) +
  geom_point(data = all_time_low_df, aes(x = Date, y = Adjusted), color = "red", size = 3) +
  annotate("text", x = all_time_high_date, y = all_time_high, label = "  High", hjust = -0.1, color = "green") +
  annotate("text", x = all_time_low_date, y = all_time_low, label = "  Low", hjust = -0.1, color = "red") +
  labs(title = paste(ticker_symbol, "(Last 5 Years)"),
       x = "Date",
       y = "Close Price") +
  theme_minimal()
