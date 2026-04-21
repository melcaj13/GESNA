import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob
import random

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Kriz Kalkanı | Hibrit Risk Analizi", page_icon="🛡️", layout="wide")

# --- ÖRNEK VERİ ÜRETİCİ (Dummy Data) ---
@st.cache_data
def load_dummy_data():
    np.random.seed(42)
    # NLP analizinin net çalışması için örnekler İngilizce ağırlıklı tutulmuştur
    sample_comments = [
        "Terrible service, absolutely disgusting experience!", 
        "The food was bad and the waiter was very rude.", 
        "Amazing place, highly recommended!", 
        "I will never come back here again, awful.", 
        "It was okay, nothing special.",
        "Worst restaurant in Philadelphia, totally ruined my night.",
        "Loved the atmosphere, great food.",
        "Overpriced and terrible quality.",
        "Very disappointing.",
        "Best meal I've ever had!"
    ]
    
    data = []
    for i in range(1, 101):
        data.append({
            "Kullanıcı_ID": f"User_{i:03d}",
            "Yorum_Metni": random.choice(sample_comments),
            "Arkadaş_Sayısı": np.random.randint(0, 5000)
        })
    return pd.DataFrame(data)

# --- ANALİZ FONKSİYONLARI ---
def analyze_data(df):
    # 1. NLP Analizi: Polarity hesapla
    df['Polarity'] = df['Yorum_Metni'].apply(lambda x: TextBlob(str(x)).sentiment.polarity)
    
    # Sadece negatif yorumları filtrele (Kriz tespiti için)
    neg_df = df[df['Polarity'] < 0].copy()
    
    if neg_df.empty:
        return neg_df
        
    # Duygu Şiddeti (Mutlak değer)
    neg_df['Duygu Şiddeti'] = neg_df['Polarity'].abs()
    
    # 2. SNA Analizi: Arkadaş Sayısını 0-1 arası normalize et (Merkezilik)
    min_val = neg_df['Arkadaş_Sayısı'].min()
    max_val = neg_df['Arkadaş_Sayısı'].max()
    
    if max_val == min_val:
        neg_df['Merkezilik'] = 0.5
    else:
        neg_df['Merkezilik'] = (neg_df['Arkadaş_Sayısı'] - min_val) / (max_val - min_val)
        
    # 3. HİBRİT RİSK SKORU HESAPLAMA
    neg_df['Risk Skoru'] = neg_df['Duygu Şiddeti'] * neg_df['Merkezilik']
    
    # Skoru daha okunabilir yapmak için 0-100 arasına çekelim
    neg_df['Risk Skoru'] = (neg_df['Risk Skoru'] * 100).round(1)
    neg_df['Merkezilik'] = neg_df['Merkezilik'].round(3)
    neg_df['Duygu Şiddeti'] = neg_df['Duygu Şiddeti'].round(3)
    
    # Risk Skoruna göre büyükten küçüğe sırala
    neg_df = neg_df.sort_values(by='Risk Skoru', ascending=False)
    
    return neg_df

# --- YAN MENÜ (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2592/2592317.png", width=80)
st.sidebar.title("🛡️ Kriz Kalkanı")
st.sidebar.markdown("### Veri Yükleme Alanı")
st.sidebar.info("Tez Kapsamı: NLP ve SNA tabanlı Hibrit Risk Modellemesi")

uploaded_file = st.sidebar.file_uploader("Kendi verinizi analiz etmek için .xlsx veya .csv yükleyin:", type=['csv', 'xlsx'])

# --- ANA EKRAN (UI) ---
st.title("📊 Dijital İtibar Risk Analizi Dashboard")
st.markdown("İşletmelerin e-WOM (müşteri yorumları) verilerini analiz ederek, **gizli kanaat önderlerini** ve potansiyel itibar krizlerini haritalandırın.")

st.divider()

# Veriyi Yükleme / Hazırlama
if uploaded_file is not None:
    st.success("✅ Dosya başarıyla yüklendi! Sizin veriniz analiz ediliyor...")
    try:
        if uploaded_file.name.endswith('.csv'):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)
            
        # Sütun kontrolü
        required_cols = ['Kullanıcı_ID', 'Yorum_Metni', 'Arkadaş_Sayısı']
        if not all(col in raw_df.columns for col in required_cols):
            st.error(f"HATA: Yüklenen dosyada şu sütunlar olmalıdır: {', '.join(required_cols)}")
            st.stop()
    except Exception as e:
        st.error(f"Dosya okunurken bir hata oluştu: {e}")
        st.stop()
else:
    st.info("📌 Şu an tez kapsamında kullanılan 'Philadelphia Yelp (Temsili)' örnek veri seti görüntülenmektedir.")
    raw_df = load_dummy_data()

# Analizi Çalıştır
analyzed_df = analyze_data(raw_df)

if analyzed_df.empty:
    st.warning("Bu veri setinde negatif yorum (kriz sinyali) bulunamadı. Harika!")
else:
    # --- KPI KARTLARI ---
    toplam_yorum = len(raw_df)
    negatif_yorum = len(analyzed_df)
    yuksek_riskli = len(analyzed_df[analyzed_df['Risk Skoru'] > 50])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="💬 Toplam İncelenen Yorum", value=toplam_yorum)
    with col2:
        st.metric(label="⚠️ Tespit Edilen Negatif Yorum", value=negatif_yorum, delta="-Kriz Sinyalleri", delta_color="inverse")
    with col3:
        st.metric(label="🚨 Yüksek Riskli Kanaat Önderi", value=yuksek_riskli, help="Risk Skoru 50'nin üzerinde olan kullanıcılar")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- RİSK MATRİSİ (SCATTER PLOT) ---
    st.subheader("📍 Hibrit Risk Matrisi (SNA x NLP)")
    st.markdown("Sağ üst çeyrekte yer alan müşteriler, hem **çok öfkeli** hem de ağ içerisinde **çok popüler** olan kilit aktörlerdir.")
    
    fig = px.scatter(
        analyzed_df, 
        x="Merkezilik", 
        y="Duygu Şiddeti", 
        size="Risk Skoru", 
        color="Risk Skoru",
        hover_name="Kullanıcı_ID",
        hover_data=["Arkadaş_Sayısı", "Yorum_Metni"],
        color_continuous_scale="Reds",
        size_max=40,
        labels={
            "Merkezilik": "Ağ Merkeziliği (SNA - Etki Gücü)",
            "Duygu Şiddeti": "Duygu Şiddeti (NLP - Negatiflik)",
            "Risk Skoru": "Kriz Risk Skoru"
        }
    )
    
    # Kritik Bölgeyi (Kırmızı Çeyrek) Vurgulama
    fig.add_shape(
        type="rect",
        x0=0.5, y0=0.5, x1=1.05, y1=1.05,
        fillcolor="red", opacity=0.1, line_width=2, line_color="red", line_dash="dash",
        layer="below"
    )
    
    fig.add_annotation(
        x=0.75, y=0.98,
        text="Acil Müdahale Bölgesi",
        showarrow=False,
        font=dict(color="darkred", size=14, weight="bold")
    )
    
    fig.update_layout(
        plot_bgcolor="rgba(250, 250, 250, 1)",
        height=500,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- VERİ TABLOSU ---
    st.subheader("📋 Acil Müdahale Gerektirenler Tablosu")
    st.markdown("Aşağıdaki liste, risk skoruna göre büyükten küçüğe sıralanmıştır. İşletme yöneticisi öncelikle bu listedeki müşterilerle iletişime geçmelidir.")
    
    display_df = analyzed_df[['Kullanıcı_ID', 'Yorum_Metni', 'Arkadaş_Sayısı', 'Merkezilik', 'Duygu Şiddeti', 'Risk Skoru']]
    
    # Tabloyu şık göstermek için formatlama
    st.dataframe(
        display_df.style.background_gradient(subset=['Risk Skoru'], cmap='Reds'),
        use_container_width=True,
        hide_index=True
    )
    
st.markdown("---")
st.caption("Bu Karar Destek Sistemi, yüksek lisans tez çalışması kapsamında tasarlanmıştır. | © 2026")
