#!/usr/bin/env python

# WS client example
import sys
import asyncio
import os
import asyncio
import websockets
from websockets import exceptions
import argparse
import requests
from requests.structures import CaseInsensitiveDict
import pprint
from pprint import pprint
import json
import time
import re
from time import sleep
import random
###############################################
import logging
logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
##############
def get_analysis_info(api_key,project_id,analysis_id):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        pipeline_info = requests.get(full_url, headers=headers)
    except:
        raise ValueError(f"Could not get pipeline_info for analysis {analysis_id} in project: {project_id}")
    return pipeline_info.json()
##############################
def get_project_id(api_key, project_name):
    projects = []
    pageOffset = 0
    pageSize = 30
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects?search={project_name}&includeHiddenProjects=true&pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectPagedList = requests.get(full_url, headers=headers)
        totalRecords = projectPagedList.json()['totalItemCount']
        while page_number * pageSize < totalRecords:
            projectPagedList = requests.get(full_url, headers=headers)
            for project in projectPagedList.json()['items']:
                projects.append({"name": project['name'], "id": project['id']})
            page_number += 1
            number_of_rows_to_skip = page_number * pageSize
    except:
        raise ValueError(f"Could not get project_id for project: {project_name}")
    if len(projects) > 1:
        raise ValueError(f"There are multiple projects that match {project_name}")
    else:
        return projects[0]['id']
############
def list_project_analyses(api_key,project_id,max_retries=20):
    # List all analyses in a project
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses?pageOffset={pageOffset}&pageSize={pageSize}"
    analyses_metadata = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectAnalysisPagedList = None
        response_code = 404
        num_tries = 0
        while response_code != 200 and num_tries  < max_retries:
            num_tries += 1
            if num_tries > 1:
                print(f"NUM_TRIES:\t{num_tries}\tTrying to get analyses  for project {project_id}")
            sleep(random.uniform(1, 3))
            projectAnalysisPagedList = requests.get(full_url, headers=headers)
            totalRecords = projectAnalysisPagedList.json()['totalItemCount']
            response_code = projectAnalysisPagedList.status_code
            while page_number * pageSize < totalRecords:
                endpoint = f"/api/projects/{project_id}/analyses?pageOffset={number_of_rows_to_skip}&pageSize={pageSize}"
                full_url = api_base_url + endpoint  ############ create header
                projectAnalysisPagedList = requests.get(full_url, headers=headers)
                for analysis in projectAnalysisPagedList.json()['items']:
                    analyses_metadata.append(analysis)
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
    except:
        raise ValueError(f"Could not get analyses for project: {project_id}")
    return analyses_metadata
################
def get_project_analysis_id(api_key,project_id,analysis_name):
    desired_analyses_status = ["REQUESTED","INPROGRESS","SUCCEEDED","FAILED"]
    analysis_id  = None
    analyses_list = list_project_analyses(api_key,project_id)
    if analysis_name is not None:
        for aidx,project_analysis in enumerate(analyses_list):
            name_check  = project_analysis['userReference'] == analysis_name 
            status_check = project_analysis['status'] in desired_analyses_status
            if project_analysis['userReference'] == analysis_name and project_analysis['status'] in desired_analyses_status:
                analysis_id = project_analysis['id']
                return analysis_id
    else:
        idx_of_interest = 0
        status_of_interest = analyses_list[idx_of_interest]['status'] 
        current_analysis_id = analyses_list[idx_of_interest]['id'] 
        while status_of_interest not in desired_analyses_status:
            idx_of_interest = idx_of_interest + 1
            status_of_interest = analyses_list[idx_of_interest]['status'] 
            current_analysis_id = analyses_list[idx_of_interest]['id'] 
            print(f"analysis_id:{current_analysis_id} status:{status_of_interest}")
        default_analysis_name = analyses_list[idx_of_interest]['userReference']
        print(f"No user reference provided, will poll the logs for the analysis {default_analysis_name}")
        analysis_id = analyses_list[idx_of_interest]['id']
    return analysis_id
##########################################
def get_analysis_metadata(api_key,project_id,analysis_id):
         # List all analyses in a project
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}"
    analysis_metadata = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectAnalysis = requests.get(full_url, headers=headers)
        analysis_metadata = projectAnalysis.json()
        ##print(pprint(analysis_metadata,indent=4))
    except:
        raise ValueError(f"Could not get analyses metadata for project: {project_id}")
    return analysis_metadata

def find_db_file(api_key,project_id,analysis_metadata,search_query = "metrics.db"):
    db_file = None
    ### assume user has not output the results of analysis to custom directory
    search_query_path = "/" + analysis_metadata['reference'] + "/" 
    search_query_path_str = [re.sub("/", "%2F", x) for x in search_query_path]
    search_query_path = "".join(search_query_path_str)
    datum = []
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data?filename={search_query}&filenameMatchMode=FUZZY&pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        #print(full_url)
        projectDataPagedList = requests.get(full_url, headers=headers)
        if projectDataPagedList.status_code == 200:
            if 'totalItemCount' in projectDataPagedList.json().keys():
                totalRecords = projectDataPagedList.json()['totalItemCount']
                while page_number * pageSize < totalRecords:
                    endpoint = f"/api/projects/{project_id}/data?filename={search_query}&filenameMatchMode=FUZZY&pageOffset={pageOffset}&pageSize={pageSize}"
                    full_url = api_base_url + endpoint  ############ create header
                    projectDataPagedList = requests.get(full_url, headers=headers)
                    for projectData in projectDataPagedList.json()['items']:
                        if re.search(analysis_metadata['reference'],projectData['data']['details']['path']) is not None:
                            datum.append({"name": projectData['data']['details']['name'], "id": projectData['data']['id'],
                                    "path": projectData['data']['details']['path']})
                    page_number += 1
                    number_of_rows_to_skip = page_number * pageSize
            else:
                for projectData in projectDataPagedList.json()['items']:
                    if re.search(analysis_metadata['reference'],projectData['data']['details']['path']) is not None:
                        datum.append({"name": projectData['data']['details']['name'], "id": projectData['data']['id'],
                                "path": projectData['data']['details']['path']}) 
        else:
            print(f"Could not get results for project: {project_id} looking for filename: {search_query}")
    except:
        print(f"Could not get results for project: {project_id} looking for filename: {search_query}")
    if len(datum) > 0:
        if len(datum) > 1:
            print(f"Found more than 1 matching DB file for project: {project_id}")
            pprint(datum,indent = 4)
        db_file = datum[0]['id']
    return db_file
#####################################################
def get_analysis_steps(api_key,project_id,analysis_id):
     # List all analyses in a project
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}/steps"
    analysis_step_metadata = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectAnalysisSteps = requests.get(full_url, headers=headers)
        test_response = projectAnalysisSteps.json()
        if 'items' in test_response.keys():
            for step in projectAnalysisSteps.json()['items']:
                analysis_step_metadata.append(step)
        else:
            print(pprint(test_response,indent=4))
            raise ValueError(f"Could not get analyses steps for project: {project_id}")
    except:
        raise ValueError(f"Could not get analyses steps for project: {project_id}")
    return analysis_step_metadata
#################
def file_or_stream(analysis_step_metadata):
    log_status = None
    for step in analysis_step_metadata:
        if 'stdOutData' in step['logs'].keys() or 'stdErrData' in step['logs'].keys()  :
            log_status = 'file'
        elif 'stdOutStream' in step['logs'].keys() or 'stdErrStream' in step['logs'].keys()  :
            log_status = 'stream'
    return log_status
###################
def download_data_from_url(download_url,output_name=None):
    command_base = ["wget"]
    if output_name is not None:
        output_name = '"' + output_name + '"' 
        command_base.append("-O")
        command_base.append(f"{output_name}")
    command_base.append(f"{download_url}")
    command_str = " ".join(command_base)
    print(f"Running: {command_str}")
    os.system(command_str)
    return print(f"Downloading from {download_url}")

def download_file(api_key,project_id,data_id,output_path):
    # List all analyses in a project
    api_base_url = os.environ['ICA_BASE_URL']+ "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data/{data_id}:createDownloadUrl"
    download_url = None
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        downloadFile = requests.post(full_url, headers=headers)
        download_url = downloadFile.json()['url']
        download_url = '"' + download_url + '"'
        download_data_from_url(download_url,output_path)
    except:
        raise ValueError(f"Could not get analyses streams for project: {project_id}")

    return print(f"Completed download from {download_url}")
##################
 
async def stream_log(uri,extra_headers):
    async with websockets.connect(uri,extra_headers=extra_headers) as ws:
        try:
            text = await ws.recv()
            print(f"< {text.rstrip()}")
        except (exceptions.ConnectionClosedError,exceptions.ConnectionClosed):
            print(f"Connection closed")
            return
#################################################
def generate_step_file(step_object,output_path):
    f = open(output_path, "w")
    for s1 in json.dumps(step_object,indent=4,sort_keys=True): 
            f.write(s1)
    f.close()
    return print(f"Created {output_path}")
###############################################    
def get_logs(api_key,project_id,analysis_id,extra_headers):
    analysis_step_metadata = get_analysis_steps(api_key,project_id,analysis_id)
    if os.path.isdir(f"analysis_id_{analysis_id}") is False:
        os.mkdir(f"analysis_id_{analysis_id}")
    while len(analysis_step_metadata) < 1:
        analysis_step_metadata = get_analysis_steps(api_key,project_id,analysis_id)
    generate_step_file(analysis_step_metadata,f"analysis_id_{analysis_id}/step_metadata.txt")
    for step in analysis_step_metadata:
        log_status = file_or_stream([step])
        step_name = step['id']
        if log_status == "file":
            if 'stdOutData' in step['logs'].keys():
                stdout_path = step['logs']['stdOutData']['details']['path']
                stdout_id = step['logs']['stdOutData']['id']
                print(f"For {step_name} Downloading the log for {stdout_path}")
                download_file(api_key,project_id,stdout_id,f"analysis_id_{analysis_id}/" +step_name +".stdout.log")
            else:
                sys.stderr.write(f"Cannot find stdOutData for {step_name}")
                pprint(step['logs'],indent = 4)
            if 'stdErrData' in step['logs'].keys():
                stderr_path = step['logs']['stdErrData']['details']['path']
                stderr_id = step['logs']['stdErrData']['id']
                print(f"For {step_name} Downloading the log for {stderr_path}")
                download_file(api_key,project_id,stderr_id,f"analysis_id_{analysis_id}/" +step_name +".stderr.log")
            else:
                sys.stderr.write(f"Cannot find stdErrData for {step_name}")
                pprint(step['logs'],indent = 4)
        elif log_status == "stream":
        ### assume stream
            stdout_websocket = step['logs']['stdOutStream']
            print(f"For step: {step_name}, streaming {stdout_websocket}")
            asyncio.get_event_loop().run_until_complete(stream_log(stdout_websocket,extra_headers))
            stderr_websocket = step['logs']['stdErrStream']
            print(f"For step: {step_name}, streaming {stderr_websocket}")
            asyncio.get_event_loop().run_until_complete(stream_log(stderr_websocket,extra_headers))
        else:
            print(f"Nothing to do for step {step_name}, analysis {analysis_id} is not running that step")
    return print(f"Finished getting logs for {analysis_id}")

###################################################
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_id',default=None, type=str, help="ICA project id [OPTIONAL]")
    parser.add_argument('--project_name',default=None, type=str, help="ICA project name")
    parser.add_argument('--analysis_id', default=None, type=str, help="ICA analysis id")
    parser.add_argument('--analysis_name', default=None, type=str, help="ICA analysis name --- analysis user reference")
    parser.add_argument('--api_key_file', default=None, type=str, help="file that contains API-Key")
    parser.add_argument('--server_url', default='https://ica.illumina.com', type=str, help="ICA base URL")
    args, extras = parser.parse_known_args()
    #############
    project_id = args.project_id
    project_name = args.project_name
    analysis_id = args.analysis_id
    analysis_name = args.analysis_name
    os.environ['ICA_BASE_URL'] = args.server_url
    ###### read in api key file
    my_api_key = None
    if args.api_key_file is not None:
        if os.path.isfile(args.api_key_file) is True:
            with open(args.api_key_file, 'r') as f:
                my_api_key = str(f.read().strip("\n"))
    if my_api_key is None:
        raise ValueError("Need API key")
    # import websocket_client
    if project_id is None and project_name is not None:
        project_id = get_project_id(my_api_key,project_name)

    if project_id is None:
        raise ValueError("Need to provide project name or project id")

    if analysis_id is None:
        analysis_id = get_project_analysis_id(my_api_key,project_id,analysis_name)
    if analysis_id is None:
        raise ValueError("Need to provide project name or analysis id or you may need to check if the analysis id you are looking at has been aborted or did not run")
    # get logs for a given analysis
    ############
    extra_headers = {}
    extra_headers['Origin'] = os.environ['ICA_BASE_URL']
    extra_headers['User-Agent'] = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Mobile Safari/537.36"
    ####
    ### obtain info for pipeline run
    analysis_info = get_analysis_info(my_api_key,project_id,analysis_id)
    if 'startDate'  in list(analysis_info.keys()):
        get_logs(my_api_key,project_id,analysis_id,extra_headers)
    else:
        print(f"It appears that {analysis_id} failed before it was run")
    ### obtain analysis run metadata so we can check the results
    analysis_run_metadata = get_analysis_metadata(my_api_key,project_id,analysis_id)
    db_file_id = find_db_file(api_key = my_api_key,project_id = project_id,analysis_metadata=analysis_run_metadata)
    if db_file_id is not None:
        print(f"Found db file: {db_file_id}.\nDownloading\n")
        download_file(api_key = my_api_key,project_id = project_id,data_id = db_file_id,output_path =f"analysis_id_{analysis_id}/metrics.db")
        plot_generation_cmd = ["Rscript","ica_pipelines.check_out_workflow_metrics.R","--db-file",f"analysis_id_{analysis_id}/metrics.db"]
        plot_generation_cmd_str = " ".join(plot_generation_cmd)
        print(f"Running: {plot_generation_cmd_str}")
        os.system(plot_generation_cmd_str)
    else:
        print(f"It appears that {analysis_id} does not have kubernetes metrics file.\nSkippiing CPU and Memory plot generation")

if __name__ == "__main__":
    main()
