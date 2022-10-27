# scripts and demo code to monitor analysis runs in ICA
# Tested with python version >= 3.9
####### scripts and demo code to monitor analysis runs in ICA
- test_websocket.py
- requirements.txt --- contains modules to run ```pip install``` on
# If analysis run is InProgress --- this script hopes to help stream logs
# If analysis run is completed (i.e. Succeeded or Failed)--- this script will download the logs

# template command line
```bash
python3 test_websocket.py --api-key-file {FILE} [--project_name {STR}|--project-id {STR}] [OPTIONAL:--analysis_name {STR} | --analysis_id {STR}]
```
- ```--api-key-file``` : path to text file that contains [your API key](https://help.ica.illumina.com/account-management/am-iam#api-keys)
- ```--project_name``` : name of youor ICA project or ```--project-id``` : project id of your ICA project
- ```--analysis_name``` : user_reference or name of your analysis run or  ```--analysis_id``` : analysis id of the analysis you want to monitor

If both ```--analysis_name``` and ```--analysis_id``` are undefined, the script will try to grab/monitor logs from the most recent analysis run in your ICA project

# Rscript extension
- An additional Rscript is provided to help parse the JSON message returned from the ICA getAnalysisSteps endpoint and provide a table containing steps to monitor a running pipeline.
This can be particularly useful for nextflow-based pipelines. An example command-line to run this script can be found below:

```bash
	 Rscript ica.analysis_table.R --process-steps $PWD/analysis_id_{ANALYSIS_ID}/step_metadata.txt
```
- directory where ```step_metadata.txt``` is generated will be created by the python script above
	
# limitations
- Distinguishes between analysis runs that have the same user_reference
  - picks the most recent analysis with the user_reference name
