# Base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose the default port (optional)
EXPOSE 8000

# Command to run the app
CMD ["python", "app.py"]