import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from textblob import TextBlob

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hibrit Risk Dashboard 2.0", page_icon="📈", layout="wide")

# --- VERİ ÜRETİCİ ---
@st.cache_data
def get_data():
    # Temsili Philadelphia Yelp Verisi
    data = {
        "Kullanıcı_ID": [f"User_{i:03d}" for i in range(1, 101)],
        "Yorum_Metni": np.random.choice([
            "Rezalet servis!", "Harika yemekler", "İdare eder", 
            "Bir daha gelmem", "Garsonlar çok kaba", "Mükemmel atmosfer",
            "Pahalı ama değmez", "En sevdiğim mekan", "Hayal kırıklığı", "Tavsiye ederim"
        ], 100),
        "Arkadaş_Sayısı": np.random.randint(10, 5000, 100)
    }
    return pd.DataFrame(data)

# --- ANALİZ ---
def run_analysis(df):
    # Eğer yüklenen veride sütun isimleri küçük/büyük harf veya boşlukluyken hata vermesin diye güvenlik önlemi
    if 'Yorum_Metni' not in df.columns:
        st.error("HATA: Excel dosyanızda 'Yorum_Metni' isimli bir sütun bulunamadı. Lütfen sütun isimlerini kontrol edin.")
        st.stop()
        
    df['Polarity'] = df['Yorum_Metni'].apply(lambda x: TextBlob(str(x)).sentiment.polarity)
    
    # Merkezilik Normalizasyonu
    min_val = df['Arkadaş_Sayısı'].min()
    max_val = df['Arkadaş_Sayısı'].max()
    
    # Eğer herkesin arkadaş sayısı aynıysa sıfıra bölme hatası almamak için
    if max_val == min_val:
        df['Merkezilik'] = 0.5
    else:
        df['Merkezilik'] = (df['Arkadaş_Sayısı'] - min_val) / (max_val - min_val)
        
    # Risk Skoru: |Negatif Polarity| * Merkezilik
    df['Risk_Skoru'] = df.apply(lambda x: abs(x['Polarity']) * x['Merkezilik'] * 100 if x['Polarity'] < 0 else 0, axis=1)
    
    # Küsuratları yuvarlayalım ki şık dursun
    df['Risk_Skoru'] = df['Risk_Skoru'].round(1)
    df['Polarity'] = df['Polarity'].round(3)
    df['Merkezilik'] = df['Merkezilik'].round(3)
    
    return df

# --- UI ---
st.title("🛡️ Hibrit Dijital İtibar Risk Analizi")
st.sidebar.header("Veri Girişi")
uploaded_file = st.sidebar.file_uploader("Kendi Excel/CSV Dosyanızı Yükleyin", type=['xlsx', 'csv'])

# --- DOSYA OKUMA VE ANALİZİ ÇALIŞTIRMA (Hatanın Düzeltildiği Yer) ---
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)
        st.sidebar.success("✅ Dosya başarıyla yüklendi!")
    except Exception as e:
        st.sidebar.error(f"Dosya okunurken bir hata oluştu: {e}")
        st.stop()
else:
    st.sidebar.info("Şu an örnek veri gösteriliyor.")
    raw_df = get_data()

# Okunan veriyi analize gönder
df = run_analysis(raw_df)

# --- KPI'LAR ---
c1, c2, c3 = st.columns(3)
c1.metric("Toplam İncelenen Yorum", len(df))
c2.metric("Tespit Edilen Kriz Sinyali (Negatif)", len(df[df['Polarity'] < 0]))
c3.metric("Maksimum Risk Skoru", f"{df['Risk_Skoru'].max():.1f}%")

st.divider()

# --- 3D RİSK EVRENİ ---
st.subheader("🌌 3D Risk Evreni")
st.markdown("Bu grafik, müşterileri **Ağ Gücü (Merkezilik)**, **Duygu Skoru (Negatiflik)** ve **Risk Skoru** eksenlerinde üç boyutlu olarak haritalandırır. Kırmızıya dönen ve yükselen noktalar gizli kanaat önderleridir.")

fig_3d = px.scatter_3d(
    df, x='Merkezilik', y='Polarity', z='Risk_Skoru',
    color='Risk_Skoru', size='Risk_Skoru',
    hover_name='Kullanıcı_ID',
    hover_data=['Arkadaş_Sayısı', 'Yorum_Metni'],
    color_continuous_scale='RdYlGn_r', # Kırmızıdan Yeşile (Ters)
    labels={'Polarity': 'Duygu Skoru', 'Merkezilik': 'Ağ Gücü', 'Risk_Skoru': 'Risk Skoru (%)'}
)

fig_3d.update_layout(height=600, margin=dict(l=0, r=0, b=0, t=0))
st.plotly_chart(fig_3d, use_container_width=True)

# --- TABLO ---
st.subheader("📋 Detaylı Risk Listesi")
st.markdown("İşletmenizin öncelikli olarak müdahale etmesi gereken müşteriler risk skoruna göre aşağıda sıralanmıştır.")

# Tabloyu formatlayıp gösterme
display_df = df[['Kullanıcı_ID', 'Yorum_Metni', 'Arkadaş_Sayısı', 'Merkezilik', 'Polarity', 'Risk_Skoru']]
st.dataframe(
    display_df.sort_values('Risk_Skoru', ascending=False).style.background_gradient(subset=['Risk_Skoru'], cmap='Reds'), 
    use_container_width=True,
    hide_index=True
)
