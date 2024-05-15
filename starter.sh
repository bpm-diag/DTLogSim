#!/bin/bash
# Change directory to the "3.6" folder
cd 3.6

# Call the Python interpreter from your virtual environment
../myenv/bin/python bpmnParsing.py

# Restore back to the original directory (optional)
cd ..

# Change directory to the "3.11" folder
cd 3.11

# Call the Python interpreter from your virtual environment
../myenv312/bin/python main.py

# Restore back to the original directory (optional)
cd ..

# Pause to keep the terminal window open (optional)
read -p "Press enter to continue"
