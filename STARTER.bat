call parse.bat
@echo off
REM Change directory to the "3.11" folder
cd 3.11

REM Call the Python interpreter from your virtual environment
..\myenv312\Scripts\python.exe main.py

REM Restore back to the original directory (optional)
cd ..

REM Pause to keep the command prompt window open (optional)
pause