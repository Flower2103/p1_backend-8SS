FROM debian:12

# ----------------------------
# Instalar dependencias base
# ----------------------------
RUN apt update && apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    nginx && \
    apt clean

# Permitir pip (evita el error de PEP 668)
RUN mkdir -p /usr/local/lib/python3.11/dist-packages

# ----------------------------
# Crear usuario
# ----------------------------
RUN useradd -m floruser

# ----------------------------
# Copiar aplicación
# ----------------------------
WORKDIR /app
COPY app/ /app/

# ----------------------------
# Instalar Flask correctamente
# ----------------------------
RUN pip3 install --break-system-packages flask

# ----------------------------
# Configurar Nginx
# ----------------------------
RUN rm /etc/nginx/sites-enabled/default
COPY nginx.conf /etc/nginx/sites-enabled/default

# ----------------------------
# Exponer puerto 80
# ----------------------------
EXPOSE 80

# ----------------------------
# Iniciar Nginx y Flask
# ----------------------------
CMD ["bash", "-c", "service nginx start && python3 /app/app.py"]

