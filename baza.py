import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# Dane powinny być przechowywane w Streamlit Secrets
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📦 Zarządzanie Magazynem")

# Menu boczne do nawigacji
menu = st.sidebar.selectbox("Wybierz tabelę", ["Kategorie", "Produkty"])

# --- SEKCJA: KATEGORIE ---
if menu == "Kategorie":
    st.header("📂 Zarządzanie Kategoriami")
    
    # Formularz dodawania
    with st.form("add_category_form"):
        st.subheader("Dodaj nową kategorię")
        nazwa = st.text_input("Nazwa kategorii")
        opis = st.text_area("Opis")
        submit = st.form_submit_button("Dodaj kategorię")
        
        if submit and nazwa:
            data, count = supabase.table("kategorie").insert({"nazwa": nazwa, "opis": opis}).execute()
            st.success(f"Dodano kategorię: {nazwa}")
            st.rerun()

    # Wyświetlanie i usuwanie
    st.subheader("Lista kategorii")
    kategorie = supabase.table("kategorie").select("*").execute()
    
    if kategorie.data:
        for kat in kategorie.data:
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{kat['nazwa']}** - {kat['opis']}")
            if col2.button("Usuń", key=f"kat_{kat['id']}"):
                supabase.table("kategorie").delete().eq("id", kat['id']).execute()
                st.rerun()
    else:
        st.info("Brak kategorii w bazie.")

# --- SEKCJA: PRODUKTY ---
elif menu == "Produkty":
    st.header("🍎 Zarządzanie Produktami")
    
    # Pobranie kategorii do listy rozwijanej
    kat_data = supabase.table("kategorie").select("id, nazwa").execute()
    kat_options = {kat['nazwa']: kat['id'] for kat in kat_data.data}

    # Formularz dodawania
    if not kat_options:
        st.warning("Najpierw dodaj przynajmniej jedną kategorię!")
    else:
        with st.form("add_product_form"):
            st.subheader("Dodaj nowy produkt")
            nazwa_prod = st.text_input("Nazwa produktu")
            liczba = st.number_input("Ilość", min_value=0, step=1)
            cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            kat_nazwa = st.selectbox("Kategoria", options=list(kat_options.keys()))
            
            submit_prod = st.form_submit_button("Dodaj produkt")
            
            if submit_prod and nazwa_prod:
                new_prod = {
                    "nazwa": nazwa_prod,
                    "liczba": liczba,
                    "cena": cena,
                    "kategoria_id": kat_options[kat_nazwa]
                }
                supabase.table("produkty").insert(new_prod).execute()
                st.success(f"Dodano produkt: {nazwa_prod}")
                st.rerun()

    # Wyświetlanie i usuwanie
    st.subheader("Lista produktów")
    # Pobieramy produkty wraz z nazwami kategorii (Join)
    produkty = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    
    if produkty.data:
        for prod in produkty.data:
            col1, col2 = st.columns([4, 1])
            kat_label = prod['kategorie']['nazwa'] if prod['kategorie'] else "Brak"
            col1.write(f"**{prod['nazwa']}** | Ilość: {prod['liczba']} | Cena: {prod['cena']} zł | Kat: {kat_label}")
            if col2.button("Usuń", key=f"prod_{prod['id']}"):
                supabase.table("produkty").delete().eq("id", prod['id']).execute()
                st.rerun()
    else:
        st.info("Brak produktów w bazie.")
