from app import create_app, db
from app.models.user import User
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.course import Course, LessonTime, CourseStudent
from app.models.attendance import Attendance

def create_tables():
    """Veritabanı tablolarını oluştur"""
    app = create_app()
    with app.app_context():
        # Veritabanı tablolarını oluştur
        db.create_all()
        
        # Admin kullanıcısı oluştur (eğer yoksa)
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin kullanıcısı oluşturuldu.")
        else:
            print("Admin kullanıcısı zaten var.")
        
        print("Veritabanı tabloları başarıyla oluşturuldu.")

if __name__ == '__main__':
    create_tables() 