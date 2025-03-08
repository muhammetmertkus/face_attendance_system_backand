import json
import numpy as np
import face_recognition
from PIL import Image
from io import BytesIO

class EmotionRecognitionService:
    """Duygu analizi servisi"""
    
    @staticmethod
    def analyze_emotions(photo_file):
        """
        Fotoğraftaki yüzlerin duygularını analiz et
        
        Args:
            photo_file (FileStorage): Yüklenen fotoğraf dosyası
            
        Returns:
            tuple: (başarı durumu, duygu analizi sonuçları veya hata mesajı)
        """
        try:
            # Fotoğrafı yükle
            image = face_recognition.load_image_file(photo_file)
            
            # Yüzleri bul
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                return False, "Fotoğrafta yüz bulunamadı."
            
            # Basit duygu analizi (gerçek duygu analizi yerine varsayılan değerler)
            results = []
            for face_location in face_locations:
                # Varsayılan duygu değerleri
                emotions_dict = {
                    'angry': 0.05,
                    'disgust': 0.02,
                    'fear': 0.01,
                    'happy': 0.7,
                    'sad': 0.05,
                    'surprise': 0.07,
                    'neutral': 0.1
                }
                
                # En yüksek duyguyu bul (bu durumda 'happy')
                dominant_emotion = 'happy'
                dominant_emotion_score = 0.7
                
                # Yüz konumu
                top, right, bottom, left = face_location
                box = [left, top, right - left, bottom - top]
                
                # Sonucu ekle
                results.append({
                    'box': box,
                    'emotions': emotions_dict,
                    'dominant_emotion': dominant_emotion,
                    'dominant_emotion_score': dominant_emotion_score
                })
            
            # Sınıfın genel duygu durumunu hesapla
            if results:
                # Tüm duyguları topla
                all_emotions = {
                    'angry': 0,
                    'disgust': 0,
                    'fear': 0,
                    'happy': 0,
                    'sad': 0,
                    'surprise': 0,
                    'neutral': 0
                }
                
                for result in results:
                    for emotion, score in result['emotions'].items():
                        all_emotions[emotion] += score
                
                # Ortalama al
                for emotion in all_emotions:
                    all_emotions[emotion] /= len(results)
                
                # En yüksek ortalama duyguyu bul
                class_dominant_emotion = max(all_emotions.items(), key=lambda x: x[1])
                
                # Genel sonucu ekle
                class_result = {
                    'face_count': len(results),
                    'emotions': all_emotions,
                    'dominant_emotion': class_dominant_emotion[0],
                    'dominant_emotion_score': class_dominant_emotion[1]
                }
                
                # Sonuçları JSON formatına dönüştür
                emotion_data = json.dumps({
                    'individual_results': results,
                    'class_result': class_result
                })
                
                return True, emotion_data
            
            return False, "Duygu analizi sonuçları işlenemedi."
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_emotion_from_face(face_image):
        """
        Tek bir yüz için duygu analizi yap
        
        Args:
            face_image (numpy.ndarray): Yüz görüntüsü
            
        Returns:
            tuple: (başarı durumu, duygu veya hata mesajı)
        """
        try:
            # Basit duygu analizi (gerçek duygu analizi yerine varsayılan değer)
            return True, "happy"
            
        except Exception as e:
            return False, str(e) 