# Use a Python 3.11 base image 
FROM python:3.11-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Set Flask environment for development
ENV FLASK_ENV=development

# Create a working directory in the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirementsInterface.txt requirementsInterface.txt
RUN pip install --no-cache-dir -r requirementsInterface.txt 

# Copy the entire application
COPY . /app

WORKDIR /app/scripts  

# Expose the Flask port
EXPOSE 5000

# Define the command to run your Flask app with the development server
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]