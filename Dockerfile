# Frontend Stage: Build React App
FROM node:18 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/ .
RUN npm install && npm run build

# Backend Stage: Flask API
FROM python:3.10 AS backend
WORKDIR /app
COPY backend/ .
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expose the Flask port
EXPOSE 5000
# Start Flask
# RUN ["flask", "db", "upgrade"]
CMD ["flask", "db", "upgrade", "&&", "python", "app.py"]
