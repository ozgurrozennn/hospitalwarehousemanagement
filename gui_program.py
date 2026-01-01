# streamlit_app_gelismis.py

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import random
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import qrcode
from PIL import Image
import requests
import io

# Barkod kütüphanesi kontrolü
try:
    from barcode import EAN13
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False

# Sayfa yapılandırması
st.set_page_config(
    page_title="Hastane Depo Yönetim Sistemi",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Oracle tarzı
st.markdown("""
<style>
    /* Genel stil */
    .main {
        background-color: #f5f6f7;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #2c2e4a;
    }

    [data-testid="stSidebar"] .css-1d391kg {
        color: white;
    }

    /* Başlık */
    .integration-header {
        background-color: white;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }

    /* Entegrasyon kartı */
    .integration-card {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #d9dde3;
        margin-bottom: 15px;
    }

    .integration-title {
        font-size: 16px;
        font-weight: bold;
        color: #333;
        margin-bottom: 5px;
    }

    .integration-desc {
        font-size: 14px;
        color: #666;
        margin-bottom: 10px;
    }

    .integration-status-enabled {
        color: #27ae60;
        font-weight: bold;
    }

    .integration-status-disabled {
        color: #95a5a6;
        font-weight: bold;
    }

    /* Section başlıkları */
    .section-title {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    /* Custom Actions */
    .custom-actions {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #d9dde3;
        margin-top: 20px;
    }

    /* Butonlar */
    .stButton>button {
        border-radius: 5px;
        background-color: #0572ce;
        color: white;
        border: none;
        padding: 8px 20px;
    }

    .stButton>button:hover {
        background-color: #045aa8;
    }

    /* Komut kutusu */
    .command-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #0572ce;
        margin: 10px 0;
        font-family: monospace;
    }

    /* Lot badge */
    .lot-badge {
        background-color: #f39c12;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-left: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Veri yükleme/kaydetme fonksiyonları
VERI_DOSYASI = "hastane_depo_streamlit.json"


def veri_yukle():
    """Veriyi yükle"""
    if Path(VERI_DOSYASI).exists():
        with open(VERI_DOSYASI, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {
            "urunler": {
                "URN001": {
                    "ad": "Eldiven (Lateks)",
                    "barkod_tipi": "QR Kod",
                    "barkod_no": "123456789012",
                    "lot_no": "LOT2024A",
                    "lot_adet": 500,
                    "depo_id": "DEP001"
                },
                "URN002": {
                    "ad": "Maske (Cerrahi)",
                    "barkod_tipi": "UTC Kod",
                    "barkod_no": "567890123456",
                    "lot_no": "LOT2024B",
                    "lot_adet": 1000,
                    "depo_id": "DEP001"
                },
                "URN003": {
                    "ad": "Serum Seti",
                    "barkod_tipi": "QR Kod",
                    "barkod_no": "234567890123",
                    "lot_no": "LOT2024C",
                    "lot_adet": 300,
                    "depo_id": "DEP002"
                },
            },
            "depolar": {
                "DEP001": {
                    "ad": "Acil Servis",
                    "urunler": {
                        "URN001": {"miktar": 50, "kritik_seviye": 100, "min_seviye": 150, "max_seviye": 1000},
                        "URN002": {"miktar": 200, "kritik_seviye": 100, "min_seviye": 250, "max_seviye": 1500}
                    }
                },
                "DEP002": {
                    "ad": "Ameliyathane",
                    "urunler": {
                        "URN003": {"miktar": 30, "kritik_seviye": 50, "min_seviye": 100, "max_seviye": 500},
                        "URN001": {"miktar": 300, "kritik_seviye": 100, "min_seviye": 200, "max_seviye": 800}
                    }
                },
                "DEP003": {
                    "ad": "Yoğun Bakım",
                    "urunler": {
                        "URN001": {"miktar": 80, "kritik_seviye": 100, "min_seviye": 150, "max_seviye": 700},
                        "URN003": {"miktar": 120, "kritik_seviye": 80, "min_seviye": 150, "max_seviye": 600}
                    }
                }
            },
            "entegrasyonlar": {
                "sistem": [
                    {"name": "Hastane Bilgi Sistemi Entegrasyonu",
                     "description": "Hastane bilgi sistemi ile veri senkronizasyonu", "enabled": True},
                    {"name": "E-Fatura Entegrasyonu", "description": "Elektronik fatura sistemine otomatik aktarım",
                     "enabled": False},
                    {"name": "Barkod Yazıcı Entegrasyonu", "description": "Doğrudan barkod yazıcıya gönderim",
                     "enabled": True},
                    {"name": "SMS Bildirimleri", "description": "Kritik stok seviyeleri için SMS uyarıları",
                     "enabled": False}
                ],
                "harici": [
                    {"name": "Microsoft Office Online",
                     "description": "Raporları Office Online ile görüntüleme ve düzenleme", "enabled": True},
                    {"name": "Google Drive Yedekleme", "description": "Otomatik Google Drive yedekleme",
                     "enabled": False},
                    {"name": "Dropbox Senkronizasyonu", "description": "Dropbox ile dosya senkronizasyonu",
                     "enabled": False}
                ]
            }
        }


def veri_kaydet(data):
    """Veriyi kaydet"""
    with open(VERI_DOSYASI, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def tcmb_kur_cek():
    """TCMB'den güncel döviz kurlarını çek"""
    try:
        import requests
        import xml.etree.ElementTree as ET
        from datetime import datetime

        # TCMB XML feed
        url = "https://www.tcmb.gov.tr/kurlar/today.xml"

        response = requests.get(url, timeout=5)
        root = ET.fromstring(response.content)

        kurlar = {}
        tarih = root.get('Date')

        for currency in root.findall('Currency'):
            kod = currency.get('CurrencyCode')
            if kod in ['USD', 'EUR', 'GBP']:
                forex_buying = currency.find('ForexBuying')
                if forex_buying is not None and forex_buying.text:
                    kurlar[kod] = float(forex_buying.text)

        kurlar['tarih'] = tarih
        return kurlar
    except Exception as e:
        # Hata durumunda sabit kurlar
        return {'USD': 34.50, 'EUR': 37.20, 'GBP': 43.80, 'tarih': datetime.now().strftime('%d.%m.%Y')}


def qr_kod_olustur(data, size=200):
    """QR kod oluştur ve BytesIO döndür"""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # PIL Image'i BytesIO'ya çevir
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def stok_durumu_hesapla(miktar, kritik, min_seviye, max_seviye):
    """Stok durumunu hesapla"""
    if miktar <= kritik:
        return "🔴 Kritik"
    elif miktar < min_seviye:
        return "🟡 Düşük"
    elif miktar <= max_seviye:
        return "🟢 Normal"
    else:
        return "🟠 Fazla"


def depo_stok_raporu(depo_adi, kritik_only=False):
    """Depo stok raporunu hazırla - Dinamik depo algılama"""
    data = st.session_state.data
    rapor = []

    for depo_id, depo_bilgi in data["depolar"].items():
        # Depo adında arama yap (kısmi eşleşme)
        if depo_adi.lower() in depo_bilgi["ad"].lower():
            for urun_id, stok_bilgi in depo_bilgi["urunler"].items():
                if urun_id not in data["urunler"]:
                    continue

                urun_adi = data["urunler"][urun_id]["ad"]
                lot_no = data["urunler"][urun_id].get("lot_no", "-")
                lot_adet = data["urunler"][urun_id].get("lot_adet", "-")

                durum = stok_durumu_hesapla(
                    stok_bilgi["miktar"],
                    stok_bilgi["kritik_seviye"],
                    stok_bilgi["min_seviye"],
                    stok_bilgi["max_seviye"]
                )

                # Kritik filtresi
                if kritik_only and "🔴" not in durum:
                    continue

                rapor.append({
                    "Depo": depo_bilgi["ad"],
                    "Ürün": urun_adi,
                    "LOT No": lot_no,
                    "LOT Adet": lot_adet,
                    "Stok Miktar": stok_bilgi["miktar"],
                    "Kritik Seviye": stok_bilgi["kritik_seviye"],
                    "Min Seviye": stok_bilgi["min_seviye"],
                    "Max Seviye": stok_bilgi["max_seviye"],
                    "Durum": durum
                })

    return rapor


def excel_olustur(df, dosya_adi):
    """Excel dosyası oluştur"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Stok Raporu')
    output.seek(0)
    return output


def csv_olustur(df):
    """CSV dosyası oluştur"""
    return df.to_csv(index=False).encode('utf-8-sig')


def chatbox_analiz(mesaj):
    """Chatbox mesajını analiz et ve işlem yap"""
    mesaj_lower = mesaj.lower().strip()

    # Komut listesi göster
    if mesaj_lower == "komut" or mesaj_lower == "komutlar":
        return "command_list", None

    # Ürün ekle
    if "ürün ekle" in mesaj_lower or "urun ekle" in mesaj_lower:
        st.session_state.current_page = "Assets"
        return "redirect", "✅ Ürün ekleme sayfasına yönlendiriliyorsunuz..."

    # Depo ekle - YENİ ÖZELLİK
    if "depo ekle" in mesaj_lower:
        st.session_state.current_page = "Sites"
        st.session_state.show_depo_ekle_form = True
        return "redirect", "✅ Depo ekleme sayfasına yönlendiriliyorsunuz..."

    # Fatura sorgulama
    if "fatura" in mesaj_lower or "irsaliye" in mesaj_lower:
        if len(st.session_state.data.get('faturalar', [])) == 0:
            return "text", "❌ Henüz hiç fatura kaydı yok. 'Fatura Gir' menüsünden fatura ekleyebilirsiniz."

        faturalar_ozet = []
        for fatura in st.session_state.data['faturalar']:
            faturalar_ozet.append({
                'Belge Tipi': fatura['belge_tipi'],
                'Fatura No': fatura['fatura_no'],
                'Tarih': fatura['fatura_tarihi'],
                'Tedarikçi': fatura['tedarikci'],
                'Kalem Sayısı': fatura['toplam_kalem'],
                'Toplam (TRY)': fatura['genel_toplam_try']
            })

        return "fatura_list", {"faturalar": faturalar_ozet, "baslik": "📄 Kayıtlı Faturalar"}

    # Depo listesi
    if mesaj_lower == "depolar" or mesaj_lower == "depo listesi" or "depoları göster" in mesaj_lower:
        if len(st.session_state.data.get('depolar', {})) == 0:
            return "text", "❌ Henüz hiç depo yok. 'Depolar' menüsünden depo ekleyebilirsiniz."

        depo_listesi = []
        for depo_id, depo_bilgi in st.session_state.data['depolar'].items():
            depo_listesi.append({
                'Depo ID': depo_id,
                'Depo Adı': depo_bilgi['ad'],
                'Ürün Sayısı': len(depo_bilgi['urunler']),
                'Toplam Stok': sum([stok['miktar'] for stok in depo_bilgi['urunler'].values()])
            })

        return "depo_list", {"depolar": depo_listesi, "baslik": "🏪 Kayıtlı Depolar"}

    # TCMB Kur sorgulama - DÜZELTME
    if "tcmb" in mesaj_lower or "kur" in mesaj_lower or "döviz" in mesaj_lower:
        # doviz_kurlari yoksa oluştur
        if 'doviz_kurlari' not in st.session_state:
            st.session_state.doviz_kurlari = tcmb_kur_cek()

        kurlar = st.session_state.doviz_kurlari
        kur_bilgisi = f"""
### 💱 TCMB Döviz Kurları (Alış)

📅 **Tarih:** {kurlar.get('tarih', 'Bilinmiyor')}

🇺🇸 **USD/TRY:** {kurlar.get('USD', 0):.4f} ₺
🇪🇺 **EUR/TRY:** {kurlar.get('EUR', 0):.4f} ₺
🇬🇧 **GBP/TRY:** {kurlar.get('GBP', 0):.4f} ₺

*Kurlar TCMB'den otomatik çekilmektedir.*
"""
        return "text", kur_bilgisi

    # Depo stok sorgulama - DİNAMİK
    depo_bulundu = None
    bulunan_depo_adi = None

    for depo_id, depo_bilgi in st.session_state.data["depolar"].items():
        depo_adi_lower = depo_bilgi["ad"].lower()

        # Mesajda depo adı geçiyor mu? (tam veya kısmi eşleşme)
        for kelime in mesaj_lower.split():
            if len(kelime) >= 3 and kelime in depo_adi_lower:
                depo_bulundu = depo_adi_lower
                bulunan_depo_adi = depo_bilgi["ad"]
                break

        if depo_bulundu:
            break

    # Depo bulundu ve stok sorgusu yapılıyor
    if depo_bulundu and ("stok" in mesaj_lower or "durum" in mesaj_lower or "kritik" in mesaj_lower):
        kritik_mi = "kritik" in mesaj_lower

        rapor = depo_stok_raporu(depo_bulundu, kritik_mi)
        if rapor:
            baslik = f"{bulunan_depo_adi} - {'Kritik Ürünler' if kritik_mi else 'Stok Durumu'}"
            return "stock_report", {"rapor": rapor, "baslik": baslik, "depo": depo_bulundu, "kritik": kritik_mi}
        else:
            return "text", f"❌ '{bulunan_depo_adi}' deposunda {'kritik ürün' if kritik_mi else 'ürün'} bulunamadı.\n\n💡 Depoya ürün eklemek için 'Stok' menüsünü kullanın."

    # Genel yardım
    return "text", "Komutu anlayamadım. Yardım için 'komut' yazın."


# Session state başlat
if 'data' not in st.session_state:
    st.session_state.data = veri_yukle()

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant",
         "content": "Merhaba! Ben Hastane Depo Asistanınızım. Size nasıl yardımcı olabilirim?\n\n💡 Komutları görmek için **'komut'** yazın."}
    ]

if 'show_barkod_dok' not in st.session_state:
    st.session_state.show_barkod_dok = False

if 'selected_product_for_barkod' not in st.session_state:
    st.session_state.selected_product_for_barkod = None

if 'show_depo_ekle_form' not in st.session_state:
    st.session_state.show_depo_ekle_form = False

# TCMB kurlarını başlat - ÖNEMLİ DÜZELTME
if 'doviz_kurlari' not in st.session_state:
    st.session_state.doviz_kurlari = tcmb_kur_cek()

# Sidebar menü
with st.sidebar:
    st.markdown("### 🏥 Hastane Depo Sistemi")
    st.markdown("---")

    # Ana Menüler
    st.markdown("#### NAVIGATION")
    if st.button("🏠 Ana Sayfa", use_container_width=True):
        st.session_state.current_page = "Dashboard"
        st.rerun()

    if st.button("📦 Stok", use_container_width=True):
        st.session_state.current_page = "Assets"
        st.rerun()

    if st.button("🏪 Depolar", use_container_width=True):
        st.session_state.current_page = "Sites"
        st.rerun()

    if st.button("📊 Analizler", use_container_width=True):
        st.session_state.current_page = "Analytics"
        st.rerun()

    st.markdown("---")
    st.markdown("#### COLLABORATION")

    if st.button("📄 Fatura Gir", use_container_width=True):
        st.session_state.current_page = "Documents"
        st.rerun()

    if st.button("💬 Yapay Zekaya Sor", use_container_width=True):
        st.session_state.current_page = "Conversations"
        st.rerun()

    st.markdown("---")
    st.markdown("#### ADMINISTRATION")

# Ana İçerik
if st.session_state.current_page == "Dashboard":
    # Dashboard sayfası
    st.markdown("# 🏥 Hastane Depo Yönetim Sistemi")
    st.markdown("### Dashboard")

    # Metrikler
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Toplam Ürün", len(st.session_state.data["urunler"]), "2 yeni")

    with col2:
        st.metric("Toplam Depo", len(st.session_state.data["depolar"]), "1 yeni")

    with col3:
        toplam_stok = sum(len(d["urunler"]) for d in st.session_state.data["depolar"].values())
        st.metric("Stok Kayıtları", toplam_stok, "-3")

    with col4:
        # Kritik ürün sayısını hesapla
        kritik_sayi = 0
        for depo_bilgi in st.session_state.data["depolar"].values():
            for stok_bilgi in depo_bilgi["urunler"].values():
                if stok_bilgi["miktar"] <= stok_bilgi["kritik_seviye"]:
                    kritik_sayi += 1
        st.metric("Kritik Ürün", kritik_sayi, "⚠️")

    st.markdown("---")

    # Grafikler
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Stok Durumu")
        if len(st.session_state.data["depolar"]) > 0:
            # Gerçek veriyi hesapla
            kritik = normal = dusuk = fazla = 0
            for depo_bilgi in st.session_state.data["depolar"].values():
                for stok_bilgi in depo_bilgi["urunler"].values():
                    durum = stok_durumu_hesapla(
                        stok_bilgi["miktar"],
                        stok_bilgi["kritik_seviye"],
                        stok_bilgi["min_seviye"],
                        stok_bilgi["max_seviye"]
                    )
                    if "🔴" in durum:
                        kritik += 1
                    elif "🟡" in durum:
                        dusuk += 1
                    elif "🟢" in durum:
                        normal += 1
                    else:
                        fazla += 1

            durum_data = pd.DataFrame({
                'Durum': ['Kritik', 'Düşük', 'Normal', 'Fazla'],
                'Adet': [kritik, dusuk, normal, fazla]
            })
            fig = px.pie(durum_data, values='Adet', names='Durum',
                         color_discrete_sequence=['#e74c3c', '#f39c12', '#27ae60', '#3498db'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Henüz veri yok")

    with col2:
        st.markdown("### 📈 Depo Bazında Ürün Dağılımı")
        if len(st.session_state.data["depolar"]) > 0:
            depo_data = pd.DataFrame([
                {
                    "Depo": v["ad"],
                    "Ürün Sayısı": len(v["urunler"])
                }
                for k, v in st.session_state.data["depolar"].items()
            ])
            fig = px.bar(depo_data, x='Depo', y='Ürün Sayısı',
                         color_discrete_sequence=['#0572ce'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Henüz veri yok")

elif st.session_state.current_page == "Assets":
    st.markdown("# 📦 Ürün Yönetimi")

    tab1, tab2, tab3, tab4 = st.tabs(["➕ Ürün Ekle", "📋 Ürün Listesi", "🖨️ Barkod Dök", "🗑️ Ürün Sil"])

    with tab1:
        st.markdown("### Yeni Ürün Ekle")

        with st.form("urun_ekle_form"):
            col1, col2 = st.columns(2)

            with col1:
                urun_adi = st.text_input("Ürün Adı *", placeholder="Örn: Eldiven (Lateks)")
                barkod_tipi = st.selectbox("Barkod Tipi *", ["QR Kod", "UTC Kod", "LOT Numarası"])
                lot_no = st.text_input("LOT Numarası *", placeholder="Örn: LOT2024A")

            with col2:
                barkod_no = st.text_input(
                    "Barkod Numarası *",
                    value=''.join([str(random.randint(0, 9)) for _ in range(12)]),
                    help="Otomatik oluşturuldu, değiştirebilirsiniz"
                )
                lot_adet = st.number_input("LOT Adeti *", min_value=1, value=100, step=1)

                # Depo seçimi
                depo_listesi = list(st.session_state.data["depolar"].items())
                if depo_listesi:
                    depo_secenekleri = [f"{depo_id} - {depo_bilgi['ad']}" for depo_id, depo_bilgi in depo_listesi]
                    secili_depo = st.selectbox("Depo Seçin *", depo_secenekleri)
                else:
                    st.warning("⚠️ Önce en az bir depo eklemelisiniz!")
                    secili_depo = None

            st.markdown("---")

            # Depoya atama bilgileri (opsiyonel)
            depoya_ata = st.checkbox("✅ Bu ürünü depoya hemen ata (stok seviyeleri belirle)")

            if depoya_ata:
                col3, col4, col5 = st.columns(3)
                with col3:
                    max_seviye = st.number_input("Maksimum Seviye", min_value=1, value=1000, step=10)
                with col4:
                    kritik_seviye = st.number_input("Kritik Seviye", min_value=0, value=100, step=10)
                with col5:
                    min_seviye = st.number_input("Minimum Seviye", min_value=1, value=50, step=10)

            submitted = st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True)

            if submitted:
                if not urun_adi or not lot_no or not secili_depo:
                    st.error("❌ Lütfen tüm zorunlu alanları doldurun!")
                else:
                    # Yeni ürün ID'si oluştur
                    urun_id = f"URN{len(st.session_state.data['urunler']) + 1:03d}"

                    # Seçili depo ID'sini al
                    depo_id = secili_depo.split(" - ")[0]

                    # Ürünü ekle
                    st.session_state.data["urunler"][urun_id] = {
                        "ad": urun_adi,
                        "barkod_tipi": barkod_tipi,
                        "barkod_no": barkod_no,
                        "lot_no": lot_no,
                        "lot_adet": lot_adet,
                        "depo_id": depo_id
                    }

                    # Depoya ata
                    if depoya_ata:
                        if max_seviye > kritik_seviye > min_seviye:
                            st.session_state.data["depolar"][depo_id]["urunler"][urun_id] = {
                                "miktar": 0,
                                "kritik_seviye": kritik_seviye,
                                "min_seviye": min_seviye,
                                "max_seviye": max_seviye
                            }
                        else:
                            st.error("❌ Hatalı seviye sıralaması! Doğru: Maksimum > Kritik > Minimum")
                            st.stop()

                    veri_kaydet(st.session_state.data)
                    st.success(f"✅ Ürün başarıyla eklendi!\n\n**ID:** {urun_id}\n**LOT:** {lot_no} ({lot_adet} adet)")
                    st.rerun()

    with tab2:
        st.markdown("### Ürün Listesi")

        if len(st.session_state.data["urunler"]) > 0:
            df = pd.DataFrame([
                {
                    "ID": k,
                    "Ürün Adı": v["ad"],
                    "Barkod Tipi": v["barkod_tipi"],
                    "Barkod No": v["barkod_no"],
                    "LOT No": v.get("lot_no", "-"),
                    "LOT Adet": v.get("lot_adet", "-"),
                    "Depo": st.session_state.data["depolar"].get(v.get("depo_id", ""), {}).get("ad", "Atanmamış")
                }
                for k, v in st.session_state.data["urunler"].items()
            ])

            # Filtreleme
            col1, col2 = st.columns([2, 1])
            with col1:
                arama = st.text_input("🔍 Ürün Ara", placeholder="Ürün adı veya LOT no ile ara...")
            with col2:
                barkod_filtre = st.selectbox("Barkod Tipi Filtrele", ["Tümü", "QR Kod", "UTC Kod", "LOT Numarası"])

            # Filtreleme uygula
            if arama:
                df = df[df['Ürün Adı'].str.contains(arama, case=False) | df['LOT No'].str.contains(arama, case=False)]

            if barkod_filtre != "Tümü":
                df = df[df['Barkod Tipi'] == barkod_filtre]

            st.dataframe(df, use_container_width=True, height=400)

            # Excel/CSV İndirme
            col1, col2 = st.columns(2)
            with col1:
                excel_data = excel_olustur(df, "urun_listesi.xlsx")
                st.download_button(
                    label="📊 Excel İndir",
                    data=excel_data,
                    file_name=f"urun_listesi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with col2:
                csv_data = csv_olustur(df)
                st.download_button(
                    label="📄 CSV İndir",
                    data=csv_data,
                    file_name=f"urun_listesi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("Henüz ürün eklenmemiş")

    with tab3:
        st.markdown("### 🖨️ Barkod Dök")

        if len(st.session_state.data["urunler"]) > 0:
            # Ürün seçimi
            urun_listesi = list(st.session_state.data["urunler"].items())
            urun_secenekleri = [
                f"{urun_id} - {urun_bilgi['ad']} (LOT: {urun_bilgi.get('lot_no', '-')})"
                for urun_id, urun_bilgi in urun_listesi
            ]

            secili_urun_str = st.selectbox("Ürün Seçin", urun_secenekleri)
            secili_urun_id = secili_urun_str.split(" - ")[0]
            secili_urun = st.session_state.data["urunler"][secili_urun_id]

            # Ürün bilgileri
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Barkod Tipi:** {secili_urun['barkod_tipi']}")
            with col2:
                st.info(f"**LOT No:** {secili_urun.get('lot_no', '-')}")
            with col3:
                st.info(f"**LOT Adet:** {secili_urun.get('lot_adet', '-')}")

            # Sadece QR ve UTC için barkod dökümü
            if secili_urun['barkod_tipi'] in ["QR Kod", "UTC Kod"]:
                st.markdown("---")

                # Barkod döküm ayarları
                col1, col2 = st.columns(2)
                with col1:
                    barkod_adet = st.number_input(
                        "Kaç Adet Barkod Oluşturulsun?",
                        min_value=1,
                        max_value=1000,
                        value=10,
                        step=1
                    )

                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🖨️ Barkod Oluştur", type="primary", use_container_width=True):
                        st.session_state.show_barkod_dialog = True
                        st.session_state.selected_product_for_barkod = secili_urun_id
                        st.session_state.barkod_adet = barkod_adet
                        st.rerun()


                # Barkod dialog/popup
                @st.dialog(f"🖨️ Barkod Yazıcı Sayfası - {secili_urun['ad']}")
                def show_barkod_printer():
                    st.markdown(f"### {secili_urun['barkod_tipi']} - {st.session_state.barkod_adet} Adet")

                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric("Ürün", secili_urun['ad'])
                    with col_info2:
                        st.metric("LOT No", secili_urun.get('lot_no', '-'))
                    with col_info3:
                        st.metric("Barkod No", secili_urun['barkod_no'])

                    st.markdown("---")

                    if secili_urun['barkod_tipi'] == "QR Kod":
                        st.markdown("### 📱 QR Kodlar")

                        # QR kodları grid halinde göster
                        cols_per_row = 4
                        num_to_show = min(st.session_state.barkod_adet, 20)  # Maksimum 20 göster

                        for row in range((num_to_show + cols_per_row - 1) // cols_per_row):
                            cols = st.columns(cols_per_row)
                            for col_idx in range(cols_per_row):
                                i = row * cols_per_row + col_idx
                                if i < num_to_show:
                                    with cols[col_idx]:
                                        # QR kod oluştur ve base64'e çevir
                                        qr = qrcode.QRCode(version=1, box_size=10, border=4)
                                        qr.add_data(f"{secili_urun['barkod_no']}-{i + 1}")
                                        qr.make(fit=True)
                                        qr_img = qr.make_image(fill_color="black", back_color="white")

                                        # BytesIO'ya kaydet
                                        buf = BytesIO()
                                        qr_img.save(buf, format='PNG')
                                        buf.seek(0)

                                        st.image(buf, caption=f"QR #{i + 1}", use_column_width=True)

                        if st.session_state.barkod_adet > 20:
                            st.info(
                                f"ℹ️ İlk 20 barkod gösterildi. Toplam {st.session_state.barkod_adet} barkod oluşturuldu.")

                    else:  # UTC Kod
                        st.markdown("### 📊 UTC Barkod (EAN13)")

                        if BARCODE_AVAILABLE:
                            # UTC kodları grid halinde göster
                            cols_per_row = 3
                            num_to_show = min(st.session_state.barkod_adet, 12)  # Maksimum 12 göster

                            for row in range((num_to_show + cols_per_row - 1) // cols_per_row):
                                cols = st.columns(cols_per_row)
                                for col_idx in range(cols_per_row):
                                    i = row * cols_per_row + col_idx
                                    if i < num_to_show:
                                        with cols[col_idx]:
                                            # EAN13 için 12 haneli kod gerekli (13. hane otomatik check digit)
                                            barkod_12_hane = secili_urun['barkod_no'][:12].zfill(12)

                                            # EAN13 barkod oluştur
                                            ean = EAN13(barkod_12_hane, writer=ImageWriter())

                                            # BytesIO'ya kaydet
                                            buf = BytesIO()
                                            ean.write(buf)
                                            buf.seek(0)

                                            st.image(buf, caption=f"UTC #{i + 1}", use_column_width=True)

                            if st.session_state.barkod_adet > 12:
                                st.info(
                                    f"ℹ️ İlk 12 barkod gösterildi. Toplam {st.session_state.barkod_adet} barkod oluşturuldu.")

                        else:
                            st.error("⚠️ python-barcode kütüphanesi yüklü değil!")
                            st.code("pip install python-barcode", language="bash")
                            st.info(
                                f"📊 {st.session_state.barkod_adet} adet UTC barkod numarası: {secili_urun['barkod_no']}")

                    st.markdown("---")

                    # Yazdırma bilgisi
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        st.success(f"✅ {st.session_state.barkod_adet} adet barkod hazır!")
                    with col_btn2:
                        if st.button("✖️ Kapat", use_container_width=True):
                            st.session_state.show_barkod_dialog = False
                            st.rerun()


                # Dialog'u göster
                if st.session_state.get('show_barkod_dialog',
                                        False) and st.session_state.selected_product_for_barkod == secili_urun_id:
                    show_barkod_printer()

            else:
                st.warning(
                    "⚠️ LOT Numarası için barkod oluşturulamaz. Sadece QR Kod ve UTC Kod tipleri için barkod dökümü yapılabilir.")

        else:
            st.info("Önce ürün eklemelisiniz")

    with tab4:
        st.markdown("### Ürün Sil")

        if len(st.session_state.data["urunler"]) > 0:
            urun_secim = st.selectbox(
                "Silinecek Ürünü Seçin",
                options=list(st.session_state.data["urunler"].keys()),
                format_func=lambda
                    x: f"{x} - {st.session_state.data['urunler'][x]['ad']} (LOT: {st.session_state.data['urunler'][x].get('lot_no', '-')})"
            )

            if st.button("🗑️ Sil", type="primary"):
                del st.session_state.data["urunler"][urun_secim]

                # Depolardaki kayıtları da temizle
                for depo_id in st.session_state.data["depolar"]:
                    if urun_secim in st.session_state.data["depolar"][depo_id]["urunler"]:
                        del st.session_state.data["depolar"][depo_id]["urunler"][urun_secim]

                veri_kaydet(st.session_state.data)
                st.success("✅ Ürün silindi!")
                st.rerun()
        else:
            st.info("Silinecek ürün yok")

elif st.session_state.current_page == "Sites":
    st.markdown("# 🏪 Depo Yönetimi")

    tab1, tab2, tab3 = st.tabs(["➕ Depo Ekle", "📋 Depo Listesi", "🗑️ Depo Sil"])

    with tab1:
        st.markdown("### Yeni Depo Ekle")

        # Chatbox'tan gelindiyse otomatik formu aç
        if st.session_state.get('show_depo_ekle_form', False):
            st.info("🤖 Yapay zeka tarafından yönlendirildiniz. Depo bilgilerini girin:")
            st.session_state.show_depo_ekle_form = False

        depo_adi = st.text_input("Depo Adı", placeholder="Örn: Radyoloji Deposu")

        if st.button("💾 Kaydet", type="primary"):
            if depo_adi:
                depo_id = f"DEP{len(st.session_state.data['depolar']) + 1:03d}"
                st.session_state.data["depolar"][depo_id] = {
                    "ad": depo_adi,
                    "urunler": {}
                }
                veri_kaydet(st.session_state.data)

                # Başarı mesajı
                st.success(f"✅ Depo eklendi! ID: {depo_id}")

                # Chatbot komutlarını göster
                st.markdown("---")
                st.markdown("### 🤖 Yapay Zeka Komutları")
                st.info(f"""
**Bu depo için Chatbox'ta kullanabileceğiniz komutlar:**

📊 **Stok Sorguları:**
- `{depo_adi.lower()} stok` → Bu deponun stok durumunu göster
- `{depo_adi.lower()} kritik` → Bu depodaki kritik ürünleri göster
- `{depo_adi.lower()} durum` → Depo stok durumu

💡 **Kısaltmalar da çalışır:**
- `{depo_adi.split()[0].lower()} stok` → İlk kelime yeterli
- `{depo_adi[:4].lower()} kritik` → İlk 4 harf bile yeterli

**Örnek Kullanım:**
```
💬 Chatbox'a git → "Yapay Zekaya Sor" menüsü
📝 Yaz: {depo_adi.lower()} stok
✅ Enter'a bas
📊 Stok raporu gelir!
```

**Diğer Komutlar:**
- `depolar` → Tüm depoları göster
- `faturalar` → Faturaları göster
- `tcmb` → Güncel döviz kurları
- `depo ekle` → 🤖 Yapay zeka ile depo ekleme (buraya yönlendirir)
""")

                st.balloons()
                st.rerun()
            else:
                st.error("Lütfen depo adını girin!")

    with tab2:
        st.markdown("### Depo Listesi")

        if len(st.session_state.data["depolar"]) > 0:
            df = pd.DataFrame([
                {
                    "ID": k,
                    "Depo Adı": v["ad"],
                    "Ürün Sayısı": len(v["urunler"])
                }
                for k, v in st.session_state.data["depolar"].items()
            ])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Henüz depo eklenmemiş")

    with tab3:
        st.markdown("### Depo Sil")

        if len(st.session_state.data["depolar"]) > 0:
            depo_secim = st.selectbox(
                "Silinecek Depoyu Seçin",
                options=list(st.session_state.data["depolar"].keys()),
                format_func=lambda x: f"{x} - {st.session_state.data['depolar'][x]['ad']}"
            )

            if st.button("🗑️ Sil", type="primary"):
                del st.session_state.data["depolar"][depo_secim]
                veri_kaydet(st.session_state.data)
                st.success("✅ Depo silindi!")
                st.rerun()
        else:
            st.info("Silinecek depo yok")

elif st.session_state.current_page == "Conversations":
    st.markdown("# 💬 Chatbox - Akıllı Sorgulama")

    # Chat mesajlarını göster
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

            # Rapor varsa göster
            if "report_data" in message:
                df = pd.DataFrame(message["report_data"])
                st.dataframe(df, use_container_width=True)

                # İndirme butonları
                st.markdown("### 📥 Raporu İndir")
                col1, col2, col3 = st.columns(3)

                with col1:
                    excel_data = excel_olustur(df, "stok_raporu.xlsx")
                    st.download_button(
                        label="📊 Excel İndir",
                        data=excel_data,
                        file_name=f"stok_raporu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col2:
                    csv_data = csv_olustur(df)
                    st.download_button(
                        label="📄 CSV İndir",
                        data=csv_data,
                        file_name=f"stok_raporu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                with col3:
                    st.info("📑 PDF özelliği yakında!")

    # Chat input
    if prompt := st.chat_input("Mesajınızı yazın... (Komutlar için 'komut' yazın)"):
        # Kullanıcı mesajını ekle
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Mesajı analiz et
        response_type, response_data = chatbox_analiz(prompt)

        if response_type == "command_list":
            komut_listesi = """
### 📋 Kullanılabilir Komutlar

**Ürün İşlemleri:**
- `ürün ekle` → Ürün ekleme sayfasını aç
- `urun ekle` → Ürün ekleme sayfasını aç

**Depo İşlemleri:**
- `depo ekle` → 🤖 Depo ekleme sayfasını aç
- `depolar` → Tüm depoları listele
- `depo listesi` → Depo listesini göster
- `depoları göster` → Depoları göster

**Fatura Sorguları:**
- `faturalar` → Tüm faturaları listele
- `fatura` → Fatura listesini göster
- `irsaliye` → İrsaliye listesini göster

**Döviz Kurları:**
- `tcmb` → TCMB güncel kurlarını göster
- `kur` → Döviz kurlarını göster
- `döviz` → Güncel döviz kurları

**Stok Sorguları:**
- `merkez depo stok` → Merkez Depo'nun tüm stok durumunu göster (LOT bilgili)
- `merkez depo kritik` → Merkez Depo'daki kritik ürünleri göster
- `merkez stok` → Merkez Depo stok durumu
- `acil servis stok` → Acil Servis deposunun stok durumunu göster
- `acil servis kritik` → Acil Servis'teki kritik ürünleri göster
- `ameliyathane stok` → Ameliyathane deposunun stok durumunu göster
- `ameliyathane kritik` → Ameliyathane'deki kritik ürünleri göster
- `yoğun bakım stok` → Yoğun Bakım deposunun stok durumunu göster
- `yoğun bakım kritik` → Yoğun Bakım'daki kritik ürünleri göster

**Not:** 
- Stok raporları gösterildikten sonra Excel, CSV formatında indirebilirsiniz
- Yeni depo ekledikten sonra aynı komutlar otomatik çalışır
- Örnek: "Radyoloji stok" → Radyoloji deposunun stokunu gösterir

**Örnekler:**
- "Merkez depo stok durumu görmek istiyorum" ✅
- "Faturalar" ✅
- "Depolar" ✅
- "TCMB kur" ✅
- "Acil servis kritik ürünler" ✅
- "Depo ekle" ✅ 🤖 YENİ!
"""
            st.session_state.chat_history.append({"role": "assistant", "content": komut_listesi})

        elif response_type == "redirect":
            st.session_state.chat_history.append({"role": "assistant", "content": response_data})
            st.rerun()

        elif response_type == "fatura_list":
            faturalar = response_data["faturalar"]
            baslik = response_data["baslik"]

            df = pd.DataFrame(faturalar)

            mesaj = f"### {baslik}\n\n✅ {len(faturalar)} adet fatura/irsaliye bulundu.\n\n📊 Aşağıda detaylı listeyi görebilir ve indirebilirsiniz:"

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": mesaj,
                "report_data": faturalar
            })

        elif response_type == "depo_list":
            depolar = response_data["depolar"]
            baslik = response_data["baslik"]

            df = pd.DataFrame(depolar)

            mesaj = f"### {baslik}\n\n✅ {len(depolar)} adet depo bulundu.\n\n📊 Aşağıda detaylı listeyi görebilirsiniz:"

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": mesaj,
                "report_data": depolar
            })

        elif response_type == "stock_report":
            rapor = response_data["rapor"]
            baslik = response_data["baslik"]

            df = pd.DataFrame(rapor)

            mesaj = f"### {baslik}\n\n✅ {len(rapor)} adet ürün bulundu.\n\n📊 Aşağıda LOT bilgileri ile birlikte detaylı raporu görebilir ve indirebilirsiniz:"

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": mesaj,
                "report_data": rapor
            })

        else:
            st.session_state.chat_history.append({"role": "assistant", "content": response_data})

        st.rerun()

elif st.session_state.current_page == "Documents":
    st.markdown("# 📄 Malzeme Fatura Girişi")

    # Merkez Depo kontrolü - yoksa oluştur
    merkez_depo_id = None
    for depo_id, depo_bilgi in st.session_state.data["depolar"].items():
        if "merkez" in depo_bilgi["ad"].lower():
            merkez_depo_id = depo_id
            break

    if not merkez_depo_id:
        # Merkez depo yoksa oluştur
        merkez_depo_id = f"DEP{len(st.session_state.data['depolar']) + 1:03d}"
        st.session_state.data["depolar"][merkez_depo_id] = {
            "ad": "Merkez Depo",
            "urunler": {}
        }
        veri_kaydet(st.session_state.data)

    if 'faturalar' not in st.session_state.data:
        st.session_state.data['faturalar'] = []

    if 'fatura_kalemleri' not in st.session_state:
        st.session_state.fatura_kalemleri = []

    # Üst bilgi kartı
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])

    with col_header1:
        st.markdown("### 🏭 Malzeme Fatura/İrsaliye Girişi")
        st.caption(f"📦 Merkez Depo: {st.session_state.data['depolar'][merkez_depo_id]['ad']}")

    with col_header2:
        if st.button("🔄 TCMB Kurlarını Güncelle", use_container_width=True):
            st.session_state.doviz_kurlari = tcmb_kur_cek()
            st.success("✅ Kurlar güncellendi!")
            st.rerun()

    with col_header3:
        kur_tarihi = st.session_state.doviz_kurlari.get('tarih', 'Bilinmiyor')
        st.info(f"📅 Kur Tarihi:\n{kur_tarihi}")

    # TCMB Kur Tablosu
    st.markdown("### 💱 TCMB Döviz Kurları (Alış)")
    col1, col2, col3 = st.columns(3)

    with col1:
        usd_kur = st.session_state.doviz_kurlari.get('USD', 0)
        st.metric("🇺🇸 USD/TRY", f"{usd_kur:.4f} ₺")

    with col2:
        eur_kur = st.session_state.doviz_kurlari.get('EUR', 0)
        st.metric("🇪🇺 EUR/TRY", f"{eur_kur:.4f} ₺")

    with col3:
        gbp_kur = st.session_state.doviz_kurlari.get('GBP', 0)
        st.metric("🇬🇧 GBP/TRY", f"{gbp_kur:.4f} ₺")

    st.markdown("---")

    # Fatura Başlık Bilgileri
    with st.form("fatura_baslik_form"):
        st.markdown("### 📋 Fatura Başlık Bilgileri")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            belge_tipi = st.selectbox("Belge Tipi", ["Fatura", "İrsaliye"])

        with col2:
            fatura_no = st.text_input("Fatura/İrsaliye No *", placeholder="F-2024-001")

        with col3:
            fatura_tarihi = st.date_input("Belge Tarihi *")

        with col4:
            tedarikci = st.text_input("Tedarikçi *", placeholder="ABC Tıbbi Malzeme Ltd.")

        baslik_kaydet = st.form_submit_button("✅ Başlık Bilgilerini Kaydet", type="primary")

        if baslik_kaydet:
            if fatura_no and tedarikci:
                st.session_state.fatura_baslik = {
                    'belge_tipi': belge_tipi,
                    'fatura_no': fatura_no,
                    'fatura_tarihi': str(fatura_tarihi),
                    'tedarikci': tedarikci
                }
                st.success(f"✅ {belge_tipi} başlık bilgileri kaydedildi!")
                st.rerun()
            else:
                st.error("❌ Fatura No ve Tedarikçi zorunludur!")

    # Fatura başlık kaydedilmişse malzeme ekleme göster
    if 'fatura_baslik' in st.session_state:
        st.markdown("---")

        # Kaydedilmiş başlık bilgisi
        st.info(
            f"📄 **{st.session_state.fatura_baslik['belge_tipi']}:** {st.session_state.fatura_baslik['fatura_no']} | "
            f"**Tedarikçi:** {st.session_state.fatura_baslik['tedarikci']} | "
            f"**Tarih:** {st.session_state.fatura_baslik['fatura_tarihi']}")

        # Malzeme Ekleme Formu
        with st.form("malzeme_ekle_form", clear_on_submit=True):
            st.markdown("### ➕ Malzeme Ekle")

            col1, col2 = st.columns(2)

            with col1:
                malzeme_adi = st.text_input("Malzeme Adı *", placeholder="Örn: Cerrahi Eldiven")
                lot_no = st.text_input("LOT Numarası", placeholder="LOT2024A",
                                       value=f"LOT{datetime.now().strftime('%Y%m%d')}")
                doviz = st.selectbox("Döviz Cinsi", ["TRY", "USD", "EUR", "GBP"])

            with col2:
                miktar = st.number_input("Miktar *", min_value=1, value=1, step=1)
                birim_fiyat = st.number_input(f"Birim Fiyat ({doviz}) *", min_value=0.0, value=0.0, step=0.01,
                                              format="%.2f")
                kdv_oran = st.selectbox("KDV Oranı (%)", [0, 1, 8, 10, 18, 20], index=5)

            # Hesaplamalar
            if birim_fiyat > 0 and miktar > 0:
                ara_toplam = birim_fiyat * miktar
                kdv_tutari = ara_toplam * (kdv_oran / 100)
                toplam = ara_toplam + kdv_tutari

                # TRY'ye çevir
                if doviz != "TRY":
                    kur = st.session_state.doviz_kurlari.get(doviz, 1)
                    ara_toplam_try = ara_toplam * kur
                    kdv_tutari_try = kdv_tutari * kur
                    toplam_try = toplam * kur
                else:
                    kur = 1
                    ara_toplam_try = ara_toplam
                    kdv_tutari_try = kdv_tutari
                    toplam_try = toplam

                # Hesaplama özeti
                st.markdown("#### 💰 Hesaplama")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Ara Toplam", f"{ara_toplam:.2f} {doviz}")
                    if doviz != "TRY":
                        st.caption(f"₺ {ara_toplam_try:,.2f}")

                with col2:
                    st.metric(f"KDV (%{kdv_oran})", f"{kdv_tutari:.2f} {doviz}")
                    if doviz != "TRY":
                        st.caption(f"₺ {kdv_tutari_try:,.2f}")

                with col3:
                    st.metric("Toplam", f"{toplam:.2f} {doviz}")
                    if doviz != "TRY":
                        st.caption(f"₺ {toplam_try:,.2f} (Kur: {kur:.4f})")

            malzeme_ekle = st.form_submit_button("➕ Malzemeyi Ekle", type="primary", use_container_width=True)

            if malzeme_ekle:
                if not malzeme_adi or birim_fiyat <= 0 or miktar <= 0:
                    st.error("❌ Malzeme adı, birim fiyat ve miktar zorunludur!")
                else:
                    # Malzemeyi listeye ekle
                    kalem = {
                        'malzeme_adi': malzeme_adi,
                        'lot_no': lot_no,
                        'miktar': miktar,
                        'doviz': doviz,
                        'birim_fiyat': birim_fiyat,
                        'ara_toplam': ara_toplam,
                        'kdv_oran': kdv_oran,
                        'kdv_tutari': kdv_tutari,
                        'toplam': toplam,
                        'kur': kur,
                        'ara_toplam_try': ara_toplam_try,
                        'kdv_tutari_try': kdv_tutari_try,
                        'toplam_try': toplam_try
                    }

                    st.session_state.fatura_kalemleri.append(kalem)
                    st.success(f"✅ {malzeme_adi} eklendi!")
                    st.rerun()

        # Eklenen Malzemeler Listesi
        if len(st.session_state.fatura_kalemleri) > 0:
            st.markdown("---")
            st.markdown("### 📦 Faturadaki Malzemeler")

            # Tablo oluştur
            df_kalemler = pd.DataFrame(st.session_state.fatura_kalemleri)

            # Gösterim için sütunları düzenle
            df_display = df_kalemler[
                ['malzeme_adi', 'lot_no', 'miktar', 'doviz', 'birim_fiyat', 'ara_toplam', 'kdv_oran', 'toplam',
                 'toplam_try']].copy()
            df_display.columns = ['Malzeme', 'LOT', 'Miktar', 'Döviz', 'Birim Fiyat', 'Ara Toplam', 'KDV %', 'Toplam',
                                  'Toplam (TRY)']

            st.dataframe(df_display, use_container_width=True)

            # Toplamlar
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                toplam_kalem = len(st.session_state.fatura_kalemleri)
                st.metric("📦 Toplam Kalem", toplam_kalem)

            with col2:
                toplam_miktar = df_kalemler['miktar'].sum()
                st.metric("📊 Toplam Miktar", int(toplam_miktar))

            with col3:
                genel_toplam = df_kalemler['toplam_try'].sum()
                st.metric("💰 Genel Toplam", f"₺ {genel_toplam:,.2f}")

            with col4:
                if st.button("🗑️ Listeyi Temizle", use_container_width=True):
                    st.session_state.fatura_kalemleri = []
                    st.rerun()

            # Faturayı Kaydet
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])

            with col2:
                if st.button("💾 Faturayı Kaydet ve Merkez Depoya Ekle", type="primary", use_container_width=True):
                    # Faturayı kaydet
                    yeni_fatura = {
                        'id': len(st.session_state.data.get('faturalar', [])) + 1,
                        'belge_tipi': st.session_state.fatura_baslik['belge_tipi'],
                        'fatura_no': st.session_state.fatura_baslik['fatura_no'],
                        'fatura_tarihi': st.session_state.fatura_baslik['fatura_tarihi'],
                        'tedarikci': st.session_state.fatura_baslik['tedarikci'],
                        'kalemler': st.session_state.fatura_kalemleri.copy(),
                        'toplam_kalem': len(st.session_state.fatura_kalemleri),
                        'genel_toplam_try': df_kalemler['toplam_try'].sum(),
                        'kayit_tarihi': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    st.session_state.data['faturalar'].append(yeni_fatura)

                    # Her malzemeyi Merkez Depo'ya ekle
                    eklenen_malzemeler = []

                    for kalem in st.session_state.fatura_kalemleri:
                        # Yeni ürün ID oluştur
                        urun_id = f"URN{len(st.session_state.data['urunler']) + 1:03d}"

                        # Barkod oluştur
                        barkod_no = ''.join([str(random.randint(0, 9)) for _ in range(12)])

                        # Ürünü sisteme ekle
                        st.session_state.data["urunler"][urun_id] = {
                            "ad": kalem['malzeme_adi'],
                            "barkod_tipi": "QR Kod",
                            "barkod_no": barkod_no,
                            "lot_no": kalem['lot_no'],
                            "lot_adet": kalem['miktar'],
                            "depo_id": merkez_depo_id,
                            "fatura_no": st.session_state.fatura_baslik['fatura_no'],
                            "birim_fiyat": kalem['birim_fiyat'],
                            "doviz": kalem['doviz']
                        }

                        # Merkez Depo'ya ekle
                        st.session_state.data["depolar"][merkez_depo_id]["urunler"][urun_id] = {
                            "miktar": kalem['miktar'],
                            "kritik_seviye": int(kalem['miktar'] * 0.1),  # %10
                            "min_seviye": int(kalem['miktar'] * 0.2),  # %20
                            "max_seviye": int(kalem['miktar'] * 2)  # 2x
                        }

                        eklenen_malzemeler.append(f"✅ {kalem['malzeme_adi']} ({kalem['miktar']} adet) - {urun_id}")

                    # Kaydet
                    veri_kaydet(st.session_state.data)

                    # Başarı mesajı
                    st.success("### 🎉 İşlem Başarılı!")
                    st.success(f"📄 Fatura kaydedildi: {st.session_state.fatura_baslik['fatura_no']}")
                    st.success(f"📦 {len(eklenen_malzemeler)} malzeme Merkez Depo'ya eklendi:")
                    for mal in eklenen_malzemeler:
                        st.write(mal)

                    # Temizle
                    st.session_state.fatura_kalemleri = []
                    del st.session_state.fatura_baslik

                    st.balloons()

                    # 3 saniye bekle ve yenile
                    import time

                    time.sleep(2)
                    st.rerun()

    # Kayıtlı Faturalar
    if len(st.session_state.data.get('faturalar', [])) > 0:
        st.markdown("---")
        st.markdown("### 📊 Kayıtlı Faturalar")

        faturalar_ozet = []
        for fatura in st.session_state.data['faturalar']:
            faturalar_ozet.append({
                'Belge Tipi': fatura['belge_tipi'],
                'Fatura No': fatura['fatura_no'],
                'Tarih': fatura['fatura_tarihi'],
                'Tedarikçi': fatura['tedarikci'],
                'Kalem Sayısı': fatura['toplam_kalem'],
                'Toplam (TRY)': f"₺ {fatura['genel_toplam_try']:,.2f}",
                'Kayıt Tarihi': fatura['kayit_tarihi']
            })

        df_faturalar = pd.DataFrame(faturalar_ozet)
        st.dataframe(df_faturalar, use_container_width=True, height=300)

        # Excel indirme
        col1, col2 = st.columns(2)

        with col1:
            excel_data = excel_olustur(df_faturalar, "fatura_listesi.xlsx")
            st.download_button(
                label="📊 Excel İndir",
                data=excel_data,
                file_name=f"fatura_listesi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            toplam_fatura_degeri = sum([f['genel_toplam_try'] for f in st.session_state.data['faturalar']])
            st.metric("💰 Toplam Fatura Değeri", f"₺ {toplam_fatura_degeri:,.2f}")

else:
    st.markdown(f"# {st.session_state.current_page}")
    st.info(f"{st.session_state.current_page} sayfası yapım aşamasında...")

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666; font-size: 12px;'>© {datetime.now().year} Hastane Depo Yönetim Sistemi. Tüm hakları saklıdır.</div>",
    unsafe_allow_html=True
)
