from datetime import datetime
from app import db

class Teacher(db.Model):
    """Öğretmen modeli"""
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    department = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    courses = db.relationship('Course', backref='teacher', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, user_id, department, title=None):
        self.user_id = user_id
        self.department = department
        self.title = title
    
    def to_dict(self):
        """Öğretmen bilgilerini sözlük olarak döndür"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'department': self.department,
            'title': self.title,
            'user': self.user.to_dict() if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Teacher {self.id}>' 