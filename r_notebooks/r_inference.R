# Install necessary libraries
if (!require(httr)) install.packages("httr", repos = "http://cran.us.r-project.org")
if (!require(jsonlite)) install.packages("jsonlite", repos = "http://cran.us.r-project.org")

# Required libraries
# If needed, install them first via install.packages("httr") and install.packages("jsonlite")
library(httr)
library(jsonlite)

ENDPOINT <- "<inference_endpoint>/v1/chat/completions"
API_TOKEN <- "<API_TOKEN>"

inference <- function(endpoint, token = NULL) {
  # Hard-code the model name and messages here:
  model <- "custom-model"
  messages <- list(
    list(role = "user", content = "What is the capital of France?")
  )
  
  # Create request body
  payload <- list(
    model    = model,
    messages = messages
  )
  
  # Conditionally build headers with or without token
  if (!is.null(token) && token != "") {
    headers <- add_headers(
      "Content-Type" = "application/json",
      "Authorization" = paste("Bearer", token)
    )
  } else {
    headers <- add_headers("Content-Type" = "application/json")
  }
  
  # Make the POST request
  response <- POST(
    url     = endpoint,
    headers,
    body    = toJSON(payload, auto_unbox = TRUE),
    encode  = "json"
    # If you have self-signed cert issues, you can uncomment:
    # , config(ssl_verifypeer = 0)
  )
  
  # Check for HTTP errors
  if (http_error(response)) {
    stop(
      "Request failed. Status: ", status_code(response), "\n",
      "Body: ", content(response, as = "text", encoding = "UTF-8")
    )
  }
  
  # Print for debugging
  cat("Response status code:", status_code(response), "\n")
  raw_text <- content(response, as = "text", encoding = "UTF-8")
  cat("Raw response text:\n", raw_text, "\n\n")
  
  # Parse JSON, avoiding unwanted simplifications
  parsed <- tryCatch({
    fromJSON(raw_text, simplifyVector = FALSE)
  }, error = function(e) {
    stop("Failed to parse JSON response: ", e$message)
  })
  
  # Extract the model's answer if present
  if ("choices" %in% names(parsed) && length(parsed$choices) > 0) {
    answer <- parsed[["choices"]][[1]][["message"]][["content"]]
    cat("Model answer:\n", answer, "\n")
    return(answer)
  } else {
    cat("No 'choices' found in response.\n")
    return(NULL)
  }
}

inference(
  endpoint = ENDPOINT,
  token    = API_TOKEN
)

