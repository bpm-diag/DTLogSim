@echo off

echo Activating virtual environment...
call interfaceVenv\Scripts\activate.bat

echo Running Flask app in DEBUG mode...
cd scripts
set FLASK_APP=app.py 
set FLASK_ENV=development
flask --app app.py --debug run

pause 