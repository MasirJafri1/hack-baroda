# =======================================================================
# Stage 1: Build the React/Vite Frontend
# =======================================================================
FROM node:18-alpine AS frontend-builder
WORKDIR /app/Frontend
COPY Frontend/package*.json ./
RUN npm install
COPY Frontend/ ./
RUN npm run build

# =======================================================================
# Stage 2: Assemble FastAPI Backend & Static Files
# =======================================================================
FROM python:3.11-slim
WORKDIR /app

# Copy backend requirements and install dependencies
COPY Backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY Backend/ .

# Copy compiled frontend assets from Stage 1 into the backend's dist folder
COPY --from=frontend-builder /app/Frontend/dist ./dist

# Expose backend server port
EXPOSE 8000

# Start FastAPI ASGI server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
