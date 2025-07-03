import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import uuid

# --- Charge les données et sessionisation ---
@st.cache_data
def load_data(path='app.json'):
    df = pd.read_json(path)
    # conversion timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['user_id', 'timestamp']).reset_index(drop=True)
    # extraire date et heure
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    # extraire pays
    df['country'] = df['geo'].apply(lambda g: g.get('country') if isinstance(g, dict) else 'Unknown')
    # sessionisation par login/logout ou timeout
    sessions = []
    for user, group in df.groupby('user_id'):
        sess_id = None
        for _, row in group.iterrows():
            if row['event_type'] == 'login':
                sess_id = str(uuid.uuid4())
            sessions.append(sess_id)
            if row['event_type'] == 'logout':
                sess_id = None
    df['session_id'] = sessions
    return df

df = load_data()

st.title("Analyse exploratoire des logs e-commerce")

# --- Filtres ---
st.sidebar.header("Filtres")
# Plage de dates
date_min, date_max = df['date'].min(), df['date'].max()
date_range = st.sidebar.date_input("Sélectionnez la plage de dates", [date_min, date_max], min_value=date_min, max_value=date_max)
# Types d'événements
event_types = df['event_type'].unique().tolist()
selected_events = st.sidebar.multiselect("Types d'événements", event_types, default=event_types)
# Pays
countries = df['country'].unique().tolist()
selected_countries = st.sidebar.multiselect("Pays", countries, default=countries)
# Device
devices = df['device_type'].unique().tolist()
selected_devices = st.sidebar.multiselect("Devices", devices, default=devices)

# Appliquer filtres
df_f = df[
    (df['date'] >= date_range[0]) & (df['date'] <= date_range[1]) &
    (df['event_type'].isin(selected_events)) &
    (df['country'].isin(selected_countries)) &
    (df['device_type'].isin(selected_devices))
]

st.markdown(f"**Logs filtrés :** {len(df_f)} enregistrements")

# --- Graphiques ---
# 1. Répartition événements par type
evt_count = df_f['event_type'].value_counts().reset_index()
evt_count.columns = ['event_type', 'count']
fig1 = px.bar(evt_count, x='event_type', y='count', title='Événements par type')
st.plotly_chart(fig1, use_container_width=True)

# 2. Évolution par heure
time_count = df_f.groupby('hour').size().reset_index(name='count')
fig2 = px.line(time_count, x='hour', y='count', markers=True, title='Événements par heure')
st.plotly_chart(fig2, use_container_width=True)

# 3. Évolution par jour
daily_count = df_f.groupby('date').size().reset_index(name='count')
fig3 = px.line(daily_count, x='date', y='count', markers=True, title='Événements par jour')
st.plotly_chart(fig3, use_container_width=True)

# 4. Top 10 produits vus
prod_views = df_f[df_f['event_type']=='product_view']
top_products = prod_views['data'].apply(lambda d: d.get('product_id')).value_counts().nlargest(10).reset_index()
top_products.columns = ['product_id', 'views']
fig4 = px.bar(top_products, x='product_id', y='views', title='Top 10 produits vus')
st.plotly_chart(fig4, use_container_width=True)

# 5. Histogramme des montants d'achats
purchases = df_f[df_f['event_type']=='purchase']
if not purchases.empty:
    purchases['amount'] = purchases['data'].apply(lambda d: d.get('amount', 0))
    fig5 = px.histogram(purchases, x='amount', nbins=20, title='Distribution des montants')
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Aucun achat")

# 6. Répartition géographique
country_count = df_f['country'].value_counts().reset_index()
country_count.columns = ['country', 'count']
fig6 = px.pie(country_count, names='country', values='count', title='Par pays')
st.plotly_chart(fig6, use_container_width=True)

# 7. Répartition par device
device_count = df_f['device_type'].value_counts().reset_index()
device_count.columns = ['device_type', 'count']
fig7 = px.pie(device_count, names='device_type', values='count', title='Par device')
st.plotly_chart(fig7, use_container_width=True)

# 8. Taux d'erreur
errors = df_f[df_f['event_type']=='error']
rate = len(errors)/len(df_f)*100 if len(df_f) else 0
st.metric("Taux d'erreur (%)", f"{rate:.2f}")

# 9. Sessions uniques
sessions = df_f['session_id'].nunique()
st.metric("Sessions uniques", sessions)

# 10. Durée moyenne des sessions
sess_times = df_f[df_f['session_id'].notna()].groupby('session_id')['timestamp'].agg(['min','max']).reset_index()
sess_times['duration_min'] = (sess_times['max'] - sess_times['min']).dt.total_seconds()/60
avg_dur = sess_times['duration_min'].mean()
st.metric("Durée moyenne session (min)", f"{avg_dur:.1f}")

st.sidebar.markdown("---")
st.sidebar.write("E-commerce Log Explorer")
