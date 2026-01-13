import streamlit as st
import pandas as pd
from supabase import create_client, Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- KONFIGURACJA POŁĄCZENIA ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Błąd konfiguracji Secrets. Sprawdź SUPABASE_URL i SUPABASE_KEY.")
    st.stop()

st.set_page_config(page_title="System Magazynowy Pro", layout="wide", page_icon="📦")

# --- STYLE CSS DLA KART ---
st.markdown("""
    <style>
    .product-card {
        border: 1px solid #e6e9ef;
        border-radius: 10px;
        padding: 20px;
        background-color: #ffffff;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .status-badge {
        padding: 4px 8px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 0.8em;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNKCJE POWIADOMIEŃ ---
def send_email_alert(recipient_email, low_stock_items):
    smtp_server, smtp_port = "smtp.gmail.com", 587
    sender_email = st.secrets.get("EMAIL_SENDER")
    sender_pw = st.secrets.get("EMAIL_PASSWORD")

    if not sender_email or not sender_pw:
        st.error("Brak konfiguracji email w Secrets!")
        return

    msg = MIMEMultipart()
    msg['Subject'] = "⚠️ Alert Magazynowy"
    body = "Niskie stany produktów:\n\n" + "\n".join([f"- {i['nazwa']}: {i['liczba']} szt." for i in low_stock_items])
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_pw)
        server.send_message(msg)
        server.quit()
        st.success("📧 Alert wysłany!")
    except Exception as e:
        st.error(f"Błąd wysyłki: {e}")

# --- POBIERANIE DANYCH ---
def fetch_data():
    p = supabase.table("produkty").select("*").execute()
    k = supabase.table("kategorie").select("*").execute()
    return p.data, k.data

prods, kats = fetch_data()
k_map = {k['id']: k['nazwa'] for k in kats}

# --- NAWIGACJA ---
st.sidebar.title("📦 Magazyn v2.0")
prog = st.sidebar.slider("Próg niskiego stanu", 0, 50, 5)
st.session_state.threshold = prog

menu = st.sidebar.radio("Nawigacja:", [
    "🖼️ Podgląd Magazynu", 
    "📊 Statystyki", 
    "🍎 Lista i Edycja", 
    "📂 Kategorie",
    "⚙️ Konfiguracja"
])

# --- 1. WIZUALNY PODGLĄD MAGAZYNU (NOWOŚĆ) ---
if menu == "🖼️ Podgląd Magazynu":
    st.title("🖼️ Podgląd Wizualny")
    
    col_search, col_filter = st.columns([2, 1])
    search = col_search.text_input("🔍 Szukaj produktu...")
    
    # Filtrowanie
    display_items = [p for p in prods if search.lower() in p['nazwa'].lower()]
    
    # Wyświetlanie w siatce (grid)
    cols = st.columns(3) # 3 karty w rzędzie
    for idx, item in enumerate(display_items):
        with cols[idx % 3]:
            # Logika statusu
            if item['liczba'] == 0:
                status, color = "BRAK", "#ff4b4b"
                icon = "🔴"
            elif item['liczba'] <= st.session_state.threshold:
                status, color = "NISKI STAN", "#ffa500"
                icon = "🟡"
            else:
                status, color = "DOSTĘPNY", "#28a745"
                icon = "🟢"

            # Renderowanie karty
            st.markdown(f"""
                <div class="product-card">
                    <h3 style="margin-top:0;">{item['nazwa']}</h3>
                    <p><b>Kategoria:</b> {k_map.get(item['kategoria_id'], 'Brak')}</p>
                    <p><b>Cena:</b> {item['cena']} zł</p>
                    <hr>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.2em;">Ilość: <b>{item['liczba']}</b></span>
                        <span style="background-color: {color}; color: white;" class="status-badge">{status} {icon}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- 2. STATYSTYKI ---
elif menu == "📊 Statystyki":
    st.title("📊 Analityka")
    if prods:
        df = pd.DataFrame(prods)
        low_stock = [p for p in prods if p['liczba'] <= st.session_state.threshold]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Unikalne produkty", len(prods))
        c2.metric("Wartość towaru", f"{(df['liczba'] * df['cena'].astype(float)).sum():,.2f} zł")
        c3.metric("Do uzupełnienia", len(low_stock))

        st.subheader("Bieżące braki")
        if low_stock:
            st.warning(f"Znaleziono {len(low_stock)} pozycji do zamówienia.")
            if st.button("📩 Wyślij listę zakupową na email"):
                send_email_alert(st.secrets.get("EMAIL_RECEIVER"), low_stock)
        else:
            st.success("Stany magazynowe są wystarczające.")

# --- 3. LISTA I EDYCJA ---
elif menu == "🍎 Lista i Edycja":
    st.title("📝 Zarządzanie Danymi")
    
    with st.expander("➕ Dodaj nowy produkt"):
        with st.form("new_p"):
            n = st.text_input("Nazwa")
            k_id = st.selectbox("Kategoria", list(k_map.keys()), format_func=lambda x: k_map[x])
            c_l, c_c = st.columns(2)
            l = c_l.number_input("Ilość", 0)
            c = c_c.number_input("Cena (zł)", 0.0)
            if st.form_submit_button("Zatwierdź"):
                supabase.table("produkty").insert({"nazwa": n, "kategoria_id": k_id, "liczba": l, "cena": c}).execute()
                st.rerun()

    if prods:
        st.subheader("Edytuj istniejące produkty")
        for p in prods:
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            c1.write(f"**{p['nazwa']}**")
            new_val = c2.number_input("Ilość", value=int(p['liczba']), key=f"ed_{p['id']}")
            if new_val != p['liczba']:
                if c3.button("Zapisz", key=f"save_{p['id']}"):
                    supabase.table("produkty").update({"liczba": new_val}).eq("id", p['id']).execute()
                    st.rerun()
            if c4.button("🗑️", key=f"del_{p['id']}"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()
            st.divider()

# --- 4. KATEGORIE ---
elif menu == "📂 Kategorie":
    st.title("📂 Kategorie")
    with st.form("k_f"):
        kn = st.text_input("Nowa kategoria")
        ko = st.text_area("Opis")
        if st.form_submit_button("Dodaj"):
            supabase.table("kategorie").insert({"nazwa": kn, "opis": ko}).execute()
            st.rerun()
    
    if kats:
        st.table(pd.DataFrame(kats)[['nazwa', 'opis']])

# --- 5. KONFIGURACJA ---
elif menu == "⚙️ Konfiguracja":
    st.header("Ustawienia systemowe")
    st.write("Wersja bazy danych: Supabase Postgres")
    st.write("Status połączenia: ✅ Połączono")
    st.info("Dane dostępowe (URL/KEY/EMAIL) należy konfigurować w panelu Streamlit Cloud (Secrets).")
