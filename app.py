import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yfinance as yf

# --- ZUGANGSDATEN ---
names = ["Dein Name"]
usernames = ["admin"]
passwords = ["dein_sicheres_passwort"]  # Hier dein Wunsch-Passwort eintragen

authenticator = stauth.Authenticate(
    names,
    usernames,
    passwords,
    cookie_name="erdgas_app_cookie",
    key="random_signature_key",
    cookie_expiry_days=30,
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
  st.error("Falscher Benutzername oder falsches Passwort!")

if authentication_status == None:
  st.warning("Bitte logge dich ein, um die App zu nutzen.")

# --- HAUPTAPP ---
if authentication_status == True:
  authenticator.logout("Abmelden", "sidebar")
  st.sidebar.write(
      f"Eingeloggt als: **{name}** (Absolut privat nur für dich 🔒)"
  )

  st.title("🔥 Erdgas (Natural Gas) Indikator")
  st.write("Echtzeit-Signal für den NYMEX Future")


  # Daten laden
  @st.cache_data(ttl=3600)
  def load_data():
    data = yf.download("NG=F", period="6mo", interval="1d", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
      data.columns = data.columns.get_level_values(0)
    return data


  with st.spinner("Lade Marktdaten..."):
    df = load_data()

  if df.empty:
    st.error("Fehler beim Laden der Daten.")
  else:
    # RSI berechnen
    window = 14
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    current_price = df["Close"].iloc[-1]
    current_rsi = df["RSI"].iloc[-1]

    # Signal bestimmen
    if current_rsi < 30:
      signal = "KAUFEN (Überverkauft)"
      box_color = "#d4edda"
      text_color = "#155724"
    elif current_rsi > 70:
      signal = "VERKAUFEN (Überkauft)"
      box_color = "#f8d7da"
      text_color = "#721c24"
    else:
      signal = "WARTEN (Neutraler Bereich)"
      box_color = "#fff3cd"
      text_color = "#856404"

    # Anzeige in der App
    col1, col2 = st.columns(2)
    col1.metric("Preis (USD)", f"{current_price:.3f}")
    col2.metric("RSI (14)", f"{current_rsi:.2f}")

    st.markdown(
        f"""
        <div style="background-color: {box_color}; color: {text_color}; padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 20px; margin-top: 20px;">
            Empfehlung: {signal}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Chart anzeigen
    st.subheader("Preisverlauf")
    st.line_chart(df["Close"])
