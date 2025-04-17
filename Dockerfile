# --- Étape 1 : build du frontend React ---
    FROM node:18 AS frontend

    WORKDIR /app/frontend
    COPY frontend/ /app/frontend
    RUN npm install && npm run build
    
    # --- Étape 2 : setup backend Flask ---
    FROM python:3.11-slim
    
    # Install Python deps
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Copier le backend
    COPY . /app
    
    # Copier les fichiers buildés de React dans un dossier frontend_dist
    COPY --from=frontend /app/frontend/dist /app/frontend_dist
    
    # Exposer port Flask
    EXPOSE 5002
    
    # Start Flask
    CMD ["python", "app.py"]
    