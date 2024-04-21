@echo off
REM Change directory to the "3.6" folder
cd 3.6

REM Ask for input
set /p userinput="Enter bpmn name (without .bpmn): "

REM Call the Python interpreter from your virtual environment
..\myenv\Scripts\python.exe bpmnParsing.py %userinput%

REM Restore back to the original directory (optional)
cd ..

