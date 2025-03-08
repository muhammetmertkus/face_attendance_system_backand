FROM python:3.9-slim

# Önerilen etiketler
LABEL Name="face_attendance_system" \
      Version="1.0.0" \
      Description="Yüz tanıma ile yoklama sistemi"

WORKDIR /app

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    zlib1g-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Uygulama dosyalarını kopyala
COPY . .

# Önceden derlenmiş paketleri kullan
RUN pip install --upgrade pip && \
    pip install wheel && \
    pip install --no-cache-dir numpy==1.26.4 && \
    pip install --no-cache-dir Pillow==9.5.0 && \
    pip install --no-cache-dir dlib==19.24.0 && \
    pip install --no-cache-dir face-recognition==1.3.0 && \
    pip install --no-cache-dir -r requirements.txt

# Uygulama portunu belirt
EXPOSE 5000

# Uygulamayı başlat
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"] 