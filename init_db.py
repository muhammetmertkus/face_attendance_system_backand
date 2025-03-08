import os
import sys
from flask_migrate import Migrate
from app import create_app, db
from app.models.user import User

# Flask uygulamasını oluştur
app = create_app()

# Migrasyon nesnesi oluştur
migrate = Migrate(app, db)

def init_db():
    """Veritabanını başlat ve migrasyon yap"""
    with app.app_context():
        # Veritabanı klasörünü kontrol et
        if not os.path.exists('migrations'):
            print("Veritabanı başlatılıyor...")
            os.system('flask db init')
        
        # Migrasyon yap
        print("Migrasyon yapılıyor...")
        os.system('flask db migrate -m "Initial migration"')
        
        # Migrasyon uygula
        print("Migrasyon uygulanıyor...")
        os.system('flask db upgrade')
        
        # Admin kullanıcısı var mı kontrol et
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            print("Admin kullanıcısı oluşturuluyor...")
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
        
        print("Veritabanı başarıyla başlatıldı.")

if __name__ == '__main__':
    init_db() 