"""
LOOP Lojistik Platformu - Teslimat Süresi Tahmin Modeli
Machine learning ile teslimat süresi tahmini ve optimizasyonu
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from core.database import get_db
from models.order import Order, OrderStatus
from models.courier import Courier
from services.weather_service import WeatherService
from services.mapbox_service import MapboxService


@dataclass
class DeliveryPrediction:
    """Teslimat tahmin sonucu"""
    predicted_duration_minutes: float
    confidence_interval: Tuple[float, float]
    factors: Dict[str, float]
    recommendations: List[str]


class DeliveryTimePredictor:
    """Teslimat süresi tahmin modeli"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = [
            'distance_km',
            'weather_condition',
            'traffic_level',
            'courier_rating',
            'courier_experience_days',
            'vehicle_type',
            'order_priority',
            'day_of_week',
            'hour_of_day',
            'is_holiday',
            'pickup_area_density',
            'delivery_area_density'
        ]
        self.weather_service = WeatherService()
        self.mapbox_service = MapboxService()
    
    async def train_model(self, historical_data: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """Modeli tarihsel verilerle eğit"""
        try:
            # Eğer veri sağlanmazsa, veritabanından çek
            if historical_data is None:
                historical_data = await self._fetch_training_data()
            
            if len(historical_data) < 100:
                logger.warning("Eğitim verisi yetersiz. Minimum 100 örnek gereklidir.")
                return {}
            
            # Veri ön işleme
            processed_data = await self._preprocess_data(historical_data)
            
            # Özellikleri ve hedef değişkeni ayır
            X = processed_data[self.feature_columns]
            y = processed_data['actual_duration_minutes']
            
            # Eğitim ve test setlerini oluştur
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=processed_data['vehicle_type']
            )
            
            # Modeli oluştur ve eğit
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=8,
                random_state=42
            )
            
            self.model.fit(X_train, y_train)
            
            # Model performansını değerlendir
            y_pred = self.model.predict(X_test)
            
            metrics = {
                'mae': mean_absolute_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2_score': r2_score(y_test, y_pred),
                'mape': np.mean(np.abs((y_test - y_pred) / y_test)) * 100
            }
            
            logger.info(f"Model eğitimi tamamlandı. Performans metrikleri: {metrics}")
            
            # Modeli kaydet
            await self._save_model()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Model eğitimi hatası: {e}")
            return {}
    
    async def predict_delivery_time(
        self,
        order_data: Dict,
        courier_data: Dict,
        weather_data: Optional[Dict] = None
    ) -> DeliveryPrediction:
        """Teslimat süresi tahmini yap"""
        try:
            if self.model is None:
                await self._load_model()
            
            # Özellik vektörünü oluştur
            features = await self._create_feature_vector(order_data, courier_data, weather_data)
            
            # Tahmin yap
            prediction = self.model.predict([features])[0]
            
            # Güven aralığını hesapla
            confidence_interval = self._calculate_confidence_interval(features)
            
            # Etki faktörlerini analiz et
            factors = await self._analyze_factors(features)
            
            # Öneriler oluştur
            recommendations = await self._generate_recommendations(features, prediction)
            
            return DeliveryPrediction(
                predicted_duration_minutes=prediction,
                confidence_interval=confidence_interval,
                factors=factors,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Teslimat süresi tahmin hatası: {e}")
            # Fallback: Basit hesaplama
            distance = order_data.get('distance_km', 5)
            base_time = distance * 3  # 3 dakika/km
            return DeliveryPrediction(
                predicted_duration_minutes=base_time,
                confidence_interval=(base_time * 0.8, base_time * 1.2),
                factors={'distance': 0.8},
                recommendations=['Gerçek zamanlı trafik verisi kullanın']
            )
    
    async def _fetch_training_data(self) -> pd.DataFrame:
        """Veritabanından eğitim verisini çek"""
        try:
            db = next(get_db())
            
            # Tamamlanmış siparişleri çek
            query = """
            SELECT 
                o.id, o.distance_km, o.actual_duration_minutes,
                o.priority, o.created_at,
                c.rating as courier_rating, c.total_deliveries,
                c.vehicle_type, c.created_at as courier_created_at,
                ST_Y(o.pickup_location) as pickup_lat,
                ST_X(o.pickup_location) as pickup_lng,
                ST_Y(o.delivery_location) as delivery_lat,
                ST_X(o.delivery_location) as delivery_lng
            FROM orders o
            JOIN couriers c ON o.assigned_courier_id = c.id
            WHERE o.status = 'delivered' 
            AND o.actual_duration_minutes IS NOT NULL
            AND o.created_at > NOW() - INTERVAL '6 months'
            """
            
            result = await db.execute(query)
            data = result.fetchall()
            
            # DataFrame'e dönüştür
            df = pd.DataFrame(data, columns=result.keys())
            
            # Ek özellikler ekle
            df['courier_experience_days'] = (df['created_at'] - df['courier_created_at']).dt.days
            df['day_of_week'] = df['created_at'].dt.dayofweek
            df['hour_of_day'] = df['created_at'].dt.hour
            
            # Hava durumu ve trafik verilerini ekle (mock)
            df['weather_condition'] = np.random.choice(['clear', 'rain', 'snow'], len(df))
            df['traffic_level'] = np.random.randint(1, 6, len(df))
            df['is_holiday'] = np.random.choice([0, 1], len(df), p=[0.9, 0.1])
            
            return df
            
        except Exception as e:
            logger.error(f"Eğitim verisi çekme hatası: {e}")
            return pd.DataFrame()
    
    async def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Veri ön işleme"""
        try:
            # Eksik değerleri doldur
            df['courier_rating'].fillna(df['courier_rating'].mean(), inplace=True)
            df['distance_km'].fillna(df['distance_km'].median(), inplace=True)
            
 # Kategorik değişkenleri encode et
            categorical_columns = ['priority', 'vehicle_type', 'weather_condition']
            for col in categorical_columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col] = self.label_encoders[col].fit_transform(df[col])
                else:
                    df[col] = self.label_encoders[col].transform(df[col])
            
            # Aykırı değerleri temizle
            Q1 = df['actual_duration_minutes'].quantile(0.25)
            Q3 = df['actual_duration_minutes'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            df = df[(df['actual_duration_minutes'] >= lower_bound) & 
                   (df['actual_duration_minutes'] <= upper_bound)]
            
            return df
            
        except Exception as e:
            logger.error(f"Veri ön işleme hatası: {e}")
            return df
    
    async def _create_feature_vector(self, order_data: Dict, courier_data: Dict, weather_data: Optional[Dict]) -> List[float]:
        """Özellik vektörü oluştur"""
        features = []
        
        # Temel özellikler
        features.append(order_data.get('distance_km', 5.0))
        features.append(self._encode_weather(weather_data))
        features.append(order_data.get('traffic_level', 3))
        features.append(courier_data.get('rating', 4.5))
        features.append(courier_data.get('experience_days', 365))
        features.append(self._encode_vehicle_type(courier_data.get('vehicle_type', 'motorcycle')))
        features.append(self._encode_priority(order_data.get('priority', 'normal')))
        
        # Zaman bazlı özellikler
        now = datetime.now()
        features.append(now.weekday())  # day_of_week
        features.append(now.hour)       # hour_of_day
        features.append(self._is_holiday(now))  # is_holiday
        
        # Alan yoğunlukları (mock)
        features.append(5.0)  # pickup_area_density
        features.append(4.0)  # delivery_area_density
        
        return features
    
    def _encode_weather(self, weather_data: Optional[Dict]) -> int:
        """Hava durumunu encode et"""
        if not weather_data:
            return 0  # clear
        
        condition = weather_data.get('main', 'Clear').lower()
        if 'rain' in condition:
            return 1
        elif 'snow' in condition:
            return 2
        elif 'cloud' in condition:
            return 3
        else:
            return 0
    
    def _encode_vehicle_type(self, vehicle_type: str) -> int:
        """Araç tipini encode et"""
        mapping = {'motorcycle': 0, 'car': 1, 'van': 2, 'bicycle': 3}
        return mapping.get(vehicle_type, 0)
    
    def _encode_priority(self, priority: str) -> int:
        """Önceliği encode et"""
        mapping = {'low': 0, 'normal': 1, 'high': 2, 'urgent': 3}
        return mapping.get(priority, 1)
    
    def _is_holiday(self, date: datetime) -> int:
        """Tatil günü kontrolü"""
        # Basit kontrol - hafta sonu
        if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return 1
        
        # Türkiye resmi tatilleri (basit liste)
        holidays = [
            (1, 1),   # Yılbaşı
            (4, 23),  # Ulusal Egemenlik
            (5, 1),   # Emek ve Dayanışma
            (5, 19),  # Atatürk'ü Anma
            (7, 15),  # Demokrasi ve Milli Birlik
            (8, 30),  # Zafer Bayramı
            (10, 29), # Cumhuriyet Bayramı
        ]
        
        return 1 if (date.month, date.day) in holidays else 0
    
    def _calculate_confidence_interval(self, features: List[float]) -> Tuple[float, float]:
        """Güven aralığını hesapla"""
        prediction = self.model.predict([features])[0]
        
        # Modelin tahmin varyansını kullan (eğer varsa)
        if hasattr(self.model, 'predict'):
            # Basit yaklaşım: %20 güven aralığı
            margin = prediction * 0.2
            return (prediction - margin, prediction + margin)
        
        return (prediction * 0.8, prediction * 1.2)
    
    async def _analyze_factors(self, features: List[float]) -> Dict[str, float]:
        """Etki faktörlerini analiz et"""
        factors = {}
        
        # Özellik önemlerini hesapla (feature importance)
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            for i, importance in enumerate(importances):
                if i < len(self.feature_columns):
                    factors[self.feature_columns[i]] = importance
        
        return factors
    
    async def _generate_recommendations(self, features: List[float], prediction: float) -> List[str]:
        """Öneriler oluştur"""
        recommendations = []
        
        # Hava durumu önerileri
        if features[1] > 0:  # Kötü hava durumu
            recommendations.append("Hava koşulları nedeniyle ek süre planlayın")
        
        # Trafik önerileri
        if features[2] > 3:  # Yoğun trafik
            recommendations.append("Alternatif rotaları değerlendirin")
        
        # Kurye performansı önerileri
        if features[3] < 4.0:  # Düşük kurye rating
            recommendations.append("Kurye eğitimi veya değişimi düşünün")
        
        # Mesafe önerileri
        if features[0] > 10:  # Uzun mesafe
            recommendations.append("Araç tipini optimize edin")
        
        # Tatil günü önerileri
        if features[11] == 1:  # Tatil günü
            recommendations.append("Tatil günü trafiğini göz önünde bulundurun")
        
        if not recommendations:
            recommendations.append("Mevcut plan optimal görünüyor")
        
        return recommendations
    
    async def _save_model(self):
        """Modeli diske kaydet"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'label_encoders': self.label_encoders,
                'feature_columns': self.feature_columns
            }
            
            joblib.dump(model_data, 'models/delivery_time_predictor.pkl')
            logger.info("Model başarıyla kaydedildi")
            
        except Exception as e:
            logger.error(f"Model kaydetme hatası: {e}")
    
    async def _load_model(self):
        """Modeli diskten yükle"""
        try:
            if os.path.exists('models/delivery_time_predictor.pkl'):
                model_data = joblib.load('models/delivery_time_predictor.pkl')
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.label_encoders = model_data['label_encoders']
                self.feature_columns = model_data['feature_columns']
                logger.info("Model başarıyla yüklendi")
            else:
                logger.warning("Kayıtlı model bulunamadı, yeni model eğitilecek")
                await self.train_model()
                
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            await self.train_model()


# Global model instance
delivery_predictor = DeliveryTimePredictor()