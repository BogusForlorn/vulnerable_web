# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Initialize the database
RUN python setup.py

# Expose port 5000 to the outside world
EXPOSE 5000

# Run gunicorn server
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "vuln_app:app"]
