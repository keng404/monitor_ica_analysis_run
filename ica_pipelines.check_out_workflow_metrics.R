#!/usr/bin/env Rscript
library(DBI)
library(RSQLite)
library(rlog)
options(stringsAsFactors=FALSE)
suppressPackageStartupMessages(library("argparse"))
parser <- ArgumentParser()

# specify our desired options 
# by default ArgumentParser will add an help option 
parser$add_argument("-d", "--db-file","--db_file",required=TRUE,default = NULL,
                    help="SQLite DB file that contains kubernetes pod metrics")
args <- parser$parse_args()
db_file = args$db_file
if(is.null(db_file)){
  stop(paste("Please provide a DB file to this script"))
}
if(!file.exists(db_file)){
  stop(paste("Please provide a DB file to this script.\nYou provided",db_file,"\n"))
  
}
con <- dbConnect(SQLite(), db_file)

# Show List of Tables
as.data.frame(dbListTables(con))
#dbListTables(con)
#1 container_metrics
#2        containers
#3       disk_usages
#4      file_systems
#5              pods
### https://stackoverflow.com/questions/54531646/checking-kubernetes-pod-cpu-and-memory-utilization
memory_conversion_list = list()
memory_conversion_list[['Ki']] = 1e3
memory_conversion_list[['Mi']] = 1e6
memory_conversion_list[['Gi']] = 1e9
memory_numerical_conversion <- function(memory_metrics){
  memory_metrics_updated = memory_metrics
  for(j in 1:length(memory_metrics_updated)){
    for(i in 1:length(names(memory_conversion_list))){
      label_to_prune = names(memory_conversion_list)[i]
      modified_value = gsub(label_to_prune,"",memory_metrics[j])
      #rlog::log_info(paste("MODIFIED_VALUE:",modified_value))
      if(modified_value != memory_metrics[j]){
        # return memory metrics in Gbytes
        memory_metrics_updated[j] = (as.numeric(modified_value) * memory_conversion_list[[label_to_prune]])/1e9
      } else{
        memory_metrics_updated[j] = (as.numeric(modified_value)/1e9)
      }
    }
  }
  return(memory_metrics_updated)
}
###### https://stackoverflow.com/questions/54531646/checking-kubernetes-pod-cpu-and-memory-utilization
cpu_conversion_list = list()
cpu_conversion_list[['m']] = 1e3
cpu_numerical_conversion <- function(cpu_metrics){
  cpu_metrics_updated = cpu_metrics
  for(j in 1:length(cpu_metrics_updated)){
    for(i in 1:length(names(cpu_conversion_list))){
      label_to_prune = names(cpu_conversion_list)[i]
      modified_value = gsub(label_to_prune,"",cpu_metrics[j])
      if(modified_value != cpu_metrics[j]){
        cpu_metrics_updated[j] = as.numeric(modified_value)/cpu_conversion_list[[label_to_prune]]
      } else{
        cpu_metrics_updated[j] = as.numeric(modified_value)/1e3
      }
    }
  }
  return(cpu_metrics_updated)
}


### associate analysis pod to container
pods <- dbReadTable(con, 'pods')
pod_labels_of_interest = c('uwf','nf','cwl')
pipeline_task_pod = pods[grepl('nf|cwl',pods$name),]$id 
runner_pod =  pods[grepl('2uwf',pods$name),]$id
analysis_id = strsplit(basename(dirname(db_file)),"\\_")[[1]]
analysis_id = analysis_id[length(analysis_id)]
#pods

### get labels for each container
containers <- dbReadTable(con, 'containers')
container_labels = c('task','nf','cwl')
pipeline_task_container = containers[containers$pod_id %in% pipeline_task_pod,]$id
pipeline_task_names = pods[pods$id %in% pipeline_task_pod,]$task
runner_container = containers[containers$pod_id %in% runner_pod,]$id
pipeline_runner_names = pods[pods$id %in% runner_pod,]$name
#containers

# Get table
### nemory and cpu usage
container_metrics <- dbReadTable(con, 'container_metrics')
## if pipeline step is short-running, we may loose resolution on CPU/memory usate
pipeline_task_container = pipeline_task_container[pipeline_task_container %in% unique(container_metrics$container_id)]
pipeline_task_names = pipeline_task_names[pipeline_task_container %in% unique(container_metrics$container_id)]
runner_container = runner_container[runner_container %in% unique(container_metrics$container_id)]
pipeline_runner_names = pipeline_runner_names[runner_container %in% unique(container_metrics$container_id)]
#container_metrics
setwd(dirname(db_file))
library(ggplot2)
library(lubridate)

for( i in 1:length(pipeline_task_container)){
  time_x = lubridate::ymd_hms(container_metrics[container_metrics$container_id %in% pipeline_task_container[i],]$timestamp)
  measurement_y = memory_numerical_conversion(container_metrics[container_metrics$container_id %in% pipeline_task_container[i],]$mem_usage) 
  p <- ggplot() + aes(x=time_x,y=as.numeric(measurement_y))  + geom_line(linetype = "dashed") + geom_point()
  p <- p + ggtitle(paste("Memory consumption of pipeline")) + xlab("timestamp") + ylab("Memory consumption in Gb")
  rlog::log_info(paste("Creating PDF for task memory usage:",paste0("analysis_",analysis_id,".",pipeline_task_names[i],".task.memory_consumption.pdf")))
  
  pdf(paste0("analysis_",analysis_id,".",pipeline_task_names[i],".task.memory_consumption.pdf"))
  print(p)
  dev.off()
}

for( i in 1:length(runner_container)){
  time_x = lubridate::ymd_hms(container_metrics[container_metrics$container_id %in% runner_container[i],]$timestamp)
  measurement_y = memory_numerical_conversion(container_metrics[container_metrics$container_id %in%  runner_container[i],]$mem_usage) 
  p <- ggplot() + aes(x=time_x,y=as.numeric(measurement_y))  + geom_line(linetype = "dashed") + geom_point()
  p <- p + ggtitle(paste("Memory consumption of runner")) + xlab("timestamp") + ylab("Memory consumption in Gb")
  rlog::log_info(paste("Creating PDF for pipeline memory usage:",paste0("analysis_",analysis_id,".",pipeline_runner_names[i],".workflow_runner.memory_consumption.pdf")))
  
  pdf(paste0("analysis_",analysis_id,".",pipeline_runner_names[i],".workflow_runner.memory_consumption.pdf"))
  print(p)
  dev.off()
}
#cpu_numerical_conversion(container_metrics[container_metrics$container_id == 4,]$cpu_usage)
for( i in 1:length(pipeline_task_container)){
  time_x = lubridate::ymd_hms(container_metrics[container_metrics$container_id %in%  pipeline_task_container[i],]$timestamp)
  measurement_y = cpu_numerical_conversion(container_metrics[container_metrics$container_id %in%  pipeline_task_container[i],]$cpu_usage) 
  p <- ggplot() + aes(x=time_x,y=as.numeric(measurement_y))  + geom_line(linetype = "dashed") + geom_point()
  p <- p + ggtitle(paste("CPU consumption of pipeline")) + xlab("timestamp") + ylab("CPU usage")
  rlog::log_info(paste("Creating PDF for task cpu usage:",paste0("analysis_",analysis_id,".",pipeline_task_names[i],".task.cpu_consumption.pdf")))
  
  pdf(paste0("analysis_",analysis_id,".",pipeline_task_names[i],".task.cpu_consumption.pdf"))
  print(p)
  dev.off()
}


for( i in 1:length(runner_container)){

  time_x = lubridate::ymd_hms(container_metrics[container_metrics$container_id %in%  runner_container[i],]$timestamp)
  measurement_y = cpu_numerical_conversion(container_metrics[container_metrics$container_id %in%  runner_container[i],]$cpu_usage) 
  p <- ggplot() + aes(x=time_x,y=as.numeric(measurement_y))  + geom_line(linetype = "dashed") + geom_point()
  p <- p + ggtitle(paste("CPU consumption of runner")) + xlab("timestamp") + ylab("CPU usage")
  rlog::log_info(paste("Creating PDF for workflow cpu usage:",paste0("analysis_",analysis_id,".",pipeline_runner_names[i],".workflow_runner.cpu_consumption.pdf")))
  pdf(paste0("analysis_",analysis_id,".",pipeline_runner_names[i],".workflow_runner.cpu_consumption.pdf"))
  print(p)
  dev.off()
}

### initial disk size configuration
file_systems <- dbReadTable(con, 'file_systems')
#file_systems

#### disk usage monitoring
disk_usages <- dbReadTable(con, 'disk_usages')
analysis_disk_usage = disk_usages[grepl("ces",disk_usages$mount_on),]
p <- ggplot() + aes(x=lubridate::ymd_hms(analysis_disk_usage$created_at),y=as.numeric(analysis_disk_usage$used_pct))  + geom_line(linetype = "dashed") + geom_point()
rlog::log_info(paste("Creating PDF for disk usage:",paste0("analysis_",analysis_id,".disk_usage.pdf")))
pdf(paste0("analysis_",analysis_id,".disk_usage.pdf"))
p + ggtitle(paste("analysis_disk_usage")) + xlab("timestamp") + ylab("disk usage %")
dev.off()

setwd(Sys.getenv('HOME'))

