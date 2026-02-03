# Use a slim Python base image
FROM python:3.9-slim-buster

# Rest of your Dockerfile
# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

COPY requirements.txt .

# Install system dependencies (adjust as needed for specific InsightFace models or features)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
	tesseract-ocr tesseract-ocr-hin \
    libgl1-mesa-glx \
	libglib2.0-0 \
	vim \
	telnet\
    && rm -rf /var/lib/apt/lists/*
	

# Install InsightFace and other Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir  --no-warn-script-location -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
#ENV NAME World



# Run app.py when the container launches
CMD ["python", "news_app.py"]