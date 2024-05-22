To install with Docker:
docker build -t diagbp .

To run with Docker (substitute the paths):
docker run -it --rm -v "AbsolutePathOfTheFolderWithBpmnFiles:/app/bpmn_input_file_here" -v "AbsolutePathOfTheFolderWhereToSaveLogFiles:/app/logs" [-v "AbsolutePathOfTheFolderWithConfigFile:/app/json"] diagbp

Example run:
docker run -it --rm -v "D:\User\Documents\GitHub\Tesi_magistrale\bpmn_input_file_here:/app/bpmn_input_file_here" -v "D:\User\Documents\GitHub\Tesi_magistrale\logs:/app/logs" diagbp 

The config file is optional and for advanced usage. If used, the config file needs to be called "diagbp.json" and it must contain what is contained in the diagbp tag in the bpmn file



---------------------


To install without Docker (first time only, windows instructions but also works similar on linux, run by cmd inside this folder):

python3.11 -m venv myenv312
myenv312/bin/Activate (if error is given try myenv312/bin/activate otherwise open powershell and execute: Set-ExecutionPolicy Unrestricted -Force)
pip install -r requirements_3.11.txt

python3.6 -m venv myenv
myenv/bin/Activate (same as before)
pip install -r requirements_3.6.txt

Instead of "python3.11" and "python3.6" commands, use any command that lets you run python on versions 3.11 and then 3.6.
This software in facts works using 2 different versions of python due to library compatibility issues, and therefore uses 2 venvs with different python versions.


To run without Docker: use STARTER.BAT