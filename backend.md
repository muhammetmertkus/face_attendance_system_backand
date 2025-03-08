# Yüz Tanıma ile Yoklama Sistemi Backend

Bu doküman, yüz tanıma ile yoklama sistemi projesinin backend servisinin detaylarını içermektedir.

**Kullanılan Teknolojiler:**

*   **Yüz Tanıma:** face-recognition
*   **Duygu Analizi:** FER (Face Emotion Recognizer)
*   **API:** Flask API
*   **Veritabanı:** SQLite3
    
## Proje Tanımı

Bu proje, yüz tanıma teknolojisi kullanarak yoklama almayı ve duygu analizi yapmayı amaçlayan bir sistemdir. Sistem, öğretmenlerin öğrencilerin yoklamasını hızlı ve doğru bir şekilde almasına olanak tanırken, aynı zamanda öğrencilerin dersteki genel duygu durumunu analiz ederek geri bildirim sağlamayı hedefler.

## API Endpointleri

Aşağıda, sistemdeki tüm API endpointleri, istek/yanıt formatları ve erişim yetkileri detaylı olarak açıklanmıştır.

### 1. Kimlik Doğrulama (Authentication)

*   **Amaç:** Kullanıcıların kimliklerini doğrulamak ve yetkilendirmek için kullanılır.

    *   🔐 **Kimlik Doğrulama** tag'i ile işaretlenmiştir.

*   **Endpointler:**

    *   **POST /api/auth/register** - Yeni kullanıcı kaydı
        *   **İstek:**
            ```json
            {
                "email": "ornek@example.com",
                "password": "guclu_sifre123",
                "first_name": "Ahmet",
                "last_name": "Yılmaz",
                "role": "teacher"
            }
            ```
        *   **Yanıtlar:**
            *   201: Kullanıcı başarıyla kaydedildi.
            *   400: Email zaten kayıtlı.
    *   **POST /api/auth/login** - Kullanıcı girişi
        *   **İstek:**
            ```json
            {
                "email": "admin@example.com",
                "password": "admin123"
            }
            ```
        *   **Yanıtlar:**
            *   200: Başarılı giriş.
                ```json
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5...",
                    "token_type": "bearer",
                    "user": {
                        "id": 1,
                        "email": "admin@example.com",
                        "first_name": "Admin",
                        "last_name": "User",
                        "role": "admin",
                        "teacher_id": null,
                        "student_id": null
                    }
                }
                ```
            *   401: Geçersiz kimlik bilgileri.
    *   **POST /api/auth/refresh** - Access token yenileme
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Yanıtlar:**
            *   200: Token başarıyla yenilendi.
                ```json
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5..."
                }
                ```
            *   401: Geçersiz veya süresi dolmuş refresh token.
    *   **GET /api/auth/me** - Mevcut kullanıcı bilgilerini getir
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Yanıtlar:**
            *   200: Kullanıcı bilgileri başarıyla getirildi.
                ```json
                {
                    "id": 1,
                    "email": "admin@example.com",
                    "first_name": "Admin",
                    "last_name": "User",
                    "role": "admin"
                }
                ```
            *   404: Kullanıcı bulunamadı.
    *   **PUT /api/auth/me** - Mevcut kullanıcı bilgilerini güncelle
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **İstek:**
            ```json
            {
                "password": "yeni_sifre123",
                "first_name": "Yeni Ad",
                "last_name": "Yeni Soyad"
            }
            ```
        *   **Yanıtlar:**
            *   200: Kullanıcı bilgileri başarıyla güncellendi.
                ```json
                {
                    "id": 1,
                    "email": "admin@example.com",
                    "first_name": "Yeni Ad",
                    "last_name": "Yeni Soyad",
                    "role": "admin"
                }
                ```
            *   404: Kullanıcı bulunamadı.
            *   500: Kullanıcı güncellenemedi.

### 2. Öğretmenler (Teachers)

*   **Amaç:** Öğretmenlerin yönetimi için kullanılır.

    *   👨‍🏫 **Öğretmenler** tag'i ile işaretlenmiştir.

*   **Endpointler:**

    *   **GET /api/teachers** - Tüm öğretmenleri listele
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   401: Yetkisiz erişim.
            *   500: Öğretmenler listelenemedi.
    *   **POST /api/teachers** - Yeni öğretmen oluştur
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **İstek:**
            ```json
            {
                "email": "ogretmen@example.com",
                "password": "sifre123",
                "first_name": "Ahmet",
                "last_name": "Yılmaz",
                "department": "Bilgisayar Mühendisliği",
                "title": "Dr. Öğr. Üyesi"
            }
            ```
        *   **Yanıtlar:**
            *   201: Öğretmen başarıyla oluşturuldu.
            *   400: Email zaten kullanılıyor.
            *   500: Öğretmen oluşturulamadı.
    *   **GET /api/teachers/{teacher_id}** - Öğretmen detayını getir
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `teacher_id` (integer, gerekli): Öğretmen ID
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   404: Öğretmen bulunamadı.
    *   **PUT /api/teachers/{teacher_id}** - Öğretmen bilgilerini güncelle
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `teacher_id` (integer, gerekli): Öğretmen ID
        *   **İstek:**
            ```json
            {
                "email": "yeni_ogretmen@example.com",
                "first_name": "Yeni Ahmet",
                "last_name": "Yeni Yılmaz",
                "department": "Elektrik Elektronik Mühendisliği",
                "title": "Prof. Dr."
            }
            ```
        *   **Yanıtlar:**
            *   200: Öğretmen başarıyla güncellendi.
            *   404: Öğretmen bulunamadı.
            *   500: Öğretmen güncellenemedi.
    *   **DELETE /api/teachers/{teacher_id}** - Öğretmeni sil
        *   **Gereksinim:** `bearerAuth` (JWT token), Admin yetkisi
        *   **Parametreler:**
            *   `teacher_id` (integer, gerekli): Silinecek öğretmenin ID'si
        *   **Yanıtlar:**
            *   200: Öğretmen başarıyla silindi.
            *   400: Öğretmenin aktif dersleri var.
            *   401: Yetkisiz erişim.
            *   403: Bu işlem için admin yetkisi gerekli.
            *   404: Öğretmen bulunamadı.
            *   500: Öğretmen silinemedi.
    *   **GET /api/teachers/{teacher_id}/courses** - Öğretmenin derslerini getir
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `teacher_id` (integer, gerekli): Öğretmen ID
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu işlem için yetkiniz yok.
            *   404: Öğretmen bulunamadı.
    *   **POST /api/teachers/forgot-password** - Öğretmen şifre hatırlatma
        *   **İstek:**
            ```json
            {
                "email": "ornek@example.com"
            }
            ```
        *   **Yanıtlar:**
            *   200: Şifre hatırlatma başarılı.
            *   400: Geçersiz istek.
            *   404: Öğretmen bulunamadı.
            *   500: Sunucu hatası.

### 3. Öğrenciler (Students)

*   **Amaç:** Öğrencilerin yönetimi için kullanılır.

    *   👨‍🎓 **Öğrenciler** tag'i ile işaretlenmiştir.

*   **Endpointler:**

    *   **POST /api/students/create-with-face** - Yeni öğrenci oluştur ve yüz fotoğrafı yükle
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **İstek:** `multipart/form-data`
            ```
            file: (JPEG/PNG formatında öğrenci yüz fotoğrafı)
            email: (string, gerekli, örnek: ogrenci@example.com)
            password: (string, gerekli, örnek: sifre123)
            first_name: (string, gerekli, örnek: Ali)
            last_name: (string, gerekli, örnek: Öğrenci)
            student_number: (string, gerekli, örnek: 20240001)
            department: (string, gerekli, örnek: Bilgisayar Mühendisliği)
            ```
        *   **Açıklama:** Bu endpoint, yeni bir öğrenci oluştururken aynı anda yüz fotoğrafını yüklemeyi sağlar. Fotoğraf, yüz tanıma sistemi için kullanılacaktır.
        *   **Yanıtlar:**
            *   201: Öğrenci başarıyla oluşturuldu ve fotoğraf yüklendi.
                ```json
                {
                    "id": 123,
                    "student_number": "20240001",
                    "user": {
                        "id": 456,
                        "email": "ogrenci@example.com",
                        "first_name": "Ali",
                        "last_name": "Öğrenci",
                        "role": "student"
                    },
                    "face_photo_url": "/static/faces/123.jpg",
                    "created_at": "2024-04-30T10:00:00Z"
                }
                ```
            *   400:
                *   Email veya öğrenci numarası zaten kullanılıyor.
                *   Geçersiz dosya formatı.
                *   Yüz bulunamadı.
            *   500: Öğrenci oluşturulamadı veya fotoğraf yüklenemedi.

    *   **GET /api/students** - Tüm öğrencileri listele
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   500: Öğrenciler listelenemedi.

    *   **GET /api/students/{student_id}** - Öğrenci detayını getir
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `student_id` (integer, gerekli): Öğrenci ID
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   404: Öğrenci bulunamadı.

    *   **PUT /api/students/{student_id}** - Öğrenci bilgilerini güncelle
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `student_id` (integer, gerekli): Öğrenci ID
        *   **İstek:**
            ```json
            {
                "email": "yeni_ogrenci@example.com",
                "first_name": "Yeni Ali",
                "last_name": "Yeni Öğrenci",
                "department": "Elektrik Elektronik Mühendisliği"
            }
            ```
        *   **Yanıtlar:**
            *   200: Öğrenci başarıyla güncellendi.
            *   404: Öğrenci bulunamadı.
            *   500: Öğrenci güncellenemedi.

    *   **POST /api/students/forgot-password** - Öğrenci şifre hatırlatma
        *   **İstek:**
            ```json
            {
                "email": "ornek@example.com"
            }
            ```
        *   **Yanıtlar:**
            *   200: Şifre hatırlatma başarılı.
            *   400: Geçersiz istek.
            *   404: Öğrenci bulunamadı.
            *   500: Sunucu hatası.

### 4. Dersler (Courses)

*   **Amaç:** Derslerin yönetimi için kullanılır.

    *   📚 **Dersler** tag'i ile işaretlenmiştir.

*   **Endpointler:**

    *   **GET /api/courses** - Tüm dersleri listele
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu işlem için yetkiniz yok.
            *   500: Dersler listelenemedi.
    *   **POST /api/courses** - Yeni ders oluştur
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **İstek:**
            ```json
            {
                "code": "CSE101",
                "name": "Bilgisayar Mühendisliğine Giriş",
                "semester": "2023-BAHAR",
                "teacher_id": 1,
                "lesson_times": [
                    {
                        "lesson_number": 1,
                        "start_time": "09:00",
                        "end_time": "09:50"
                    },
                    {
                        "lesson_number": 2,
                        "start_time": "13:00",
                        "end_time": "13:50"
                    }
                ]
            }
            ```
        *   **Yanıtlar:**
            *   201: Ders başarıyla oluşturuldu.
            *   400: Geçersiz istek veya ders saati çakışması.
    *   **GET /api/courses/{course_id}** - Belirli bir dersi getir
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Ders ID
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu dersi görüntüleme yetkiniz yok.
            *   404: Ders bulunamadı.
            *   500: Ders getirilemedi.
    *   **PUT /api/courses/{course_id}** - Ders bilgilerini güncelle
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Güncellenecek ders ID
        *   **İstek:**
            ```json
            {
                "code": "CSE101",
                "name": "Bilgisayar Mühendisliğine Giriş",
                "semester": "2023-BAHAR",
                "teacher_id": 1,
                "lesson_times": [
                    {
                        "lesson_number": 1,
                        "day": "MONDAY",
                        "start_time": "09:00",
                        "end_time": "09:50"
                    },
                    {
                        "lesson_number": 2,
                        "day": "WEDNESDAY",
                        "start_time": "13:00",
                        "end_time": "13:50"
                    }
                ]
            }
            ```
        *   **Yanıtlar:**
            *   200: Ders başarıyla güncellendi.
            *   400: Geçersiz istek.
            *   401: Yetkilendirme hatası.
            *   403: Yetki hatası.
            *   404: Kaynak bulunamadı.
            *   500: Sunucu hatası.
    *   **DELETE /api/courses/{course_id}** - Dersi sil
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Ders ID
        *   **Yanıtlar:**
            *   204: Ders başarıyla silindi.
            *   403: Bu işlem için yetkiniz yok.
            *   404: Ders bulunamadı.
            *   500: Ders silinemedi.
    *   **GET /api/courses/{course_id}/students** - Dersin öğrencilerini getir
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Ders ID
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu dersin öğrencilerini görüntüleme yetkiniz yok.
            *   404: Ders bulunamadı.
            *   500: Dersin öğrencileri getirilemedi.
    *   **POST /api/courses/{course_id}/students** - Derse öğrenci ekle
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Ders ID
        *   **İstek:**
            ```json
            {
                "student_ids": [1, 2, 3]
            }
            ```
        *   **Yanıtlar:**
            *   201: Öğrenciler başarıyla eklendi.
            *   400: Geçersiz istek veya öğrenciler zaten ekli.
            *   403: Bu işlem için yetkiniz yok.
            *   404: Ders veya öğrenciler bulunamadı.
            *   500: Öğrenciler eklenemedi.
    *   **DELETE /api/courses/{course_id}/students/{student_id}** - Dersten öğrenci çıkar
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Ders ID
            *   `student_id` (integer, gerekli): Öğrenci ID
        *   **Yanıtlar:**
            *   204: Öğrenci başarıyla çıkarıldı.
            *   403: Bu işlem için yetkiniz yok.
            *   404: Ders, öğrenci bulunamadı veya öğrenci bu derste kayıtlı değil.
            *   500: Öğrenci çıkarılamadı.

### 5. Yoklama (Attendance)

*   **Amaç:** Yoklama işlemlerini yönetmek için kullanılır.

    *   ✅ **Yoklama İşlemleri** tag'i ile işaretlenmiştir.

*   **Endpointler:**

    *   **POST /api/courses/{course_id}/attendance** - Yoklama Al
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Ders ID
        *   **İstek:** `multipart/form-data` formatında `photo` alanı ile fotoğraf
        *   **Yanıtlar:**
            *   201: Yoklama başarıyla alındı.
    *   **GET /api/attendance** - Tüm yoklamaları listele
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `start_date` (date, opsiyonel): Başlangıç tarihi
            *   `end_date` (date, opsiyonel): Bitiş tarihi
            *   `course_id` (integer, opsiyonel): Ders ID
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu işlem için yetkiniz yok.
            *   500: Yoklamalar listelenemedi.
    *   **GET /api/attendance/{attendance_id}** - Yoklama detayını getir
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `attendance_id` (integer, gerekli): Yoklama ID
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu işlem için yetkiniz yok.
            *   404: Yoklama bulunamadı.
            *   500: Yoklama detayı getirilemedi.
    *   **GET /api/attendance/course/{course_id}** - Dersin yoklamalarını getir
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Ders ID
            *   `start_date` (date, opsiyonel): Başlangıç tarihi
            *   `end_date` (date, opsiyonel): Bitiş tarihi
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu işlem için yetkiniz yok.
            *   404: Ders bulunamadı.
            *   500: Dersin yoklamaları getirilemedi.
    *   **POST /api/attendance/{attendance_id}/students/{student_id}** - Öğrenciyi manuel olarak yoklamaya ekle
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `attendance_id` (integer, gerekli): Yoklama ID
            *   `student_id` (integer, gerekli): Öğrenci ID
        *   **İstek:**
            ```json
            {
                "status": "PRESENT",
                "note": "Manuel olarak eklendi"
            }
            ```
        *   **Yanıtlar:**
            *   201: Öğrenci başarıyla eklendi.
            *   400: Geçersiz istek.
            *   403: Bu işlem için yetkiniz yok.
            *   404: Yoklama veya öğrenci bulunamadı.
            *   500: Öğrenci eklenemedi.
    *   **GET /api/attendance/course/{course_id}/student/{student_id}** - Belirli bir derste öğrencinin yoklamalarını getir
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Ders ID
            *   `student_id` (integer, gerekli): Öğrenci ID
            *   `start_date` (date, opsiyonel): Başlangıç tarihi
            *   `end_date` (date, opsiyonel): Bitiş tarihi
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu işlem için yetkiniz yok.
            *   404: Ders veya öğrenci bulunamadı.
            *   500: Yoklama kayıtları getirilemedi.

### 6. Yoklama Raporları (Attendance Reports)

*   **Amaç:** Yoklama ve duygu analizi raporlarını oluşturmak için kullanılır.

    *   📊 **Yoklama Raporları** tag'i ile işaretlenmiştir.

*   **Endpointler:**

    *   **GET /api/reports/attendance/daily** - Günlük yoklama raporu
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `date` (date, opsiyonel): Rapor tarihi (Varsayılan: bugün)
            *   `course_id` (integer, opsiyonel): Ders ID
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu dersin raporlarını görüntüleme yetkiniz yok.
            *   500: Rapor oluşturulurken bir hata oluştu.
    *   **GET /api/reports/emotions/course/{course_id}** - Ders duygu analizi raporu
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `course_id` (integer, gerekli): Ders ID
            *   `start_date` (date, opsiyonel): Başlangıç tarihi
            *   `end_date` (date, opsiyonel): Bitiş tarihi
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu dersin raporlarını görüntüleme yetkiniz yok.
            *   404: Ders bulunamadı.
            *   500: Rapor oluşturulurken bir hata oluştu.
    *   **GET /api/reports/attendance/student/{student_id}** - Öğrenci yoklama raporu
        *   **Gereksinim:** `bearerAuth` (JWT token)
        *   **Parametreler:**
            *   `student_id` (integer, gerekli): Öğrenci ID
            *   `course_id` (integer, opsiyonel): Ders ID
            *   `start_date` (date, opsiyonel): Başlangıç tarihi
            *   `end_date` (date, opsiyonel): Bitiş tarihi
        *   **Yanıtlar:**
            *   200: Başarılı.
            *   403: Bu dersin raporlarını görüntüleme yetkiniz yok.
            *   404: Öğrenci bulunamadı.
            *   500: Rapor oluşturulurken bir hata oluştu.

### 7. Admin

*   **Amaç:** Sistem yöneticisi işlemleri için kullanılır.

    *   ⚙️ **Admin** tag'i ile işaretlenmiştir.

*   **Endpointler:**

    *   **POST /api/admin/reset-database** - Veritabanını sıfırla
        *   **Gereksinim:** `bearerAuth` (JWT token), Admin yetkisi
        *   **Yanıtlar:**
            *   200: Veritabanı başarıyla sıfırlandı.
            *   401: Yetkilendirme hatası.
            *   403: Bu işlem için admin yetkisi gerekli.
            *   500: Veritabanı sıfırlanamadı.

## Erişim Yetkileri

*   **Admin:** Tüm endpointlere erişim yetkisine sahiptir.
*   **Öğretmen:**
    *   Kendi dersleri ile ilgili endpointlere erişebilir.
    *   Öğrenci bilgilerini görüntüleyebilir.
    *   Yoklama alabilir ve yoklama raporlarını görüntüleyebilir.
*   **Öğrenci:**
    *   Kendi yoklama bilgilerini görüntüleyebilir.

## Ek Notlar

*   Tüm `date` formatındaki parametreler `YYYY-MM-DD` formatında olmalıdır.
*   Tüm zaman bilgileri `HH:MM` formatında olmalıdır.
*   Hata durumlarında, API genellikle bir JSON objesi içinde `error` alanıyla birlikte hata mesajı döndürür. 