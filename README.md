# Yüz Tanıma ile Yoklama Sistemi

Bu proje, yüz tanıma teknolojisi kullanarak yoklama almayı ve duygu analizi yapmayı amaçlayan bir sistemdir. Sistem, öğretmenlerin öğrencilerin yoklamasını hızlı ve doğru bir şekilde almasına olanak tanırken, aynı zamanda öğrencilerin dersteki genel duygu durumunu analiz ederek geri bildirim sağlamayı hedefler.

## Kullanılan Teknolojiler

- **Backend:** Flask API
- **Veritabanı:** SQLite3
- **Yüz Tanıma:** face-recognition
- **Duygu Analizi:** FER (Face Emotion Recognizer)
- **Kimlik Doğrulama:** JWT (JSON Web Token)
- **API Dokümantasyonu:** Swagger UI

## Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- CMake (face-recognition kütüphanesi için)
- C++ Derleyici (face-recognition kütüphanesi için)

### Adımlar

1. Projeyi klonlayın:
   ```
   git clone https://github.com/kullanici/face_backend.git
   cd face_backend
   ```

2. Sanal ortam oluşturun ve aktifleştirin:
   ```
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. Gerekli paketleri yükleyin:
   ```
   pip install -r requirements.txt
   ```

4. Veritabanını oluşturun:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. Uygulamayı çalıştırın:
   ```
   flask run
   ```

6. Tarayıcınızda aşağıdaki adresi açarak API dokümantasyonuna erişebilirsiniz:
   ```
   http://localhost:5000/api/docs
   ```

## Test Verileri

Sistemi test etmek için örnek veriler ekleyebilirsiniz. Bunun için önce bir admin kullanıcısı oluşturun ve giriş yapın, ardından `/api/admin/seed-database` endpointini kullanarak örnek verileri ekleyin.

### Admin Kullanıcısı Oluşturma

```
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin"
  }'
```

### Giriş Yapma

```
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'
```

Dönen yanıttan `access_token` değerini alın ve aşağıdaki isteklerde kullanın.

### Örnek Verileri Ekleme

```
curl -X POST http://localhost:5000/api/admin/seed-database \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## API Endpointleri

API endpointleri hakkında detaylı bilgi için Swagger dokümantasyonunu kullanabilirsiniz:

```
http://localhost:5000/api/docs
```

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın. 