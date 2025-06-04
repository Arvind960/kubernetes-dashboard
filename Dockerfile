FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY k8s_dashboard_server.py .
COPY templates/ templates/
COPY static/ static/

# Expose the port the app runs on
EXPOSE 8888

# Command to run the application
CMD ["python", "k8s_dashboard_server.py"]
