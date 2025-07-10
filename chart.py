from pyairtable import Api
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
from collections import Counter
import requests

# Configuracion de AirTable

api_key_at = st.secrets["airtable"]["api_key"]
base_id = st.secrets["airtable"]["base_24_id"]
table_id = st.secrets["airtable"]["table_24_id"]

api = Api(api_key_at)
table_24 = api.table(base_id, table_id)

records_24 = table_24.all(view='MEX24_Full Applicants', time_zone="Europe/Madrid")
data_24 = [record['fields'] for record in records_24]
df = pd.DataFrame(data_24)

def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df = df.applymap(fix_cell)
st.set_page_config(
    page_title="Opencall Dashboard Decelera Mexico 2025",
    layout="wide"
)

#vamos al lio
df['fecha'] = pd.to_datetime(df['Created_str'], errors='coerce')
df = df[df['fecha'] >= pd.to_datetime('2024-06-17')]

#creamos la columna semana por lunes de cada semana
df['semana'] = df['fecha'] - pd.to_timedelta(df['fecha'].dt.dayofweek, unit='d')
df['semana'] = df['semana'].dt.date

#quitamos los repetidos
# Limpieza completa
df['PH1_reference_$startups'] = df['PH1_reference_$startups'].fillna('Sin referencia')
df['PH1_reference_$startups'] = df['PH1_reference_$startups'].astype(str)
df['PH1_reference_$startups'] = df['PH1_reference_$startups'].str.strip()
df['PH1_reference_$startups'] = df['PH1_reference_$startups'].str.replace(r'\s+', ' ', regex=True)
df['PH1_reference_$startups'] = df['PH1_reference_$startups'].str.lower()

# Reemplazo
reemplazos = {
    "decelera linkedin post": "Decelera Linkedin post",
    "linkedin post from someone else": "Linkedin post from someone else",
    "decelera team reached through email": "Decelera team reached through email",
    "decelera team reached through linkedin": "Decelera team reached through LinkedIn",
    "startup communty (i.e. other accelerators)": "Startup Community (i.e. other accelerators)",
    "Startup Communty  (i.e. other accelerators)": "Startup Community (i.e. other accelerators)",
    "Startup Community  (i.e. other accelerator)": "Startup Community (i.e. other accelerators)",
    "startup community (i.e. other accelerator)": "Startup Community (i.e. other accelerators)",
    "startup community (i.e. other accelerators)": "Startup Community (i.e. other accelerators)",
    "online press/magazine/blog/newsletters": "Online Press / Blogs",
    "gust": "Gust",
    "instagram": "Instagram",
    "google": "Google",
    "referral": "Referral",
    "sin referencia": "Sin referencia"
}

df['PH1_reference_$startups'] = df['PH1_reference_$startups'].replace(reemplazos)



#agrupamos por semana y referencia
conteo = df.groupby(['semana', 'PH1_reference_$startups']).size().reset_index(name='count')
# Calcular porcentaje global por referencia

total_global = conteo['count'].sum()
conteo_global = conteo.groupby('PH1_reference_$startups')['count'].sum().reset_index()
conteo_global['pct'] = conteo_global['count'] / total_global * 100

# Identificar referencias menores al 0.8%
referencias_pequenas = conteo_global[conteo_global['pct'] < 1]['PH1_reference_$startups'].tolist()

conteo['Referencia_agrupada'] = conteo['PH1_reference_$startups'].apply(
    lambda x: 'Others' if x in referencias_pequenas else x
)

# Agrupar de nuevo para consolidar los "Others" por semana
conteo = conteo.groupby(['semana', 'Referencia_agrupada'], as_index=False)['count'].sum()

# Calcular total semanal
conteo['total_semanal'] = conteo.groupby('semana')['count'].transform('sum')
conteo['pct'] = (conteo['count'] / conteo['total_semanal'] * 100).round(1)
conteo['text'] = conteo['count'].astype(str) + "(" + conteo['pct'].astype(str) + "%)"

fig = px.bar(
    conteo,
    x='semana',
    y='count',
    color='Referencia_agrupada',
    title='References per week Mexico 2024',
    text='text',
    barmode='stack'
)

fig.update_traces(
    textposition='inside'
)

fig.update_layout(template='plotly_white', xaxis_title='Week', yaxis_title='Number of applications', height=1400)

st.plotly_chart(fig)