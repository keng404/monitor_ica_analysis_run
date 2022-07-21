####### scripts and demo code to monitor analysis runs in ICA
- test_websocket.py
- requirements.txt --- contains modules to run ```pip install``` on

# template command line
```bash
python3 test_websocket.py --api-key-file {FILE} [--project_name {STR}|--project-id {STR}] [OPTIONAL:--analysis_name {STR} | --analysis_id {STR}]
```
- ```--api-key-file``` : path to text file that contains [your API key](https://help.ica.illumina.com/account-management/am-iam#api-keys)
- ```--project_name``` : name of youor ICA project
- ```--project-id``` : project id of your ICA project
- ```--analysis_name``` : user_reference or name of your analysis run
- ```--analysis_id``` : analysis id of the analysis you want to monitor

If both ```--analysis_name``` and ```--analysis_id``` are undefined, the script will try to grab/monitor logs from the most recent analysis run in your ICA project

# limitations
- Distinguishes between analysis runs that have the same user_reference
  - picks the most recent analysis with the user_reference name