import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Dashboard Weekly Performance", layout="wide")
st.title("Weekly Training + Test vs League Match U16")

# ================== 1. CARICAMENTO FILE ==================
PATH_FILE = "Dataset_combinato_GPS_finale.xlsx"  # file in the same directory

if os.path.exists(PATH_FILE):
    df_raw = pd.read_excel(PATH_FILE)
    st.success(f"File '{PATH_FILE}' caricato con successo!")
else:
    st.warning(f"File '{PATH_FILE}' non trovato. Mettilo nella stessa cartella dell'app.")
    st.stop()

# ================== 2. PREPARAZIONE DATI ==================
df_raw['Data'] = pd.to_datetime(df_raw['Data'])

mask_match_valid = (
    (df_raw['Competition'].isin(['League', 'Test Match'])) &
    (df_raw['Time'] == 'Full Match')
)
mask_training = df_raw['Competition'] == 'Full Training'

df = df_raw[mask_match_valid | mask_training].copy()
df = df.sort_values('Data')

df_team_avg = df[df['PLAYER'] == 'Team Average'].copy()

players = [p for p in df['PLAYER'].dropna().unique().tolist() if p != 'Team Average']
players.insert(0, 'Team Average')

metriche = [m for m in df.select_dtypes(include='number').columns.tolist() if m != 'Vel Max']

# ================== 3. SIDEBAR CONTROLLI ==================
st.sidebar.header("Filtri")
giocatore = st.sidebar.selectbox("Giocatore", players)
metrica = st.sidebar.selectbox("Metrica", metriche)

# ================== 4. PREPARAZIONE SETTIMANALE ==================
df_weekly = df[df['PLAYER'] == giocatore].copy()
df_weekly['Week'] = df_weekly['Data'].dt.to_period('W').apply(lambda r: r.start_time)

df_training = df_weekly[df_weekly['Competition'] == 'Full Training']
df_league = df_weekly[df_weekly['Competition'] == 'League']
df_test = df_weekly[df_weekly['Competition'] == 'Test Match']
df_train_test = pd.concat([df_training, df_test])

# ================== 5. AGGREGAZIONE DATI ==================
train_agg = df_train_test.groupby('Week')[metrica].sum().reset_index()
league_agg = df_league.groupby('Week').agg({metrica: 'sum', 'Opponent': 'first'}).reset_index()

ratio_texts = []
for week in train_agg['Week']:
    train_val = train_agg.loc[train_agg['Week'] == week, metrica].values[0]
    league_row = league_agg.loc[league_agg['Week'] == week, metrica]

    if not league_row.empty and league_row.values[0] > 0:
        ratio_texts.append(f"{train_val / league_row.values[0]:.2f}x")
    else:
        ratio_texts.append("")

# ================== 6. GRAFICO ==================
fig_week = go.Figure()

fig_week.add_trace(go.Bar(
    x=train_agg['Week'],
    y=train_agg[metrica],
    name='Full Training + Test',
    marker_color='rgba(0,180,0,0.85)',
    text=ratio_texts,
    textposition='inside',
    insidetextanchor='middle',
    textfont=dict(color='white', size=11)
))

fig_week.add_trace(go.Bar(
    x=league_agg['Week'],
    y=league_agg[metrica],
    name='League Match',
    marker_color='rgba(255,0,0,0.85)',
    text=league_agg['Opponent'],
    textposition='inside',
    insidetextanchor='middle',
    textfont=dict(color='white', size=11)
))

fig_week.update_layout(
    title=f"{metrica} - Weekly Training + Test vs League Match ({giocatore})",
    barmode='group',
    hovermode='x unified',
    template='plotly_white',
    xaxis=dict(
        type="date",
        dtick="M1",
        tickformat="%b %Y",
        rangeslider=dict(visible=True)
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_week, use_container_width=True)
