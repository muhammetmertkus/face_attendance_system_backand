from datetime import datetime
from app import db

class Student(db.Model):
    """Öğrenci modeli"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    face_encoding = db.Column(db.Text, nullable=True)  # Yüz tanıma için kodlanmış veri
    face_photo_url = db.Column(db.String(255), nullable=True)  # Yüz fotoğrafı URL'si
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    courses = db.relationship('CourseStudent', backref='student', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, user_id, student_number, department, face_encoding=None, face_photo_url=None):
        self.user_id = user_id
        self.student_number = student_number
        self.department = department
        self.face_encoding = face_encoding
        self.face_photo_url = face_photo_url
    
    def to_dict(self):
        """Öğrenci bilgilerini sözlük olarak döndür"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'student_number': self.student_number,
            'department': self.department,
            'face_photo_url': self.face_photo_url,
            'user': self.user.to_dict() if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Student {self.student_number}>' 