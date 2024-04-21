To install (first time only, windows instructions, run by cmd inside this folder):

python3.12 -m venv myenv312
myenv312/bin/activate
pip install -r requirements_3.12.txt

python3.6 -m venv myenv
myenv/bin/activate
pip install -r requirements_3.6.txt

Instead of "python3.12" and "python3.6" commands, use any command that lets you run python on versions 3.12 and then 3.6.
This software in facts works using 2 different versions of python due to library compatibility issues, and therefore uses 2 venvs with different python versions.



To run: use STARTER.BAT



-----------------WARNING----------------
the repo has been moved to: https://github.com/bpm-diag/bp-simulation