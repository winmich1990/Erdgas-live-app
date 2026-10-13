import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Erdgas Trading App", page_icon="🔥", layout="centered"
)

st.title("🔥 Erdgas (Natural Gas) Chart & Signal")

# --- ZEITRAUM UND INTERVALL WAHL ---
timeframe = st.selectbox(
    "Zeiteinheit wählen:",
    (
        "15-Minuten-Chart (15m)",
        "Stundenchart (1H)",
        "Wochenchart (1W)",
        "Monatschart (1M)",
    ),
)

# Parameter je nach Auswahl festlegen
if timeframe == "15-Minuten-Chart (15m)":
  period = "30d"
  interval = "15m"
elif timeframe == "Stundenchart (1H)":
  period = "59d"
  interval = "1h"
elif timeframe == "Wochenchart (1W)":
  period = "2y"
  interval = "1wk"
else:  # Monatschart
  period = "5y"
  interval = "1mo"


# Daten laden
@st.cache_data(ttl=300)
def load_data(p, i):
  data = yf.download("NG=F", period=p, interval=i, progress=False)
  if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
  return data


with st.spinner("Lade Chartdaten..."):
  df = load_data(period, interval)

if df.empty or len(df) < 50:
  st.error(
      "Nicht genügend Daten für die Berechnung geladen. Bitte wähle einen"
      " anderen Zeitraum."
  )
else:
  # Letzte genaue Aktualisierungszeit ermitteln
  last_timestamp = df.index[-1].strftime("%d.%m.%Y %H:%M")

  # --- INDIKATOREN BERECHNEN ---
  df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()

  window = 14
  delta = df["Close"].diff()
  gain = delta.where(delta > 0, 0).rolling(window=window).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
  rs = gain / loss
  df["RSI"] = 100 - (100 / (1 + rs))

  current_price = df["Close"].iloc[-1]
  current_rsi = df["RSI"].iloc[-1]
  current_ema = df["EMA_50"].iloc[-1]

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

  # Key Metrics anzeigen
  col1, col2, col3 = st.columns(3)
  col1.metric("Preis (USD)", f"{current_price:.3f}")
  col2.metric("RSI (14)", f"{current_rsi:.2f}")
  col3.metric("EMA 50", f"{current_ema:.3f}")

  st.caption(f"Letzter Datenpunkt: {last_timestamp}")

  st.markdown(
      f"""
        <div style="background-color: {box_color}; color: {text_color}; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 20px;">
            Empfehlung: {signal}
        </div>
        """,
      unsafe_allow_html=True,
  )

  # --- KERZENCHART & RSI GRAFIK (PLOTLY) ---
  fig = make_subplots(
      rows=2,
      cols=1,
      shared_xaxes=True,
      vertical_spacing=0.05,
      row_heights=[0.7, 0.3],
      subplot_titles=("Candlestick & EMA 50", "RSI (14)"),
  )

  # 1. Kerzenchart (Candlestick)
  fig.add_trace(
      go.Candlestick(
          x=df.index,
          open=df["Open"],
          high=df["High"],
          low=df["Low"],
          close=df["Close"],
          name="Erdgas Kerzen",
      ),
      row=1,
      col=1,
  )

  # 2. EMA 50 Linie
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["EMA_50"],
          mode="lines",
          name="EMA 50",
          line=dict(color="orange", width=1.5),
      ),
      row=1,
      col=1,
  )

  # 3. RSI Linie
  fig.add_trace(
      go.Scatter(
          x=df.index,
          y=df["RSI"],
          mode="lines",
          name="RSI 14",
          line=dict(color="purple", width=1.5),
      ),
      row=2,
      col=1,
  )

  # RSI Überkauft / Überverkauft Linien (30 und 70)
  fig.add_hline(
      y=70, line_dash="dash", line_color="red", row=2, col=1, opacity=0.5
  )
  fig.add_hline(
      y=30, line_dash="dash", line_color="green", row=2, col=1, opacity=0.5
  )

  # Layout-Anpassung
  fig.update_layout(
      height=600,
      xaxis_rangeslider_visible=False,
      margin=dict(l=10, r=10, t=30, b=10),
  )

  st.plotly_chart(fig, use_container_width=True)
