options(stringsAsFactors=FALSE)
suppressPackageStartupMessages(library("argparse"))
library(rjson)
library(rlog)
# create parser object
parser <- ArgumentParser()
parser$add_argument("-p", "--process-steps","--process_steps", default=NULL, required=TRUE,
                    help="Main NF script")
parser$add_argument("-n", "--num-processes","--num_processes", default='10', required=FALSE,
                    help="Main NF script")
########################################
args <- parser$parse_args()
num_processes = strtoi(args$num_processes)
step_data = args$process_steps
step_data_loaded = rjson::fromJSON(file = step_data)
############
replaceBadTimestamp <- function(ts_of_interest){
  if(is.null(ts_of_interest)){
    new_ts = "9999-12-03T00:00:00Z"
    return(new_ts)
  } else if(ts_of_interest == "0001-01-03T00:00:00Z"){
    new_ts = gsub("0001","9999",ts_of_interest)
    return(new_ts)
  } else{
    return(ts_of_interest)
  }
  
}
#################
process_starts = c()
for(i in 1:length(step_data_loaded)){
  process_name = step_data_loaded[[i]]$id
  ##"0001-01-03T00:00:00Z"
  queue_date = NULL
  if("queueDate" %in% names(step_data_loaded[[i]])){
    queue_date = step_data_loaded[[i]]$queueDate
  }
  queue_date = replaceBadTimestamp(queue_date)
  
  start_date = NULL
  if("startDate" %in% names(step_data_loaded[[i]])){
    start_date = step_data_loaded[[i]]$startDate
  }
  start_date = replaceBadTimestamp(start_date)
  
  end_date = NULL
  if("endDate" %in% names(step_data_loaded[[i]])){
    end_date = step_data_loaded[[i]]$endDate
  }
  end_date = replaceBadTimestamp(end_date)
  
  process_starts = rbind(process_starts,c(process_name,queue_date,start_date,end_date))
}
process_starts = as.data.frame(process_starts)
colnames(process_starts) = c('processName','queueDate','startDate','endDate')

rlog::log_info(paste("most recently queued processes"))
head(process_starts[order(process_starts$queueDate,decreasing = T),],num_processes)

rlog::log_info(paste("most recently started processes"))
head(process_starts[order(process_starts$startDate,decreasing = T),],num_processes)

rlog::log_info(paste("most recently finished processes"))
head(process_starts[order(process_starts$endDate,decreasing = T),],num_processes)

## write table
output_table = gsub(".txt$",".table.txt",step_data)
rlog::log_info(paste("Writing process table out to:",output_table))
write.table(process_starts,file = output_table,row.names = F,quote=F,sep=",")