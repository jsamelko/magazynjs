import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd konfiguracji Secrets. Sprawdź SUPABASE_URL i SUPABASE_KEY.")
    st.stop()

st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")
st.title("📦 System Zarządzania Magazynem")

# Menu boczne
menu = st.sidebar.selectbox("Nawigacja", ["Kategorie", "Produkty"])

# --- SEKCJA: KATEGORIE ---
if menu == "Kategorie":
    st.header("📂 Kategorie produktów")
    
    # Formularz dodawania kategorii
    with st.form("form_kat"):
        st.subheader("Dodaj nową kategorię")
        nazwa = st.text_input("Nazwa kategorii")
        opis = st.text_area("Opis (opcjonalnie)")
        submit_kat = st.form_submit_button("Zapisz kategorię")
        
        if submit_kat:
            if nazwa:
                # LINIA 33: Poprawione wywołanie insert z obsługą błędu
                try:
                    supabase.table("kategorie").insert({"nazwa": nazwa, "opis": opis}).execute()
                    st.success(f"Dodano kategorię: {nazwa}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd podczas dodawania: {e}")
            else:
                st.warning("Nazwa kategorii jest wymagana.")

    st.divider()

    # Wyświetlanie listy kategorii
    st.subheader("Lista dostępnych kategorii")
    kat_resp = supabase.table("kategorie").select("*").order("id").execute()
    
    if kat_resp.data:
        for kat in kat_resp.data:
            col1, col2 = st.columns([5, 1])
            col1.write(f"**{kat['nazwa']}** — {kat['opis'] if kat['opis'] else 'Brak opisu'}")
            
            # LINIA 53: Poprawione wywołanie delete z obsługą relacji klucza obcego
            if col2.button("Usuń", key=f"del_kat_{kat['id']}"):
                try:
                    supabase.table("kategorie").delete().eq("id", kat['id']).execute()
                    st.success("Usunięto kategorię.")
                    st.rerun()
                except Exception:
                    st.error("Nie można usunąć! Kategoria jest używana przez produkty.")
    else:
        st.info("Brak kategorii w bazie.")

# --- SEKCJA: PRODUKTY ---
elif menu == "Produkty":
    st.header("🍎 Produkty w magazynie")
    
    # Pobranie danych o kategoriach do dropdowna
    kat_resp = supabase.table("kategorie").select("id, nazwa").execute()
    kategorie_mapa = {k['id']: k['nazwa'] for k in kat_resp.data}
    opcje_kat = {k['nazwa']: k['id'] for k in kat_resp.data}

    # Formularz dodawania produktu
    if not opcje_kat:
        st.warning("Najpierw dodaj przynajmniej jedną kategorię!")
    else:
        with st.form("form_prod"):
            st.subheader("Dodaj nowy produkt")
            col_a, col_b = st.columns(2)
            nazwa_p = col_a.text_input("Nazwa produktu")
            kat_p = col_a.selectbox("Kategoria", options=list(opcje_kat.keys()))
            liczba_p = col_b.number_input("Ilość (szt.)", min_value=0, step=1)
            cena_p = col_b.number_input("Cena (zł)", min_value=0.0, format="%.2f")
            
            submit_prod = st.form_submit_button("Dodaj do bazy")
            
            if submit_prod and nazwa_p:
                payload = {
                    "nazwa": nazwa_p,
                    "liczba": liczba_p,
                    "cena": cena_p,
                    "kategoria_id": opcje_kat[kat_p]
                }
                supabase.table("produkty").insert(payload).execute()
                st.success(f"Dodano produkt: {nazwa_p}")
                st.rerun()

    st.divider()

    # Wyświetlanie listy produktów
    st.subheader("Aktualny stan magazynowy")
    prod_resp = supabase.table("produkty").select("*").order("id").execute()

    if prod_resp.data:
        h1, h2, h3, h4, h5 = st.columns([3, 2, 1, 1, 1])
        h1.write("**Nazwa**")
        h2.write("**Kategoria**")
        h3.write("**Ilość**")
        h4.write("**Cena**")
        h5.write("**Akcja**")
        
        for prod in prod_resp.data:
            c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 1, 1])
            c1.write(prod['nazwa'])
            nazwa_kategorii = kategorie_mapa.get(prod['kategoria_id'], "Nieznana")
            c2.write(nazwa_kategorii)
            c3.write(str(prod['liczba']))
            c4.write(f"{prod['cena']} zł")
            
            if c5.button("Usuń", key=f"del_prod_{prod['id']}"):
                supabase.table("produkty").delete().eq("id", prod['id']).execute()
                st.rerun()
    else:
        st.info("Magazyn jest pusty.")
