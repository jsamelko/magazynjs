import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Błąd konfiguracji Secrets. Sprawdź ustawienia.")
    st.stop()

st.set_page_config(page_title="Pro Magazyn", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def get_categories():
    res = supabase.table("kategorie").select("*").order("nazwa").execute()
    return res.data

def get_products():
    res = supabase.table("produkty").select("*").order("nazwa").execute()
    return res.data

# --- SIDEBAR / NAWIGACJA ---
st.sidebar.title("🎮 Panel Sterowania")
menu = st.sidebar.radio("Przejdź do:", ["📊 Dashboard", "📂 Kategorie", "🍎 Produkty", "✏️ Edycja i Zapasy"])

# --- 1. DASHBOARD (ANALITYKA) ---
if menu == "📊 Dashboard":
    st.title("📈 Analityka Magazynu")
    prods = get_products()
    kats = get_categories()
    
    if prods:
        df = pd.DataFrame(prods)
        total_items = df['liczba'].sum()
        # Obliczanie wartości: liczba * cena
        df['wartosc'] = df['liczba'] * df['cena'].astype(float)
        total_value = df['wartosc'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Liczba produktów", len(df))
        col2.metric("Suma sztuk w magazynie", f"{total_items:.0f}")
        col3.metric("Całkowita wartość", f"{total_value:,.2f} zł")
        
        st.subheader("📦 Stan zapasów na wykresie")
        st.bar_chart(df.set_index('nazwa')['liczba'])
    else:
        st.info("Brak danych do wyświetlenia analityki.")

# --- 2. KATEGORIE ---
elif menu == "📂 Kategorie":
    st.header("Zarządzanie Kategoriami")
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("form_kat"):
            n = st.text_input("Nazwa")
            o = st.text_area("Opis")
            if st.form_submit_button("Zapisz"):
                if n:
                    supabase.table("kategorie").insert({"nazwa": n, "opis": o}).execute()
                    st.success("Dodano!")
                    st.rerun()

    kats = get_categories()
    if kats:
        st.table(pd.DataFrame(kats)[['nazwa', 'opis']])

# --- 3. PRODUKTY (PRZEGLĄDANIE I WYSZUKIWANIE) ---
elif menu == "🍎 Produkty":
    st.header("Przegląd Produktów")
    
    # Filtry i wyszukiwanie
    col_f1, col_f2 = st.columns([2, 1])
    search = col_f1.text_input("🔍 Szukaj produktu po nazwie...")
    
    prods = get_products()
    kats = get_categories()
    mapa_kats = {k['id']: k['nazwa'] for k in kats}
    
    if prods:
        df = pd.DataFrame(prods)
        df['kategoria'] = df['kategoria_id'].map(mapa_kats)
        
        # Filtrowanie w Pandas
        if search:
            df = df[df['nazwa'].str.contains(search, case=False)]
            
        st.dataframe(df[['nazwa', 'kategoria', 'liczba', 'cena']], use_container_width=True)
        
        # Eksport do CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Pobierz listę (CSV)", csv, "magazyn.csv", "text/csv")

# --- 4. EDYCJA I ZAPASY (ZAAWANSOWANE) ---
elif menu == "✏️ Edycja i Zapasy":
    st.header("Szybka edycja stanów")
    prods = get_products()
    
    if prods:
        for p in prods:
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                c1.write(f"**{p['nazwa']}**")
                
                # Inline update liczby
                nowa_liczba = c2.number_input("Ilość", value=int(p['liczba']), key=f"n_{p['id']}")
                if nowa_liczba != p['liczba']:
                    if c2.button("Aktualizuj", key=f"btn_n_{p['id']}"):
                        supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", p['id']).execute()
                        st.rerun()
                
                # Usuwanie
                if c4.button("🗑️", key=f"del_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
                st.divider()
    else:
        st.info("Brak produktów do edycji.")

    # Formularz dodawania na dole
    st.subheader("➕ Dodaj nowy produkt")
    kats = get_categories()
    if kats:
        with st.form("new_p"):
            c_n = st.text_input("Nazwa")
            c_k = st.selectbox("Kategoria", options=[k['id'] for k in kats], format_func=lambda x: next(i['nazwa'] for i in kats if i['id'] == x))
            col_x, col_y = st.columns(2)
            c_l = col_x.number_input("Ilość", min_value=0)
            c_c = col_y.number_input("Cena", min_value=0.0)
            if st.form_submit_button("Dodaj produkt"):
                supabase.table("produkty").insert({"nazwa": c_n, "kategoria_id": c_k, "liczba": c_l, "cena": c_c}).execute()
                st.rerun()
