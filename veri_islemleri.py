

import json

def veri_kaydet(dosya_adi, veri):
    """Veriyi JSON dosyasına kaydet"""
    try:
        with open(dosya_adi, 'w', encoding='utf-8') as dosya:
            json.dump(veri, dosya, ensure_ascii=False, indent=4)
        return True
    except:
        return False

def veri_yukle(dosya_adi):
    """JSON dosyasından veri yükle"""
    try:
        with open(dosya_adi, 'r', encoding='utf-8') as dosya:
            return json.load(dosya)
    except:
        return None

def ilk_veri_olustur():
    """Program ilk çalıştığında boş yapı oluştur"""
    return {
        "urunler": {},
        "depolar": {}
    }