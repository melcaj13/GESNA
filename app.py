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
    df['Polarity'] = df['Yorum_Metni'].apply(lambda x: TextBlob(str(x)).sentiment.polarity)
    # Merkezilik Normalizasyonu
    df['Merkezilik'] = (df['Arkadaş_Sayısı'] - df['Arkadaş_Sayısı'].min()) / (df['Arkadaş_Sayısı'].max() - df['Arkadaş_Sayısı'].min())
    # Risk Skoru: |Negatif Polarity| * Merkezilik
    df['Risk_Skoru'] = df.apply(lambda x: abs(x['Polarity']) * x['Merkezilik'] * 100 if x['Polarity'] < 0 else 0, axis=1)
    return df

# --- UI ---
st.title("🛡️ Hibrit Dijital İtibar Risk Analizi")
st.sidebar.header("Veri Girişi")
uploaded_file = st.sidebar.file_uploader("Excel/CSV Yükle", type=['xlsx', 'csv'])

df = run_analysis(uploaded_file if uploaded_file else get_data())

# KPI'lar
c1, c2, c3 = st.columns(3)
c1.metric("Toplam Analiz", len(df))
c2.metric("Kriz Sinyalleri", len(df[df['Polarity'] < 0]))
c3.metric("Maksimum Risk", f"{df['Risk_Skoru'].max():.1f}%")

# 3D RİSK EVRENİ (Favorin!)
st.subheader("🌌 3D Risk Evreni")
fig_3d = px.scatter_3d(
    df, x='Merkezilik', y='Polarity', z='Risk_Skoru',
    color='Risk_Skoru', size='Risk_Skoru',
    hover_name='Kullanıcı_ID',
    color_continuous_scale='RdYlGn_r', # Kırmızıdan Yeşile
    labels={'Polarity': 'Duygu Skoru', 'Merkezilik': 'Ağ Gücü', 'Risk_Skoru': 'Risk %'}
)
st.plotly_chart(fig_3d, use_container_width=True)

# TABLO
st.subheader("📋 Detaylı Risk Listesi")
st.dataframe(df.sort_values('Risk_Skoru', ascending=False), use_container_width=True)
