from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from app import db
from app.models.user import User
from app.models.teacher import Teacher
from app.models.student import Student

class AuthService:
    """Kimlik doğrulama servisi"""
    
    @staticmethod
    def register_user(email, password, first_name, last_name, role, department=None, branch=None, title=None, student_number=None):
        """
        Yeni kullanıcı kaydı
        
        Args:
            email (str): E-posta adresi
            password (str): Şifre
            first_name (str): Ad
            last_name (str): Soyad
            role (str): Rol ('admin', 'teacher', 'student')
            department (str): Bölüm
            branch (str): Şube
            title (str): Ünvan
            student_number (str): Öğrenci numarası
            
        Returns:
            tuple: (başarı durumu, kullanıcı veya hata mesajı)
        """
        try:
            # E-posta adresi kontrolü
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return False, "Bu e-posta adresi zaten kullanılıyor."
            
            # Kullanıcı oluştur
            user = User(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            
            db.session.add(user)
            db.session.flush()  # ID ataması için flush
            
            # Rol bazlı işlemler
            if role == 'teacher' and department:
                teacher = Teacher(
                    user_id=user.id,
                    department=department,
                    branch=branch,
                    title=title
                )
                db.session.add(teacher)
                user.teacher = teacher
            
            elif role == 'student':
                face_encoding = kwargs.get('face_encoding')
                face_photo_url = kwargs.get('face_photo_url')
                
                # Öğrenci numarası kontrolü
                existing_student = Student.query.filter_by(student_number=student_number).first()
                if existing_student:
                    db.session.rollback()
                    return False, "Bu öğrenci numarası zaten kullanılıyor."
                
                student = Student(
                    user_id=user.id,
                    student_number=student_number,
                    department=department,
                    face_encoding=face_encoding,
                    face_photo_url=face_photo_url
                )
                db.session.add(student)
            
            # Değişiklikleri kaydet
            db.session.commit()
            
            return True, user
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def login(email, password):
        """
        Kullanıcı girişi
        
        Args:
            email (str): E-posta adresi
            password (str): Şifre
            
        Returns:
            tuple: (başarı durumu, token bilgileri veya hata mesajı)
        """
        try:
            # Kullanıcıyı bul
            user = User.query.filter_by(email=email).first()
            
            # Kullanıcı yoksa veya şifre yanlışsa
            if not user or not user.check_password(password):
                return False, "Geçersiz e-posta adresi veya şifre."
            
            # Token oluştur
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
            return True, {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'user': user.to_dict()
            }
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def refresh_token(user_id):
        """
        Access token yenileme
        
        Args:
            user_id (int): Kullanıcı ID
            
        Returns:
            tuple: (başarı durumu, yeni token veya hata mesajı)
        """
        try:
            # Kullanıcıyı kontrol et
            user = User.query.get(user_id)
            if not user:
                return False, "Kullanıcı bulunamadı."
            
            # Yeni access token oluştur
            access_token = create_access_token(identity=user.id)
            
            return True, {
                'access_token': access_token
            }
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        ID'ye göre kullanıcı getir
        
        Args:
            user_id (int): Kullanıcı ID
            
        Returns:
            tuple: (başarı durumu, kullanıcı veya hata mesajı)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "Kullanıcı bulunamadı."
            
            return True, user
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def update_user(user_id, **kwargs):
        """
        Kullanıcı bilgilerini güncelle
        
        Args:
            user_id (int): Kullanıcı ID
            **kwargs: Güncellenecek alanlar
            
        Returns:
            tuple: (başarı durumu, kullanıcı veya hata mesajı)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "Kullanıcı bulunamadı."
            
            # Şifre güncelleme
            if 'password' in kwargs and kwargs['password']:
                user.set_password(kwargs['password'])
            
            # Diğer alanları güncelle
            for key, value in kwargs.items():
                if key != 'password' and hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            
            # Rol için ek işlemler
            if user.role == 'teacher' and user.teacher:
                for key, value in kwargs.items():
                    if hasattr(user.teacher, key) and value is not None:
                        setattr(user.teacher, key, value)
            
            elif user.role == 'student' and user.student:
                for key, value in kwargs.items():
                    if hasattr(user.student, key) and value is not None:
                        setattr(user.student, key, value)
            
            # Değişiklikleri kaydet
            db.session.commit()
            
            return True, user
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def forgot_password(email):
        """
        Şifre hatırlatma
        
        Args:
            email (str): E-posta adresi
            
        Returns:
            tuple: (başarı durumu, mesaj)
        """
        try:
            # Kullanıcıyı bul
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return False, "Bu e-posta adresiyle kayıtlı kullanıcı bulunamadı."
            
            # Gerçek uygulamada burada şifre sıfırlama e-postası gönderilir
            # Bu örnekte sadece başarılı olduğunu varsayıyoruz
            
            return True, "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi."
            
        except Exception as e:
            return False, str(e) 