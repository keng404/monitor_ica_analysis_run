# CWL-based pipeline
1. Find command line tool towards the end of the pipeline
2. Add dirent
   - start with your command
   - then add the following:
  ```cp -r /mounted-ica-user-dir/* $(runtime.outdir)/```
3. Add the following under ```requirements``` for your command-line tool:
    - ```class: InlineJavascriptRequirement```
    - ```class: InitialWorkDirRequirement```
4. Add this to your tool output in the CWL script
```bash
  pipeline_db_files:
    type:
      type: array
      items: File
    outputBinding:
      glob:
      - '*.db'
      - '*.log'
  debugging_directory:
    type:
      type: array
      items: Directory
    outputBinding:
      glob:
      - '*bpe*'
      - '*ica*'
```
5. Add debugging directories and pipeline_db files to your workflow.cwl under the ouutputs section. It will look like something like this:
```bash
tso500_solid__debugging_directory:
    outputSource: tso500_solid/debugging_directory
    type: Directory[]?
  tso500_solid__pipeline_db_files:
    outputSource: tso500_solid/pipeline_db_files
    type: File[]?
```

# Nextflow-based pipeline
1. Find your ```main.nf``` file in ICA for your pipeline, make sure you are in edit mode.
2. Add the following to the bottom of your pipeline
```bash
workflow.onComplete {
['cp','-r',"${workflow.launchDir}/.ica/user","${workflow.launchDir}/out"].execute()
}
```
or
```bash
workflow.onError {
['cp','-r',"${workflow.launchDir}/.ica/user","${workflow.launchDir}/out"].execute()
}
```