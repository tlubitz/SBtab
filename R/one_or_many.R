#' Read an SBtab file in TSV (Tab-Separated Values format) with multiple tables
#' 
#' Returns a list of all headers and tables
#' 
#' This function supports files with multiple tables separated by '%'
#' 
#' @param fname A file name to read from.
#' @return nested list containing a list of headers and a list of sbtabs.
#' @author Elad Noor, \email{noor@imsb.biol.ethz.ch}
#' @export
#' 
one_or_many <- 
  function(fname) {
  headers <- list()
  sbtabs <- list()
  mydata <- read.table(fname, sep="\t", stringsAsFactors = FALSE)
  num_lines <- dim(mydata)[1]
  if (num_lines > 0) { # if file not empty
    header_line <- NULL
    last_line <- 1
    for (r in 1:num_lines) {
      if (substr(mydata$V1[r], 1, 2) == '!!') {
        header_line <- r
      } else if (substr(mydata$V1[r], 1, 2) == '%' || r == num_lines) {
        header <- as.character(mydata$V1[header_line])
        header <- substr(header, 3, nchar(header))    # remove the !! from the header text
        columns <- as.character(mydata[header_line+1,]) 
        columns <- substr(columns, 2, nchar(columns)) # remove the ! from each column title
        if (r == num_lines) {
          data <- mydata[(header_line+2):r,]
        } else {
          data <- mydata[(header_line+2):(r-1),]
        }
        sbtab <- data.frame(data, row.names = NULL)
        names(sbtab) <- columns
        headers[[length(sbtabs)+1]] = header
        sbtabs[[length(sbtabs)+1]] = sbtab
      }
    }
  }
  return(list(headers=headers, sbtabs=sbtabs))
}
