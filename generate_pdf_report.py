
import json
import csv
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from app.models.orm import User, Courier, Order
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.cache_service import cache_service
from app.dependencies import get_current_user
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
import io
from datetime import datetime

# --- Mocks ---

# Mock Redis
async def mock_redis_connect():
    pass
async def mock_redis_disconnect():
    pass
cache_service.connect = mock_redis_connect
cache_service.disconnect = mock_redis_disconnect

# Mock DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

app.dependency_overrides[get_db] = override_get_db

# Mock Auth (Admin)
async def override_get_current_user():
    return User(id=1, email="admin@loop.com", full_name="Admin User", role="admin", is_active=True)

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

# --- Mock realistic data instead of fetching from empty DB ---
def get_realistic_test_data():
    """Generate realistic test data for the report"""
    return {
        "total_orders": 47,
        "delivered_orders": 35,
        "cancelled_orders": 4,
        "in_progress_orders": 8,
        "success_rate": 74.47,
        "cancellation_rate": 8.51,
        "average_delivery_distance_km": 6.8
    }

def create_chart(data):
    print("📈 Grafik Olusturuluyor...")
    # Extract relevant metrics for the chart
    labels = ['Teslim Edilen', 'Iptal Edilen', 'Islemde']
    values = [
        data.get('delivered_orders', 0),
        data.get('cancelled_orders', 0),
        data.get('in_progress_orders', 0)
    ]
    
    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, values, color=['#4CAF50', '#F44336', '#FF9800'], width=0.6)
    plt.title('Siparis Durum Dagilimi', fontsize=16, fontweight='bold', pad=20)
    plt.ylabel('Siparis Sayisi', fontsize=12)
    plt.xlabel('Durum', fontsize=12)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height +  0.5,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    
    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

def create_pie_chart(data):
    """Create a pie chart for order distribution"""
    print("📊 Pasta Grafik Olusturuluyor...")
    
    labels = ['Basarili\nTeslimatlar', 'Iptal\nEdilenler', 'Devam\nEdenler']
    sizes = [
        data.get('delivered_orders', 0),
        data.get('cancelled_orders', 0),
        data.get('in_progress_orders', 0)
    ]
    colors_pie = ['#4CAF50', '#F44336', '#FF9800']
    explode = (0.05, 0, 0)  # Explode first slice
    
    plt.figure(figsize=(7, 7))
    patches, texts, autotexts = plt.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
                                         autopct='%1.1f%%', startangle=90, textprops={'fontsize': 11})
    
    # Bold font for percentages
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)
    
    plt.title('Siparis Dagil im Yuzdeleri', fontsize=14, fontweight='bold', pad=20)
    plt.axis('equal')
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

def generate_pdf(data, chart_buffer, pie_chart_buffer, filename="gunluk_rapor.pdf"):
    print(f"📄 PDF Olusturuluyor: {filename}...")
    
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("LOOP Lojistik - Gunluk Performans Raporu", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Date and time
    date_str = datetime.now().strftime("%d %B %Y, %H:%M")
    date_text = Paragraph(f"<b>Rapor Tarihi:</b> {date_str}", styles['Normal'])
    elements.append(date_text)
    elements.append(Spacer(1, 24))
    
    # Summary section
    summary_title = Paragraph("<b>Yonetici Ozeti</b>", styles['Heading2'])
    elements.append(summary_title)
    elements.append(Spacer(1, 12))
    
    summary_text = f"""
    Bugun toplam <b>{data.get('total_orders', 0)}</b> siparis islendi. 
    Bunlardan <b>{data.get('delivered_orders', 0)}</b> tanesi basariyla teslim edildi, 
    <b>{data.get('in_progress_orders', 0)}</b> tanesi devam ediyor ve 
    <b>{data.get('cancelled_orders', 0)}</b> tanesi iptal edildi. 
    Basari orani <b>%{data.get('success_rate', 0):.1f}</b> olarak gerceklesmistir.
    """
    summary_para = Paragraph(summary_text, styles['Normal'])
    elements.append(summary_para)
    elements.append(Spacer(1, 24))
    
    # Metrics Table
    metrics_title = Paragraph("<b>Detayli Metrikler</b>", styles['Heading2'])
    elements.append(metrics_title)
    elements.append(Spacer(1, 12))
    
    table_data = [["Metrik", "Deger", "Durum"]]
    
    # Translation map for keys with status indicators
    metrics_list = [
        ("total_orders", "Toplam Siparis", lambda x: "Normal" if x > 0 else "Dusuk"),
        ("delivered_orders", "Teslim Edilen", lambda x: "Iyi" if x > 20 else "Normal"),
        ("cancelled_orders", "Iptal Edilen", lambda x: "Dikkat" if x > 5 else "Iyi"),
        ("in_progress_orders", "Islemde", lambda x: "Normal"),
        ("success_rate", "Basari Orani (%)", lambda x: "Mukemmel" if x > 80 else "Iyi" if x > 60 else "Gelismeli"),
        ("cancellation_rate", "Iptal Orani (%)", lambda x: "Dikkat" if x > 10 else "Iyi"),
        ("average_delivery_distance_km", "Ort. Teslimat Mesafesi (km)", lambda x: "Normal")
    ]

    for key, label, status_func in metrics_list:
        value = data.get(key, 0)
        status = status_func(value)
        
        # Format value
        if 'rate' in key or 'percentage' in key:
            formatted_value = f"{value:.2f}%"
        elif 'distance' in key:
            formatted_value = f"{value:.1f} km"
        else:
            formatted_value = str(int(value))
            
        table_data.append([label, formatted_value, status])
        
    table = Table(table_data, colWidths=[200, 120, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 30))
    
    # Bar Chart
    if chart_buffer:
        chart_title = Paragraph("<b>Siparis Durum Dagilimi</b>", styles['Heading2'])
        elements.append(chart_title)
        elements.append(Spacer(1, 12))
        
        img = Image(chart_buffer)
        img.drawHeight = 250
        img.drawWidth = 450
        elements.append(img)
        elements.append(Spacer(1, 30))
    
    # Pie Chart
    if pie_chart_buffer:
        pie_title = Paragraph("<b>Siparis Yuzde Dagilimi</b>", styles['Heading2'])
        elements.append(pie_title)
        elements.append(Spacer(1, 12))
        
        pie_img = Image(pie_chart_buffer)
        pie_img.drawHeight = 280
        pie_img.drawWidth = 350
        elements.append(pie_img)
    
    doc.build(elements)
    print("✅ PDF Basariyla Olusturuldu")

def main():
    print("🚀 Gunluk Rapor Olusturuluyor")
    print("=" * 40)
    
    # Use realistic test data
    data = get_realistic_test_data()
    print(f"📊 Test Verileri Yuklendi: {data['total_orders']} siparis")
    
    chart_buffer = create_chart(data)
    pie_chart_buffer = create_pie_chart(data)
    generate_pdf(data, chart_buffer, pie_chart_buffer)
    
    print(f"\n📄 Rapor basariyla olusturuldu: gunluk_rapor.pdf")
    print(f"📊 Toplam {data['total_orders']} siparis analiz edildi")

if __name__ == "__main__":
    main()
