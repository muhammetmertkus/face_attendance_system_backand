from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.utils.helpers import admin_required
import os
import shutil
import sqlite3
import datetime
import tempfile
from alembic.config import Config
from alembic import command

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/reset-database', methods=['POST'])
@jwt_required()
@admin_required
def reset_database():
    """Veritabanını sıfırla"""
    try:
        # Tüm tabloları temizle
        db.drop_all()
        db.create_all()
        
        # Yüz fotoğraflarını temizle
        upload_folder = current_app.config['UPLOAD_FOLDER']
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path) and filename != '.gitkeep':
                os.unlink(file_path)
        
        return jsonify(message="Veritabanı başarıyla sıfırlandı."), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/seed-database', methods=['POST'])
@jwt_required()
@admin_required
def seed_database():
    """Veritabanına örnek veriler ekle"""
    try:
        from app.models.user import User
        from app.models.teacher import Teacher
        from app.models.student import Student
        from app.models.course import Course, LessonTime, CourseStudent
        
        # Admin kullanıcısı oluştur
        admin = User(
            email="admin@example.com",
            password="admin123",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        db.session.add(admin)
        
        # Öğretmen kullanıcıları oluştur
        teacher1 = User(
            email="teacher1@example.com",
            password="teacher123",
            first_name="Ahmet",
            last_name="Yılmaz",
            role="teacher"
        )
        db.session.add(teacher1)
        db.session.flush()
        
        teacher1_profile = Teacher(
            user_id=teacher1.id,
            department="Bilgisayar Mühendisliği",
            title="Dr. Öğr. Üyesi"
        )
        db.session.add(teacher1_profile)
        
        teacher2 = User(
            email="teacher2@example.com",
            password="teacher123",
            first_name="Ayşe",
            last_name="Demir",
            role="teacher"
        )
        db.session.add(teacher2)
        db.session.flush()
        
        teacher2_profile = Teacher(
            user_id=teacher2.id,
            department="Elektrik Elektronik Mühendisliği",
            title="Prof. Dr."
        )
        db.session.add(teacher2_profile)
        
        # Öğrenci kullanıcıları oluştur
        student1 = User(
            email="student1@example.com",
            password="student123",
            first_name="Mehmet",
            last_name="Kaya",
            role="student"
        )
        db.session.add(student1)
        db.session.flush()
        
        student1_profile = Student(
            user_id=student1.id,
            student_number="20240001",
            department="Bilgisayar Mühendisliği"
        )
        db.session.add(student1_profile)
        
        student2 = User(
            email="student2@example.com",
            password="student123",
            first_name="Zeynep",
            last_name="Şahin",
            role="student"
        )
        db.session.add(student2)
        db.session.flush()
        
        student2_profile = Student(
            user_id=student2.id,
            student_number="20240002",
            department="Bilgisayar Mühendisliği"
        )
        db.session.add(student2_profile)
        
        student3 = User(
            email="student3@example.com",
            password="student123",
            first_name="Ali",
            last_name="Öztürk",
            role="student"
        )
        db.session.add(student3)
        db.session.flush()
        
        student3_profile = Student(
            user_id=student3.id,
            student_number="20240003",
            department="Elektrik Elektronik Mühendisliği"
        )
        db.session.add(student3_profile)
        
        # Dersleri oluştur
        course1 = Course(
            code="CSE101",
            name="Bilgisayar Mühendisliğine Giriş",
            semester="2023-BAHAR",
            teacher_id=teacher1_profile.id
        )
        db.session.add(course1)
        db.session.flush()
        
        # Ders saatlerini ekle
        lesson_time1 = LessonTime(
            course_id=course1.id,
            lesson_number=1,
            day="MONDAY",
            start_time="09:00",
            end_time="09:50"
        )
        db.session.add(lesson_time1)
        
        lesson_time2 = LessonTime(
            course_id=course1.id,
            lesson_number=2,
            day="WEDNESDAY",
            start_time="13:00",
            end_time="13:50"
        )
        db.session.add(lesson_time2)
        
        course2 = Course(
            code="EEE201",
            name="Elektrik Devre Temelleri",
            semester="2023-BAHAR",
            teacher_id=teacher2_profile.id
        )
        db.session.add(course2)
        db.session.flush()
        
        # Ders saatlerini ekle
        lesson_time3 = LessonTime(
            course_id=course2.id,
            lesson_number=1,
            day="TUESDAY",
            start_time="10:00",
            end_time="10:50"
        )
        db.session.add(lesson_time3)
        
        lesson_time4 = LessonTime(
            course_id=course2.id,
            lesson_number=2,
            day="THURSDAY",
            start_time="14:00",
            end_time="14:50"
        )
        db.session.add(lesson_time4)
        
        # Öğrencileri derslere ekle
        course_student1 = CourseStudent(
            course_id=course1.id,
            student_id=student1_profile.id
        )
        db.session.add(course_student1)
        
        course_student2 = CourseStudent(
            course_id=course1.id,
            student_id=student2_profile.id
        )
        db.session.add(course_student2)
        
        course_student3 = CourseStudent(
            course_id=course2.id,
            student_id=student2_profile.id
        )
        db.session.add(course_student3)
        
        course_student4 = CourseStudent(
            course_id=course2.id,
            student_id=student3_profile.id
        )
        db.session.add(course_student4)
        
        # Değişiklikleri kaydet
        db.session.commit()
        
        return jsonify(message="Örnek veriler başarıyla eklendi."), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/backup-database', methods=['POST'])
@jwt_required()
@admin_required
def backup_database():
    """Veritabanını yedekle"""
    try:
        # Veritabanı dosya yolunu al
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        if not db_uri.startswith('sqlite:///'):
            return jsonify(error="Bu işlem sadece SQLite veritabanları için desteklenmektedir."), 400
        
        db_path = db_uri.replace('sqlite:///', '')
        
        # Yedekleme klasörünü oluştur
        backup_dir = os.path.join(current_app.root_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Yedek dosya adını oluştur
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Veritabanını yedekle
        shutil.copy2(db_path, backup_path)
        
        # Yüz fotoğraflarını yedekle
        faces_dir = current_app.config['UPLOAD_FOLDER']
        faces_backup_dir = os.path.join(backup_dir, f"faces_{timestamp}")
        os.makedirs(faces_backup_dir, exist_ok=True)
        
        for filename in os.listdir(faces_dir):
            file_path = os.path.join(faces_dir, filename)
            if os.path.isfile(file_path):
                shutil.copy2(file_path, os.path.join(faces_backup_dir, filename))
        
        return jsonify(message="Veritabanı başarıyla yedeklendi.", backup_file=backup_filename), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/restore-database', methods=['POST'])
@jwt_required()
@admin_required
def restore_database():
    """Veritabanını geri yükle"""
    try:
        data = request.get_json()
        
        if 'backup_file' not in data:
            return jsonify(error="Yedek dosya adı gerekli."), 400
        
        backup_filename = data['backup_file']
        
        # Yedekleme klasörünü kontrol et
        backup_dir = os.path.join(current_app.root_path, 'backups')
        backup_path = os.path.join(backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            return jsonify(error="Belirtilen yedek dosyası bulunamadı."), 404
        
        # Veritabanı dosya yolunu al
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        if not db_uri.startswith('sqlite:///'):
            return jsonify(error="Bu işlem sadece SQLite veritabanları için desteklenmektedir."), 400
        
        db_path = db_uri.replace('sqlite:///', '')
        
        # Veritabanı bağlantısını kapat
        db.session.close()
        db.engine.dispose()
        
        # Veritabanını geri yükle
        shutil.copy2(backup_path, db_path)
        
        # Yüz fotoğraflarını geri yükle
        timestamp = backup_filename.replace('backup_', '').replace('.db', '')
        faces_backup_dir = os.path.join(backup_dir, f"faces_{timestamp}")
        
        if os.path.exists(faces_backup_dir):
            faces_dir = current_app.config['UPLOAD_FOLDER']
            
            # Mevcut fotoğrafları temizle
            for filename in os.listdir(faces_dir):
                file_path = os.path.join(faces_dir, filename)
                if os.path.isfile(file_path) and filename != '.gitkeep':
                    os.unlink(file_path)
            
            # Yedek fotoğrafları geri yükle
            for filename in os.listdir(faces_backup_dir):
                file_path = os.path.join(faces_backup_dir, filename)
                if os.path.isfile(file_path):
                    shutil.copy2(file_path, os.path.join(faces_dir, filename))
        
        return jsonify(message="Veritabanı başarıyla geri yüklendi."), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/backups', methods=['GET'])
@jwt_required()
@admin_required
def list_backups():
    """Mevcut yedekleri listele"""
    try:
        # Yedekleme klasörünü kontrol et
        backup_dir = os.path.join(current_app.root_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Yedek dosyalarını listele
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('backup_') and filename.endswith('.db'):
                file_path = os.path.join(backup_dir, filename)
                if os.path.isfile(file_path):
                    # Dosya bilgilerini al
                    stat = os.stat(file_path)
                    timestamp = filename.replace('backup_', '').replace('.db', '')
                    
                    # Tarih formatını düzenle
                    try:
                        date = datetime.datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                        formatted_date = date.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_date = timestamp
                    
                    backups.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created_at': formatted_date
                    })
        
        # Tarihe göre sırala (en yeni en üstte)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify(backups=backups), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/download-backup/<filename>', methods=['GET'])
@jwt_required()
@admin_required
def download_backup(filename):
    """Yedek dosyasını indir"""
    try:
        # Yedekleme klasörünü kontrol et
        backup_dir = os.path.join(current_app.root_path, 'backups')
        backup_path = os.path.join(backup_dir, filename)
        
        if not os.path.exists(backup_path):
            return jsonify(error="Belirtilen yedek dosyası bulunamadı."), 404
        
        return send_file(backup_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify(error=str(e)), 500

def upgrade_database():
    """Veritabanını en son sürüme yükseltir."""
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        return True, None
    except Exception as e:
        return False, str(e)

@bp.route('/upgrade-db', methods=['POST'])
@jwt_required()
def upgrade_db():
    """Veritabanını yükseltme endpoint'i."""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'error': 'Bu işlem için admin yetkisi gerekli.'}), 403

    success, error = upgrade_database()

    if success:
        return jsonify({'message': 'Veritabanı başarıyla güncellendi.'}), 200
    else:
        return jsonify({'error': f'Veritabanı güncellenemedi: {error}'}), 500 