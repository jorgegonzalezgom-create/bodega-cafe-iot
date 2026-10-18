# Dockerfile: receta para construir el contenedor de la app Flask

# 1. Parte de una imagen que ya trae Python 3.12
FROM python:3.12-slim

# 2. Carpeta de trabajo dentro del contenedor
WORKDIR /app

# 3. Copia la lista de librerias y las instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia el codigo de la aplicacion
COPY app.py .

# 5. Comando que se ejecuta al arrancar el contenedor
CMD ["python", "app.py"]
