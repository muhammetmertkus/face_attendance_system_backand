import requests
import json
import os
from datetime import datetime

# Swagger dosyasını yükle
with open('app/static/swagger.json', 'r', encoding='utf-8') as f:
    swagger = json.load(f)

# API ana dizini
BASE_URL = 'http://localhost:5000'

# Test sonuçlarını saklamak için sözlük
test_results = {
    'admin': [],
    'teacher': [],
    'student': []
}

# Hata raporunu saklamak için liste
error_report = []

# Test sırasında oluşturulan ID'leri saklamak için sözlük
created_ids = {
    'teacher_id': 1,  # Varsayılan değer
    'student_id': 1,  # Varsayılan değer
    'course_id': 1    # Varsayılan değer
}

# Zaman damgası oluştur
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Rapor dosyasının adını oluştur
report_filename = f"test_report_{timestamp}.txt"

# Test fonksiyonu
def test_endpoint(method, path, role, security=None, data=None, files=None):
    # Path parametrelerini gerçek değerlerle değiştir
    actual_path = path
    if '{teacher_id}' in path:
        actual_path = path.replace('{teacher_id}', str(created_ids['teacher_id']))
    if '{student_id}' in path:
        actual_path = actual_path.replace('{student_id}', str(created_ids['student_id']))
    if '{course_id}' in path:
        actual_path = actual_path.replace('{course_id}', str(created_ids['course_id']))
    if '{attendance_id}' in path:
        actual_path = actual_path.replace('{attendance_id}', '1')  # Varsayılan değer
    if '{token}' in path:
        actual_path = actual_path.replace('{token}', 'test_token')  # Varsayılan değer
    if '{filename}' in path:
        actual_path = actual_path.replace('{filename}', 'test_backup.db')  # Varsayılan değer

    url = BASE_URL + actual_path
    headers = {}

    # Yetkilendirme başlığını ekle
    if security:
        # Token'ı al
        if role == 'admin':
            token = admin_token
        elif role == 'teacher':
            token = teacher_token
        elif role == 'student':
            token = student_token
        else:
            token = None

        if token:
            # Bearer önekini ekleyerek doğru formatta gönder
            headers['Authorization'] = f'Bearer {token}'

    try:
        print(f"\nTesting {method} {url} as {role}")
        print(f"Headers: {headers}")
        print(f"Data: {data}")

        if method == 'get':
            response = requests.get(url, headers=headers, params=data)
        elif method == 'post':
            if files:
                response = requests.post(url, headers=headers, files=files, data=data)
            else:
                response = requests.post(url, headers=headers, json=data)
        elif method == 'put':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'delete':
            response = requests.delete(url, headers=headers)

        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response Body: {response.json()}")
            response_body = response.json()
            
            # ID'leri kaydet
            if method == 'post' and response.status_code == 201:
                if 'teacher' in path and 'teacher' in response_body:
                    created_ids['teacher_id'] = response_body['teacher']['id']
                    print(f"Saved teacher_id: {created_ids['teacher_id']}")
                elif 'student' in path and 'student' in response_body:
                    created_ids['student_id'] = response_body['student']['id']
                    print(f"Saved student_id: {created_ids['student_id']}")
                elif 'course' in path and 'course' in response_body:
                    created_ids['course_id'] = response_body['course']['id']
                    print(f"Saved course_id: {created_ids['course_id']}")
                
        except json.JSONDecodeError:
            print(f"Response Body: {response.text}")
            response_body = response.text

        # Test sonucunu kaydet
        test_results[role].append({
            'method': method,
            'path': path,
            'status_code': response.status_code,
            'response_body': response_body
        })

        # Hata durumunda rapor oluştur
        if response.status_code >= 400:
            error_report.append({
                'role': role,
                'method': method,
                'path': path,
                'status_code': response.status_code,
                'response_body': response_body
            })

    except Exception as e:
        print(f"Error: {e}")
        error_report.append({
            'role': role,
            'method': method,
            'path': path,
            'error': str(e)
        })

# Kullanıcı kayıt ve oturum açma işlemleri
def register_and_login(role):
    # Kayıt bilgileri
    register_data = {
        'email': f'{role}@example.com',
        'password': f'{role}123',
        'first_name': f'{role.capitalize()}',
        'last_name': 'User',
        'role': role
    }
    if role == 'student':
        register_data['student_number'] = '20240001'
        register_data['department'] = 'Bilgisayar Mühendisliği'
    elif role == 'teacher':
        register_data['department'] = 'Bilgisayar Mühendisliği'
        register_data['title'] = 'Dr. Öğr. Üyesi'

    # Kayıt ol
    register_url = BASE_URL + '/api/auth/register'
    register_response = requests.post(register_url, json=register_data)

    if register_response.status_code == 201:
        print(f"\n{role.capitalize()} registered successfully")
    elif register_response.status_code == 400 and 'Bu e-posta adresi zaten kullanılıyor.' in register_response.text:
        print(f"\n{role.capitalize()} already registered")
    else:
        print(f"\n{role.capitalize()} registration failed: {register_response.text}")
        return None

    # Oturum açma bilgileri
    login_data = {
        'email': f'{role}@example.com',
        'password': f'{role}123'
    }

    # Oturum aç
    login_url = BASE_URL + '/api/auth/login'
    login_response = requests.post(login_url, json=login_data)

    if login_response.status_code == 200:
        print(f"{role.capitalize()} logged in successfully")
        try:
            return login_response.json()['access_token']
        except (KeyError, json.JSONDecodeError):
            print(f"Token could not be extracted from response: {login_response.text}")
            # Test için sahte bir token döndür
            return "test_token_for_" + role
    else:
        print(f"{role.capitalize()} login failed: {login_response.text}")
        # Test için sahte bir token döndür
        return "test_token_for_" + role

# Kullanıcıları kaydet ve token'ları al
print("Registering and logging in users...")
admin_token = register_and_login('admin')
teacher_token = register_and_login('teacher')
student_token = register_and_login('student')

# Test yüz fotoğrafı oluştur (eğer yoksa)
test_face_dir = os.path.join(os.getcwd(), 'app', 'static', 'faces')
test_face_path = os.path.join(test_face_dir, 'test_face.jpg')

if not os.path.exists(test_face_dir):
    os.makedirs(test_face_dir)

if not os.path.exists(test_face_path):
    # Basit bir test yüz fotoğrafı oluştur
    try:
        import numpy as np
        from PIL import Image
        
        # 100x100 boyutunda gri bir görüntü oluştur
        img_array = np.ones((100, 100, 3), dtype=np.uint8) * 128
        img = Image.fromarray(img_array)
        img.save(test_face_path)
        print(f"Test face image created at {test_face_path}")
    except ImportError:
        print("PIL or numpy not installed. Cannot create test face image.")

# Admin testleri
if admin_token:
    print("\n=== Running Admin Tests ===")
    for path, methods in swagger['paths'].items():
        for method, details in methods.items():
            if '⚙️ Admin' in details.get('tags', []):
                security = details.get('security')
                parameters = details.get('parameters', [])
                data = {}
                files = {}

                # Parametreleri işle
                for param in parameters:
                    if param['in'] == 'body':
                        if 'schema' in param and 'properties' in param['schema']:
                            data = {k: v.get('example') for k, v in param['schema']['properties'].items()}
                    elif param['in'] == 'formData' and param.get('type') == 'file':
                        # Dosya yükleme örneği
                        try:
                            # Mevcut dosya adını al
                            file_name = param['name']
                            # Dosya yolu oluştur
                            file_path = test_face_path
                            # Dosyanın var olup olmadığını kontrol et
                            if os.path.exists(file_path):
                                # Dosyayı aç ve files sözlüğüne ekle
                                files[param['name']] = open(file_path, 'rb')
                            else:
                                print(f"Dosya bulunamadı: {file_path}")
                        except FileNotFoundError:
                            print(f"Dosya bulunamadı: {file_path}")
                    elif param['in'] == 'formData':
                        data[param['name']] = param.get('example')

                test_endpoint(method, path, 'admin', security, data, files)

                # Dosyaları kapat
                for file in files.values():
                    file.close()

# Öğretmen testleri
if teacher_token:
    print("\n=== Running Teacher Tests ===")
    for path, methods in swagger['paths'].items():
        for method, details in methods.items():
            if '👨‍🏫 Öğretmenler' in details.get('tags', []) or '📚 Dersler' in details.get('tags', []) or '✅ Yoklama İşlemleri' in details.get('tags', []) or '📊 Yoklama Raporları' in details.get('tags', []):
                security = details.get('security')
                parameters = details.get('parameters', [])
                data = {}
                files = {}

                # Parametreleri işle
                for param in parameters:
                    if param['in'] == 'body':
                        if 'schema' in param and 'properties' in param['schema']:
                            data = {k: v.get('example') for k, v in param['schema']['properties'].items()}
                    elif param['in'] == 'formData' and param.get('type') == 'file':
                        # Dosya yükleme örneği
                        try:
                            file_path = test_face_path
                            if os.path.exists(file_path):
                                files[param['name']] = open(file_path, 'rb')
                            else:
                                print(f"Dosya bulunamadı: {file_path}")
                        except FileNotFoundError:
                            print(f"Dosya bulunamadı: {file_path}")
                    elif param['in'] == 'formData':
                        data[param['name']] = param.get('example')
                    elif param['in'] == 'query':
                        if not data:
                            data = {}
                        data[param['name']] = param.get('default', param.get('example'))

                test_endpoint(method, path, 'teacher', security, data, files)

                # Dosyaları kapat
                for file in files.values():
                    file.close()

# Öğrenci testleri
if student_token:
    print("\n=== Running Student Tests ===")
    for path, methods in swagger['paths'].items():
        for method, details in methods.items():
            if '👨‍🎓 Öğrenciler' in details.get('tags', []):
                security = details.get('security')
                parameters = details.get('parameters', [])
                data = {}
                files = {}

                # Parametreleri işle
                for param in parameters:
                    if param['in'] == 'body':
                        if 'schema' in param and 'properties' in param['schema']:
                            data = {k: v.get('example') for k, v in param['schema']['properties'].items()}
                    elif param['in'] == 'formData' and param.get('type') == 'file':
                        # Dosya yükleme örneği
                        try:
                            file_path = test_face_path
                            if os.path.exists(file_path):
                                files[param['name']] = open(file_path, 'rb')
                            else:
                                print(f"Dosya bulunamadı: {file_path}")
                        except FileNotFoundError:
                            print(f"Dosya bulunamadı: {file_path}")
                    elif param['in'] == 'formData':
                        data[param['name']] = param.get('example')
                    elif param['in'] == 'query':
                        if not data:
                            data = {}
                        data[param['name']] = param.get('default', param.get('example'))

                test_endpoint(method, path, 'student', security, data, files)

                # Dosyaları kapat
                for file in files.values():
                    file.close()

# Hata raporunu dosyaya yaz
with open(report_filename, 'w', encoding='utf-8') as f:
    if error_report:
        f.write("Hata Raporu:\n")
        for error in error_report:
            f.write(f"Rol: {error['role']}\n")
            f.write(f"Metot: {error['method']}\n")
            f.write(f"Path: {error['path']}\n")
            if 'status_code' in error:
                f.write(f"Status Kodu: {error['status_code']}\n")
            if 'response_body' in error:
                f.write(f"Response Body: {error['response_body']}\n")
            if 'error' in error:
                f.write(f"Hata: {error['error']}\n")
            f.write("-" * 30 + "\n")
    else:
        f.write("Hata bulunamadı.\n")

print(f"\nHata raporu {report_filename} dosyasına kaydedildi.") 