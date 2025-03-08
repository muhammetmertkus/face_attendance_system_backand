## Eksik Backend Özellikleri ve API Endpointleri

Aşağıdaki tabloda, mevcut backend servisindeki eksik özellikler ve API endpointleri listelenmiştir. Bu liste, sağlanan kod dosyaları (`app/routes`, `app/models`) ve `backend.md` dosyasındaki genel proje tanımı ve API endpointleri karşılaştırılarak oluşturulmuştur.

**Not:** Bu analiz, `backend.md` dosyasının eksiksiz ve doğru bir şekilde tüm API endpointlerini ve özellikleri tanımladığı varsayımına dayanmaktadır.

### 1. Kimlik Doğrulama (Authentication)

*   **Şifre Sıfırlama:**
    *   Öğretmenler ve öğrenciler için şifre sıfırlama özelliği eksik. Mevcut durumda sadece şifre hatırlatma özelliği bulunmaktadır.
    *   **Endpoint:**
        *   POST /api/auth/reset-password (Şifre sıfırlama isteği gönderme)
        *   PUT /api/auth/reset-password/{token} (Şifreyi sıfırlama)

### 2. Kullanıcı Yönetimi (User Management)

*   **Öğrenci Yönetimi:**
    *   Öğrenci oluşturma, güncelleme ve silme işlemleri için admin/öğretmen yetkisi kontrolü eksik.
    *   **Endpointler:**
        *   POST /api/admin/students (Yeni öğrenci oluşturma - Admin/Öğretmen)
        *   PUT /api/admin/students/{student_id} (Öğrenci güncelleme - Admin/Öğretmen)
        *   DELETE /api/admin/students/{student_id} (Öğrenci silme - Admin/Öğretmen)
*   **Öğretmen Yönetimi:**
    *   Öğretmen oluşturma, güncelleme ve silme işlemleri için admin yetkisi kontrolü eksik.
    *   **Endpointler:**
        *   POST /api/admin/teachers (Yeni öğretmen oluşturma - Admin/Öğretmen)
        *   PUT /api/admin/teachers/{teacher_id} (Öğretmen güncelleme - Admin/Öğretmen)
*   **Kullanıcı Listeleme:**
    *   Sistemdeki tüm kullanıcıları listeleme özelliği eksik.
    *   **Endpoint:**
        *   GET /api/admin/users (Tüm kullanıcıları listeleme - Admin/Öğretmen)

### 3. Yoklama (Attendance)

*   **Yoklama Güncelleme/Silme:**
    *   Alınan bir yoklamayı güncelleme veya silme özelliği eksik.
        *   DELETE /api/attendance/{attendance_id} (Yoklama silme - Admin/Öğretmen)
*   **Yoklama Detaylarını Görüntüleme İyileştirmeleri:**
    *   Yoklama detaylarını getirirken (GET /api/attendance/{attendance_id}), öğrenci isimleri gibi ek bilgiler de döndürülmeli.

### 4. Raporlama (Reporting)

*   **Duygu Analizi Raporları:**
    *   Duygu analizi sonuçlarını görselleştirmek için grafikler veya tablolar oluşturma özelliği eksik.
*   **Öğrenci Devamsızlık Raporu:**
    *   Öğrencinin belirli bir dönemdeki devamsızlık yüzdesini gösteren bir rapor eksik.
    *   **Endpoint:**
        *   GET /api/reports/attendance/student/{student_id}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD (Öğrenci devamsızlık raporu)
*   **Ders Bazlı Devamsızlık Raporu:**
    *   Bir dersteki genel devamsızlık oranını gösteren bir rapor eksik.
    *   **Endpoint:**
        *   GET /api/reports/attendance/course/{course_id}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD (Ders bazlı devamsızlık raporu)

### 5. Diğer Eksik Fonksiyonlar

*   **Veritabanı Yedekleme/Geri Yükleme:**
    *   Veritabanını yedekleme ve geri yükleme özelliği eksik.
    *   **Endpointler:**
        *   POST /api/admin/backup-database (Veritabanı yedekleme - Admin)
        *   POST /api/admin/restore-database (Veritabanı geri yükleme - Admin)
*   **Loglama:**
    *   Sistemdeki hataları ve önemli olayları loglama özelliği eksik.

Bu liste, projenin geliştirme sürecinde dikkate alınması gereken potansiyel eksiklikleri ve iyileştirme alanlarını göstermektedir. 