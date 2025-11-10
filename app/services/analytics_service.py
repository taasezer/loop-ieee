"""
LOOP Lojistik Platformu - Analytics ve Business Intelligence Servisi
Gelişmiş raporlama, veri analizi ve görselleştirme
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
import json
from collections import defaultdict

from core.database import get_db
from core.cache import cache_manager, cache_result
from models.order import Order, OrderStatus
from models.courier import Courier, CourierStatus
from ml_models.delivery_time_predictor import delivery_predictor


class ReportType(Enum):
    """Rapor tipleri"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ChartType(Enum):
    """Grafik tipleri"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"


@dataclass
class KPI:
    """KPI (Key Performance Indicator)"""
    name: str
    value: float
    target: float
    unit: str
    trend: float  # Yüzde değişim
    status: str  # good, warning, critical
    description: str


@dataclass
class ChartData:
    """Grafik verisi"""
    chart_type: ChartType
    title: str
    subtitle: str
    x_axis_label: str
    y_axis_label: str
    data: List[Dict[str, Any]]
    colors: List[str] = None
    options: Dict[str, Any] = None


@dataclass
class Report:
    """Rapor"""
    id: str
    title: str
    description: str
    report_type: ReportType
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    kpis: List[KPI]
    charts: List[ChartData]
    insights: List[str]
    recommendations: List[str]


class AnalyticsService:
    """Analytics ve BI servisi"""
    
    def __init__(self):
        self.db = None
        self.kpi_targets = {
            'delivery_success_rate': 98.0,
            'average_delivery_time': 45.0,
            'courier_utilization': 85.0,
            'customer_satisfaction': 4.5,
            'operational_efficiency': 90.0,
            'cost_per_delivery': 25.0
        }
    
    async def initialize(self):
        """Servisi başlat"""
        self.db = next(get_db())
        logger.info("Analytics servisi başlatıldı")
    
    @cache_result(cache_type='analytics', ttl=1800)
    async def generate_dashboard_kpis(self, period_days: int = 30) -> List[KPI]:
        """Dashboard KPI'larını oluştur"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            kpis = []
            
            # 1. Teslimat Başarı Oranı
            success_rate = await self._calculate_delivery_success_rate(start_date, end_date)
            kpis.append(KPI(
                name="Teslimat Başarı Oranı",
                value=success_rate,
                target=self.kpi_targets['delivery_success_rate'],
                unit="%",
                trend=await self._calculate_trend('delivery_success_rate', period_days),
                status=self._get_kpi_status(success_rate, self.kpi_targets['delivery_success_rate'], higher_is_better=True),
                description="Başarıyla tamamlanan teslimatların oranı"
            ))
            
            # 2. Ortalama Teslimat Süresi
            avg_delivery_time = await self._calculate_average_delivery_time(start_date, end_date)
            kpis.append(KPI(
                name="Ortalama Teslimat Süresi",
                value=avg_delivery_time,
                target=self.kpi_targets['average_delivery_time'],
                unit="dk",
                trend=await self._calculate_trend('average_delivery_time', period_days),
                status=self._get_kpi_status(avg_delivery_time, self.kpi_targets['average_delivery_time'], higher_is_better=False),
                description="Siparişten teslimata ortalama süre"
            ))
            
            # 3. Kurye Kullanım Oranı
            courier_utilization = await self._calculate_courier_utilization(start_date, end_date)
            kpis.append(KPI(
                name="Kurye Kullanım Oranı",
                value=courier_utilization,
                target=self.kpi_targets['courier_utilization'],
                unit="%",
                trend=await self._calculate_trend('courier_utilization', period_days),
                status=self._get_kpi_status(courier_utilization, self.kpi_targets['courier_utilization'], higher_is_better=True),
                description="Aktif kuryelerin kullanım oranı"
            ))
            
            # 4. Müşteri Memnuniyeti
            customer_satisfaction = await self._calculate_customer_satisfaction(start_date, end_date)
            kpis.append(KPI(
                name="Müşteri Memnuniyeti",
                value=customer_satisfaction,
                target=self.kpi_targets['customer_satisfaction'],
                unit="/5",
                trend=await self._calculate_trend('customer_satisfaction', period_days),
                status=self._get_kpi_status(customer_satisfaction, self.kpi_targets['customer_satisfaction'], higher_is_better=True),
                description="Müşteri memnuniyet ortalaması"
            ))
            
            # 5. Operasyonel Verimlilik
            operational_efficiency = await self._calculate_operational_efficiency(start_date, end_date)
            kpis.append(KPI(
                name="Operasyonel Verimlilik",
                value=operational_efficiency,
                target=self.kpi_targets['operational_efficiency'],
                unit="%",
                trend=await self._calculate_trend('operational_efficiency', period_days),
                status=self._get_kpi_status(operational_efficiency, self.kpi_targets['operational_efficiency'], higher_is_better=True),
                description="Operasyonel süreçlerin verimlilik oranı"
            ))
            
            # 6. Teslimat Başına Maliyet
            cost_per_delivery = await self._calculate_cost_per_delivery(start_date, end_date)
            kpis.append(KPI(
                name="Teslimat Başına Maliyet",
                value=cost_per_delivery,
                target=self.kpi_targets['cost_per_delivery'],
                unit="TL",
                trend=await self._calculate_trend('cost_per_delivery', period_days),
                status=self._get_kpi_status(cost_per_delivery, self.kpi_targets['cost_per_delivery'], higher_is_better=False),
                description="Her teslimat için ortalama maliyet"
            ))
            
            return kpis
            
        except Exception as e:
            logger.error(f"KPI oluşturma hatası: {e}")
            return []
    
    @cache_result(cache_type='analytics', ttl=3600)
    async def generate_performance_report(self, report_type: ReportType, period_days: int = 30) -> Report:
        """Performans raporu oluştur"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # KPI'lar
            kpis = await self.generate_dashboard_kpis(period_days)
            
            # Grafikler
            charts = await self._generate_performance_charts(start_date, end_date)
            
            # İçgörüler
            insights = await self._generate_insights(kpis, charts)
            
            # Öneriler
            recommendations = await self._generate_recommendations(kpis, insights)
            
            report = Report(
                id=f"performance_{datetime.now().timestamp()}",
                title=f"Performans Raporu - {report_type.value.title()}",
                description=f"Son {period_days} günün performans analizi",
                report_type=report_type,
                generated_at=datetime.utcnow(),
                period_start=start_date,
                period_end=end_date,
                kpis=kpis,
                charts=charts,
                insights=insights,
                recommendations=recommendations
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Performans raporu oluşturma hatası: {e}")
            return None
    
    async def _generate_performance_charts(self, start_date: datetime, end_date: datetime) -> List[ChartData]:
        """Performans grafiklerini oluştur"""
        charts = []
        
        # 1. Günlük Teslimat Hacmi
        daily_deliveries = await self._get_daily_delivery_volume(start_date, end_date)
        charts.append(ChartData(
            chart_type=ChartType.LINE,
            title="Günlük Teslimat Hacmi",
            subtitle="Günlük teslimat sayıları",
            x_axis_label="Tarih",
            y_axis_label="Teslimat Sayısı",
            data=daily_deliveries,
            colors=["#3B82F6", "#10B981"]
        ))
        
        # 2. Kurye Performansı
        courier_performance = await self._get_courier_performance_data(start_date, end_date)
        charts.append(ChartData(
            chart_type=ChartType.BAR,
            title="Kurye Performansı",
            subtitle="Kurye başına ortalama teslimat süresi",
            x_axis_label="Kurye",
            y_axis_label="Ortalama Süre (dk)",
            data=courier_performance,
            colors=["#F59E0B", "#EF4444"]
        ))
        
        # 3. Bölgesel Dağılım
        regional_distribution = await self._get_regional_distribution(start_date, end_date)
        charts.append(ChartData(
            chart_type=ChartType.PIE,
            title="Bölgesel Dağılım",
            subtitle="Teslimatların bölgesel dağılımı",
            x_axis_label="",
            y_axis_label="",
            data=regional_distribution,
            colors=["#8B5CF6", "#EC4899", "#06B6D4", "#84CC16"]
        ))
        
        # 4. Zaman Çizelgesi
        timeline_data = await self._get_timeline_data(start_date, end_date)
        charts.append(ChartData(
            chart_type=ChartType.SCATTER,
            title="Teslimat Zaman Çizelgesi",
            subtitle="Sipariş oluşturma vs teslimat süresi",
            x_axis_label="Sipariş Oluşturma Saati",
            y_axis_label="Teslimat Süresi (dk)",
            data=timeline_data,
            colors=["#F97316", "#DC2626"]
        ))
        
        return charts
    
    async def _generate_insights(self, kpis: List[KPI], charts: List[ChartData]) -> List[str]:
        """İçgörüleri oluştur"""
        insights = []
        
        # KPI'lara göre içgörüler
        for kpi in kpis:
            if kpi.status == 'critical':
                insights.append(f"{kpi.name} kritik seviyede. Hedef: {kpi.target}{kpi.unit}, Mevcut: {kpi.value}{kpi.unit}")
            elif kpi.status == 'warning':
                insights.append(f"{kpi.name} düşük performans gösteriyor. İyileştirme gerekiyor.")
            elif kpi.trend > 10:
                insights.append(f"{kpi.name} olumlu yönde gelişiyor. %{kpi.trend:.1f} artış.")
            elif kpi.trend < -10:
                insights.append(f"{kpi.name} olumsuz yönde gelişiyor. %{abs(kpi.trend):.1f} düşüş.")
        
        # Grafik verilerine göre içgörüler
        for chart in charts:
            if chart.title == "Günlük Teslimat Hacmi":
                peak_days = self._identify_peak_days(chart.data)
                if peak_days:
                    insights.append(f"En yoğun günler: {', '.join(peak_days)}")
            
            elif chart.title == "Kurye Performansı":
                top_performers = self._identify_top_performers(chart.data)
                if top_performers:
                    insights.append(f"En iyi performans gösteren kuryeler: {', '.join(top_performers)}")
        
        # ML tahminleri
        predictions = await self._get_ml_predictions()
        if predictions:
            insights.extend(predictions)
        
        return insights
    
    async def _generate_recommendations(self, kpis: List[KPI], insights: List[str]) -> List[str]:
        """Öneriler oluştur"""
        recommendations = []
        
        # KPI'lara göre öneriler
        for kpi in kpis:
            if kpi.name == "Teslimat Başarı Oranı" and kpi.status == 'critical':
                recommendations.append("Kurye eğitim programları düzenlenmeli")
                recommendations.append("GPS takip sistemleri güncellenmeli")
                
            elif kpi.name == "Ortalama Teslimat Süresi" and kpi.status == 'warning':
                recommendations.append("Rota optimizasyon algoritmaları gözden geçirilmeli")
                recommendations.append("Trafik verisi entegrasyonu geliştirilmeli")
                
            elif kpi.name == "Kurye Kullanım Oranı" and kpi.value < 70:
                recommendations.append("Kurye dağıtım algoritması optimize edilmeli")
                recommendations.append("Yeni kurye alımı planlanmalı")
        
        # İçgörülere göre öneriler
        for insight in insights:
            if "yoğun günler" in insight:
                recommendations.append("Yoğun günler için ek kurye planlaması yapılmalı")
            elif "en iyi performans" in insight:
                recommendations.append("Başarılı kuryelerin yöntemleri diğerlerine öğretilmeli")
        
        return recommendations
    
    # Hesaplama metodları
    async def _calculate_delivery_success_rate(self, start_date: datetime, end_date: datetime) -> float:
        """Teslimat başarı oranını hesapla"""
        try:
            total_deliveries = await self._get_total_deliveries(start_date, end_date)
            successful_deliveries = await self._get_successful_deliveries(start_date, end_date)
            
            return (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
            
        except Exception as e:
            logger.error(f"Teslimat başarı oranı hesaplama hatası: {e}")
            return 0.0
    
    async def _calculate_average_delivery_time(self, start_date: datetime, end_date: datetime) -> float:
        """Ortalama teslimat süresini hesapla"""
        try:
            # Veritabanından veri çek (mock)
            return 42.5  # dakika
            
        except Exception as e:
            logger.error(f"Ortalama teslimat süresi hesaplama hatası: {e}")
            return 0.0
    
    async def _calculate_courier_utilization(self, start_date: datetime, end_date: datetime) -> float:
        """Kurye kullanım oranını hesapla"""
        try:
            # Aktif kurye sayısı
            active_couriers = len([
                courier for courier in await self._get_all_couriers()
                if courier.status == CourierStatus.AVAILABLE
            ])
            
            # Toplam kurye sayısı
            total_couriers = len(await self._get_all_couriers())
            
            return (active_couriers / total_couriers * 100) if total_couriers > 0 else 0
            
        except Exception as e:
            logger.error(f"Kurye kullanım oranı hesaplama hatası: {e}")
            return 0.0
    
    async def _calculate_customer_satisfaction(self, start_date: datetime, end_date: datetime) -> float:
        """Müşteri memnuniyetini hesapla"""
        try:
            # Mock hesaplama
            return 4.2
            
        except Exception as e:
            logger.error(f"Müşteri memnuniyeti hesaplama hatası: {e}")
            return 0.0
    
    async def _calculate_operational_efficiency(self, start_date: datetime, end_date: datetime) -> float:
        """Operasyonel verimliliği hesapla"""
        try:
            # Mock hesaplama
            return 87.3
            
        except Exception as e:
            logger.error(f"Operasyonel verimlilik hesaplama hatası: {e}")
            return 0.0
    
    async def _calculate_cost_per_delivery(self, start_date: datetime, end_date: datetime) -> float:
        """Teslimat başına maliyeti hesapla"""
        try:
            # Mock hesaplama
            return 23.5
            
        except Exception as e:
            logger.error(f"Teslimat başına maliyet hesaplama hatası: {e}")
            return 0.0
    
    async def _calculate_trend(self, metric_name: str, period_days: int) -> float:
        """Trendi hesapla"""
        try:
            # Basit trend hesaplama (mock)
            return np.random.uniform(-20, 20)
            
        except Exception as e:
            logger.error(f"Trend hesaplama hatası: {e}")
            return 0.0
    
    def _get_kpi_status(self, current: float, target: float, higher_is_better: bool = True) -> str:
        """KPI durumunu belirle"""
        if higher_is_better:
            if current >= target:
                return "good"
            elif current >= target * 0.8:
                return "warning"
            else:
                return "critical"
        else:
            if current <= target:
                return "good"
            elif current <= target * 1.2:
                return "warning"
            else:
                return "critical"
    
    # Veri çekme metodları (mock implementasyonlar)
    async def _get_total_deliveries(self, start_date: datetime, end_date: datetime) -> int:
        """Toplam teslimat sayısı"""
        return 1500
    
    async def _get_successful_deliveries(self, start_date: datetime, end_date: datetime) -> int:
        """Başarılı teslimat sayısı"""
        return 1425
    
    async def _get_all_couriers(self) -> List[Courier]:
        """Tüm kuryeleri al"""
        return []
    
    async def _get_daily_delivery_volume(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Günlük teslimat hacmi"""
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'deliveries': np.random.randint(40, 80)
            })
            current_date += timedelta(days=1)
        
        return data
    
    async def _get_courier_performance_data(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Kurye performans verisi"""
        return [
            {'courier': 'Kurye 1', 'avg_time': 38.5},
            {'courier': 'Kurye 2', 'avg_time': 42.1},
            {'courier': 'Kurye 3', 'avg_time': 35.8}
        ]
    
    async def _get_regional_distribution(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Bölgesel dağılım"""
        return [
            {'region': 'Beşiktaş', 'count': 350},
            {'region': 'Kadıköy', 'count': 280},
            {'region': 'Şişli', 'count': 220},
            {'region': 'Üsküdar', 'count': 180}
        ]
    
    async def _get_timeline_data(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Zaman çizelgesi verisi"""
        data = []
        for hour in range(24):
            data.append({
                'hour': hour,
                'delivery_time': np.random.uniform(30, 60)
            })
        return data
    
    def _identify_peak_days(self, data: List[Dict]) -> List[str]:
        """En yoğun günleri belirle"""
        if not data:
            return []
        
        max_deliveries = max(item['deliveries'] for item in data)
        peak_days = [item['date'] for item in data if item['deliveries'] >= max_deliveries * 0.8]
        return peak_days
    
    def _identify_top_performers(self, data: List[Dict]) -> List[str]:
        """En iyi performans gösterenleri belirle"""
        if not data:
            return []
        
        min_time = min(item['avg_time'] for item in data)
        top_performers = [item['courier'] for item in data if item['avg_time'] <= min_time * 1.1]
        return top_performers
    
    async def _get_ml_predictions(self) -> List[str]:
        """ML tahminlerini al"""
        try:
            # Mock ML tahminleri
            predictions = [
                "Gelecek hafta teslimat sayısında %15 artış bekleniyor",
                "Hava durumu kötüleşirse teslimat süreleri %20 uzayabilir",
                "Yeni kurye alımı gerekebilir"
            ]
            return predictions
            
        except Exception as e:
            logger.error(f"ML tahminleri alma hatası: {e}")
            return []


# Global analytics service instance
analytics_service = AnalyticsService()


# Rapor şablonları
REPORT_TEMPLATES = {
    "executive_summary": {
        "title": "Yönetici Özeti",
        "description": "Üst düzey performans özet raporu",
        "kpis": ["delivery_success_rate", "customer_satisfaction", "operational_efficiency"],
        "charts": ["daily_volume", "regional_distribution"],
        "frequency": "weekly"
    },
    "operational_report": {
        "title": "Operasyonel Rapor",
        "description": "Detaylı operasyonel performans analizi",
        "kpis": ["delivery_success_rate", "average_delivery_time", "courier_utilization", "cost_per_delivery"],
        "charts": ["daily_volume", "courier_performance", "timeline_analysis"],
        "frequency": "daily"
    },
    "financial_report": {
        "title": "Finansal Rapor",
        "description": "Gelir-gider ve maliyet analizi",
        "kpis": ["cost_per_delivery", "revenue_per_delivery", "profit_margin"],
        "charts": ["revenue_trend", "cost_breakdown"],
        "frequency": "monthly"
    },
    "customer_report": {
        "title": "Müşteri Raporu",
        "description": "Müşteri memnuniyeti ve geri bildirim analizi",
        "kpis": ["customer_satisfaction", "delivery_success_rate", "repeat_customer_rate"],
        "charts": ["satisfaction_trend", "customer_segments"],
        "frequency": "monthly"
    }
}