import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os
import locale

st.set_page_config(layout="wide", page_title="Dashboard de Atrasos de Voos no Brasil")

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    print("Locale pt_BR.UTF-8 não encontrado.")

sns.set_theme(style="whitegrid")

# --- CARREGAMENTO E CACHE DOS DADOS ---
@st.cache_data
def carregar_e_tratar_dados():
    caminho_dataset = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Dataset')
    padrao_arquivos = os.path.join(caminho_dataset, '*', '*.csv')
    lista_arquivos = glob.glob(padrao_arquivos)
    
    if not lista_arquivos:
        st.error("Nenhum arquivo CSV encontrado na pasta Dataset.")
        return pd.DataFrame()

    lista_dfs = [pd.read_csv(arquivo, sep=';', header=1, encoding='utf-8', low_memory=False) for arquivo in lista_arquivos]
    df = pd.concat(lista_dfs, ignore_index=True)
    
    colunas = {
        'origem': 'ICAO Aeródromo Origem',
        'empresa': 'ICAO Empresa Aérea',
        'partida_prevista': 'Partida Prevista',
        'partida_real': 'Partida Real'
    }
    df = df.rename(columns={v: k for k, v in colunas.items()})

    colunas_essenciais = ['origem', 'empresa', 'partida_prevista', 'partida_real']
    df.dropna(subset=colunas_essenciais, inplace=True)
    df['partida_prevista'] = pd.to_datetime(df['partida_prevista'], errors='coerce')
    df['partida_real'] = pd.to_datetime(df['partida_real'], errors='coerce')
    df.dropna(subset=['partida_prevista', 'partida_real'], inplace=True)

    df['atraso_minutos'] = (df['partida_real'] - df['partida_prevista']).dt.total_seconds() / 60
    df['houve_atraso'] = df['atraso_minutos'] > 15
    df['ano'] = df['partida_prevista'].dt.year
    df['mes'] = df['partida_prevista'].dt.month
    df['dia_da_semana'] = df['partida_prevista'].dt.day_name()
    bins = [-1, 6, 12, 18, 24]
    labels = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
    df['periodo_do_dia'] = pd.cut(df['partida_prevista'].dt.hour, bins=bins, labels=labels, right=False)
    
    return df

# --- INÍCIO DA APLICAÇÃO ---
with st.spinner('Carregando e processando dados... Isso pode levar um minuto na primeira vez.'):
    df_completo = carregar_e_tratar_dados()

if df_completo.empty:
    st.stop()

st.title("✈️ Dashboard de Atrasos de Voos no Brasil")
st.markdown("Use os filtros na barra lateral para explorar os dados de voos de 2022 a 2024.")

st.sidebar.header("Filtros")

anos_disponiveis = sorted(df_completo['ano'].unique(), reverse=True)
anos_selecionados = st.sidebar.multiselect("Selecione o(s) Ano(s)", anos_disponiveis, default=anos_disponiveis)

empresas_disponiveis = sorted(df_completo['empresa'].unique())
empresas_selecionadas = st.sidebar.multiselect("Selecione a(s) Companhia(s)", empresas_disponiveis, default=[])

aeroportos_disponiveis = df_completo['origem'].value_counts().nlargest(50).index.tolist()
aeroportos_selecionados = st.sidebar.multiselect("Selecione o(s) Aeroporto(s) de Origem", sorted(aeroportos_disponiveis), default=[])

query = []
if anos_selecionados:
    query.append("ano in @anos_selecionados")
if empresas_selecionadas:
    query.append("empresa in @empresas_selecionadas")
if aeroportos_selecionados:
    query.append("origem in @aeroportos_selecionados")

if query:
    df_filtrado = df_completo.query(" and ".join(query))
else:
    df_filtrado = df_completo.copy()

df_atrasos = df_filtrado[df_filtrado['houve_atraso']].copy()

st.header("Visão Geral dos Voos Filtrados")

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    # Métricas (KPIs)
    total_voos = len(df_filtrado)
    total_atrasos = len(df_atrasos)
    taxa_atraso = (total_atrasos / total_voos * 100) if total_voos > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Voos", f"{total_voos:,}".replace(",", "."))
    col2.metric("Total de Atrasos", f"{total_atrasos:,}".replace(",", "."))
    col3.metric("Taxa de Atraso", f"{taxa_atraso:.2f}%")

    st.header("Análises Detalhadas")

    st.subheader("Aeroportos com Mais Atrasos")
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    atrasos_por_aeroporto = df_atrasos['origem'].value_counts().nlargest(15)
    sns.barplot(x=atrasos_por_aeroporto.values, y=atrasos_por_aeroporto.index, palette='viridis', ax=ax1)
    ax1.set_xlabel('Número de Atrasos')
    ax1.set_ylabel('Aeroporto (Origem)')
    st.pyplot(fig1)

    st.subheader("Evolução Mensal do Número de Atrasos")
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    atrasos_por_mes = df_atrasos.groupby(['ano', 'mes']).size().reset_index(name='total_atrasos')
    if not atrasos_por_mes.empty:
        atrasos_por_mes['ano_mes'] = pd.to_datetime(atrasos_por_mes['ano'].astype(str) + '-' + atrasos_por_mes['mes'].astype(str))
        sns.lineplot(x='ano_mes', y='total_atrasos', data=atrasos_por_mes, marker='o', ax=ax2)
        ax2.set_xlabel('Data')
        ax2.set_ylabel('Número de Atrasos')
        plt.xticks(rotation=45)
    st.pyplot(fig2)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Atrasos por Dia da Semana")
        fig3, ax3 = plt.subplots(figsize=(8, 6))
        ordem_dias = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
        sns.countplot(data=df_atrasos, y='dia_da_semana', order=ordem_dias, palette='plasma', ax=ax3)
        ax3.set_xlabel('Número de Atrasos')
        ax3.set_ylabel('Dia da Semana')
        st.pyplot(fig3)

    with col2:
        st.subheader("Atrasos por Período do Dia")
        fig4, ax4 = plt.subplots(figsize=(8, 6))
        ordem_periodo = ['Manhã', 'Tarde', 'Noite', 'Madrugada']
        sns.countplot(data=df_atrasos, y='periodo_do_dia', order=ordem_periodo, palette='magma', ax=ax4)
        ax4.set_xlabel('Número de Atrasos')
        ax4.set_ylabel('Período do Dia')
        st.pyplot(fig4)