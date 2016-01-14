#' Read an SBtab file in TSV (Tab-Separated Values format) into an data.frame
#' 
#' Returns a list containing the header and the data.frame.
#' 
#' This function only supports files with a single table.
#' 
#' @param fname A file name to read from.
#' @return  list containing the header and the data.frame.
#' 
#' @author Elad Noor, \email{noor@imsb.biol.ethz.ch}
#' @export
#' 
sbtab_read_tsv <- 
  function(fname) {
  mydata <- read.table(fname, sep="\t", stringsAsFactors = FALSE)
  header <- as.character(mydata$V1[1])
  header <- substr(header, 3, nchar(header))    # remove the !! from the header text
  columns <- as.character(mydata[2,]) 
  columns <- substr(columns, 2, nchar(columns)) # remove the ! from each column title
  data <- mydata[(3):dim(mydata)[1],]
  sbtab <- data.frame(data, row.names = NULL)
  names(sbtab) <- columns
  return(list(header=header, sbtab=sbtab))
}
