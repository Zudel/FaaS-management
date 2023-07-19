# Dockerfile for GUI Python 
FROM python:3.9-slim
# Set the working directory to /app
WORKDIR /app
# Copy the current directory contents into the container at /app
ADD ./gui /app
# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y tk libx11-dev

EXPOSE  8000
# Run app.py when the container launches
CMD ["bash", "-c", "export DISPLAY=:0 && python main.py"]
