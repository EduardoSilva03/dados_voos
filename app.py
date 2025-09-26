'''import streamlit as st
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

@st.cache_data
def carregar_e_tratar_dados():
    caminho_dataset = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Dataset')
    padrao_arquivos = os.path.join(caminho_dataset, '*', '*.csv')
    lista_arquivos = glob.glob(padrao_arquivos)
    
    if not lista_arquivos:
        st.error("Nenhum arquivo CSV de voos encontrado na pasta Dataset.")
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

with st.spinner('Carregando e processando dados... Isso pode levar um minuto na primeira vez.'):
    df_completo = carregar_e_tratar_dados()

if df_completo.empty:
    st.stop()

st.title("✈️ Dashboard de Atrasos de Voos no Brasil")
st.markdown("Use os filtros na barra lateral para explorar os dados de voos.")

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
    total_voos = len(df_filtrado)
    total_atrasos = len(df_atrasos)
    taxa_atraso = (total_atrasos / total_voos * 100) if total_voos > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Voos", f"{total_voos:,}".replace(",", "."))
    col2.metric("Total de Atrasos", f"{total_atrasos:,}".replace(",", "."))
    col3.metric("Taxa de Atraso", f"{taxa_atraso:.2f}%")
    st.divider()

    st.subheader("1. Qual o aeroporto que tem mais atrasos no geral?")
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    atrasos_por_aeroporto = df_atrasos['origem'].value_counts().nlargest(15)
    sns.barplot(x=atrasos_por_aeroporto.values, y=atrasos_por_aeroporto.index, palette='viridis', ax=ax1)
    ax1.set_xlabel('Número de Atrasos')
    ax1.set_ylabel('Aeroporto (Origem)')
    st.pyplot(fig1)
    st.divider()

    st.subheader("2. Qual o aeroporto aumentou ou diminuiu o número de atrasos?")
    anos_filtrados = sorted(df_filtrado['ano'].unique())
    if len(anos_filtrados) >= 2:
        primeiro_ano, ultimo_ano = anos_filtrados[0], anos_filtrados[-1]
        atrasos_por_ano_aeroporto = df_atrasos.groupby(['ano', 'origem']).size().unstack(fill_value=0)

        if primeiro_ano in atrasos_por_ano_aeroporto.columns and ultimo_ano in atrasos_por_ano_aeroporto.columns:
            aeroportos_comuns = atrasos_por_ano_aeroporto.index[(atrasos_por_ano_aeroporto[primeiro_ano] > 50) & (atrasos_por_ano_aeroporto[ultimo_ano] > 50)]
            
            if not aeroportos_comuns.empty:
                variacao = atrasos_por_ano_aeroporto.loc[aeroportos_comuns, ultimo_ano] - atrasos_por_ano_aeroporto.loc[aeroportos_comuns, primeiro_ano]
                top_aumento = variacao.nlargest(10)
                top_diminuicao = variacao.nsmallest(10)
                fig2, (ax1_var, ax2_var) = plt.subplots(2, 1, figsize=(12, 10))
                sns.barplot(x=top_aumento.values, y=top_aumento.index, ax=ax1_var, palette='Reds_r')
                ax1_var.set_title(f'Top 10 Aumentos de Atrasos ({primeiro_ano} vs {ultimo_ano})', fontsize=14)
                sns.barplot(x=top_diminuicao.values, y=top_diminuicao.index, ax=ax2_var, palette='Greens_r')
                ax2_var.set_title(f'Top 10 Reduções de Atrasos ({primeiro_ano} vs {ultimo_ano})', fontsize=14)
                plt.tight_layout()
                st.pyplot(fig2)
            else:
                st.info(f"Não há aeroportos com dados suficientes em {primeiro_ano} e {ultimo_ano} para uma comparação justa.")
        else:
            st.warning(f"Não há dados de atrasos registrados para ambos os anos ({primeiro_ano} e {ultimo_ano}) com os filtros atuais para fazer a comparação.")
    else:
        st.info("Selecione pelo menos dois anos no filtro para visualizar a variação de atrasos.")
    st.divider()

    st.subheader("3. Os atrasos aumentaram ou diminuíram no período?")
    fig3, ax3 = plt.subplots(figsize=(12, 5))
    atrasos_por_mes = df_atrasos.groupby(['ano', 'mes']).size().reset_index(name='total_atrasos')
    if not atrasos_por_mes.empty:
        atrasos_por_mes['ano_mes'] = pd.to_datetime(atrasos_por_mes['ano'].astype(str) + '-' + atrasos_por_mes['mes'].astype(str))
        sns.lineplot(x='ano_mes', y='total_atrasos', data=atrasos_por_mes, marker='o', ax=ax3)
        ax3.set_xlabel('Data')
        ax3.set_ylabel('Número de Atrasos')
        plt.xticks(rotation=45)
    st.pyplot(fig3)
    st.divider()

    st.subheader("4. Dias da semana com mais atrasos (a cada ano)")
    ordem_dias = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
    g4 = sns.catplot(data=df_atrasos, x='dia_da_semana', col='ano', kind='count', order=ordem_dias, palette='plasma', height=5, aspect=1.5, col_wrap=3)
    g4.fig.suptitle('Número de Atrasos por Dia da Semana (Anual)', y=1.03, fontsize=16)
    g4.set_axis_labels("Dia da Semana", "Número de Atrasos")
    g4.set_xticklabels(rotation=45)
    st.pyplot(g4.fig)
    st.divider()

    st.subheader("5. Período do dia com mais atrasos (a cada ano)")
    ordem_periodo = ['Manhã', 'Tarde', 'Noite', 'Madrugada']
    g5 = sns.catplot(data=df_atrasos, x='periodo_do_dia', col='ano', kind='count', order=ordem_periodo, palette='magma', height=5, aspect=1.5, col_wrap=3)
    g5.fig.suptitle('Número de Atrasos por Período do Dia (Anual)', y=1.03, fontsize=16)
    g5.set_axis_labels("Período do Dia", "Número de Atrasos")
    st.pyplot(g5.fig)
    st.divider()
    
    st.subheader("6. Companhia que mais atrasa (a cada ano)")
    g6 = sns.catplot(data=df_atrasos, x='empresa', col='ano', kind='count', palette='cividis', height=5, aspect=1.5, order=df_atrasos['empresa'].value_counts().index, col_wrap=3)
    g6.fig.suptitle('Número de Atrasos por Companhia Aérea (Anual)', y=1.03, fontsize=16)
    g6.set_axis_labels("Companhia Aérea", "Número de Atrasos")
    g6.set_xticklabels(rotation=45)
    st.pyplot(g6.fig)'''

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

st.set_page_config(layout="wide", page_title="Dashboard de Atrasos de Voos no Brasil")

sns.set_theme(style="whitegrid")

@st.cache_data
def carregar_e_tratar_dados():
    caminho_dataset = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Dataset')
    padrao_arquivos = os.path.join(caminho_dataset, '*', '*.csv')
    lista_arquivos = glob.glob(padrao_arquivos)
    
    if not lista_arquivos:
        return pd.DataFrame()

    lista_dfs = [pd.read_csv(arquivo, sep=';', header=1, encoding='utf-8', low_memory=False) for arquivo in lista_arquivos]
    df = pd.concat(lista_dfs, ignore_index=True)
    
    df['Partida Prevista'] = pd.to_datetime(df['Partida Prevista'], errors='coerce')
    df.dropna(subset=['Partida Prevista'], inplace=True)
    df = df[df['Partida Prevista'].dt.year < 2025]

    colunas = {
        'origem': 'ICAO Aeródromo Origem',
        'empresa': 'ICAO Empresa Aérea',
        'partida_prevista': 'Partida Prevista',
        'partida_real': 'Partida Real'
    }
    df = df.rename(columns={v: k for k, v in colunas.items()})

    colunas_essenciais = ['origem', 'empresa', 'partida_prevista', 'partida_real']
    df.dropna(subset=colunas_essenciais, inplace=True)
    
    df['partida_real'] = pd.to_datetime(df['partida_real'], errors='coerce')
    df.dropna(subset=['partida_real'], inplace=True)

    df['atraso_minutos'] = (df['partida_real'] - df['partida_prevista']).dt.total_seconds() / 60
    df['houve_atraso'] = df['atraso_minutos'] > 15
    df['ano'] = df['partida_prevista'].dt.year
    df['mes'] = df['partida_prevista'].dt.month
    
    dias_map = {0: 'segunda-feira', 1: 'terça-feira', 2: 'quarta-feira', 3: 'quinta-feira', 4: 'sexta-feira', 5: 'sábado', 6: 'domingo'}
    df['dia_da_semana'] = df['partida_prevista'].dt.dayofweek.map(dias_map)
    
    bins = [-1, 6, 12, 18, 24]
    labels = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
    df['periodo_do_dia'] = pd.cut(df['partida_prevista'].dt.hour, bins=bins, labels=labels, right=False)
    
    return df

with st.spinner('Carregando e processando dados...'):
    df_completo = carregar_e_tratar_dados()

if df_completo.empty:
    st.error("Não foi possível carregar os dados. Verifique a pasta 'Dataset' e os arquivos CSV.")
    st.stop()

st.title("✈️ Dashboard de Atrasos de Voos no Brasil (2022-2024)")
st.markdown("Use os filtros na barra lateral para explorar os dados.")

st.sidebar.header("Filtros")

anos_disponiveis = sorted(df_completo['ano'].unique(), reverse=True)
anos_selecionados = st.sidebar.multiselect("Ano(s)", anos_disponiveis, default=anos_disponiveis)

empresas_disponiveis = sorted(df_completo['empresa'].unique())
empresas_selecionadas = st.sidebar.multiselect("Companhia(s) Aérea(s)", empresas_disponiveis, default=[])

aeroportos_disponiveis = df_completo['origem'].value_counts().nlargest(50).index.tolist()
aeroportos_selecionados = st.sidebar.multiselect("Aeroporto(s) de Origem", sorted(aeroportos_disponiveis), default=[])

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
    total_voos = len(df_filtrado)
    total_atrasos = len(df_atrasos)
    taxa_atraso = (total_atrasos / total_voos * 100) if total_voos > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Voos", f"{total_voos:,}".replace(",", "."))
    col2.metric("Total de Atrasos", f"{total_atrasos:,}".replace(",", "."))
    col3.metric("Taxa de Atraso", f"{taxa_atraso:.2f}%")
    st.divider()

    st.subheader("1. Aeroportos com maior número de atrasos no geral")
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    atrasos_por_aeroporto = df_atrasos['origem'].value_counts().nlargest(15)
    sns.barplot(x=atrasos_por_aeroporto.values, y=atrasos_por_aeroporto.index, palette='viridis', ax=ax1)
    ax1.set_xlabel('Número de Atrasos')
    ax1.set_ylabel('Aeroporto (Origem)')
    st.pyplot(fig1)
    st.divider()

    st.subheader("2. Variação de atrasos por aeroporto")
    anos_filtrados_unicos = sorted(df_atrasos['ano'].unique())
    if len(anos_selecionados) >= 2:
        primeiro_ano, ultimo_ano = min(anos_selecionados), max(anos_selecionados)
        atrasos_por_ano_aeroporto = df_atrasos.groupby(['ano', 'origem']).size().unstack(fill_value=0)
        
        if primeiro_ano in atrasos_por_ano_aeroporto.columns and ultimo_ano in atrasos_por_ano_aeroporto.columns:
            aeroportos_comuns = atrasos_por_ano_aeroporto.index[(atrasos_por_ano_aeroporto[primeiro_ano] > 50) & (atrasos_por_ano_aeroporto[ultimo_ano] > 50)]
            
            if not aeroportos_comuns.empty:
                variacao = atrasos_por_ano_aeroporto.loc[aeroportos_comuns, ultimo_ano] - atrasos_por_ano_aeroporto.loc[aeroportos_comuns, primeiro_ano]
                top_aumento = variacao.nlargest(10)
                top_diminuicao = variacao.nsmallest(10)
                fig2, (ax1_var, ax2_var) = plt.subplots(2, 1, figsize=(12, 10))
                sns.barplot(x=top_aumento.values, y=top_aumento.index, ax=ax1_var, palette='Reds_r')
                ax1_var.set_title(f'Top 10 Aumentos ({primeiro_ano} vs {ultimo_ano})', fontsize=14)
                sns.barplot(x=top_diminuicao.values, y=top_diminuicao.index, ax=ax2_var, palette='Greens_r')
                ax2_var.set_title(f'Top 10 Reduções ({primeiro_ano} vs {ultimo_ano})', fontsize=14)
                plt.tight_layout()
                st.pyplot(fig2)
            else:
                st.info(f"Não há aeroportos com dados suficientes em {primeiro_ano} e {ultimo_ano} para uma comparação.")
        else:
            st.warning(f"Não há dados de atrasos para ambos os anos ({primeiro_ano} e {ultimo_ano}) com os filtros atuais.")
    else:
        st.info("Selecione pelo menos dois anos no filtro para visualizar a variação de atrasos.")
    st.divider()

    st.subheader("3. Evolução do número de atrasos no período")
    fig3, ax3 = plt.subplots(figsize=(12, 5))
    atrasos_por_mes = df_atrasos.groupby(['ano', 'mes']).size().reset_index(name='total_atrasos')
    if not atrasos_por_mes.empty:
        atrasos_por_mes['ano_mes'] = pd.to_datetime(atrasos_por_mes['ano'].astype(str) + '-' + atrasos_por_mes['mes'].astype(str))
        sns.lineplot(x='ano_mes', y='total_atrasos', data=atrasos_por_mes, marker='o', ax=ax3, hue='ano', palette='viridis')
        ax3.set_xlabel('Data')
        ax3.set_ylabel('Número de Atrasos')
        plt.xticks(rotation=45)
    st.pyplot(fig3)
    st.divider()

    col_anual1, col_anual2 = st.columns(2)
    with col_anual1:
        st.subheader("4. Atrasos por dia da semana (anual)")
        ordem_dias = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
        g4 = sns.catplot(data=df_atrasos, x='dia_da_semana', col='ano', kind='count', order=ordem_dias, palette='plasma', height=5, aspect=1.2)
        g4.fig.suptitle('Contagem de Atrasos por Dia da Semana', y=1.03, fontsize=16)
        g4.set_axis_labels("", "Número de Atrasos")
        g4.set_xticklabels(rotation=45)
        st.pyplot(g4.fig)

    with col_anual2:
        st.subheader("5. Atrasos por período do dia (anual)")
        ordem_periodo = ['Manhã', 'Tarde', 'Noite', 'Madrugada']
        g5 = sns.catplot(data=df_atrasos, x='periodo_do_dia', col='ano', kind='count', order=ordem_periodo, palette='magma', height=5, aspect=1.2)
        g5.fig.suptitle('Contagem de Atrasos por Período do Dia', y=1.03, fontsize=16)
        g5.set_axis_labels("", "Número de Atrasos")
        st.pyplot(g5.fig)
    st.divider()
    
    st.subheader("6. Top 15 Companhias com mais atrasos (anual)")
    if not df_atrasos.empty:
        top_15_empresas = df_atrasos['empresa'].value_counts().nlargest(15).index.tolist()
        df_top_empresas = df_atrasos[df_atrasos['empresa'].isin(top_15_empresas)]
        
        st.markdown("#### Destaques Anuais")
        anos_no_df = sorted(df_top_empresas['ano'].unique())
        
        for ano in anos_no_df:
            df_ano = df_top_empresas[df_top_empresas['ano'] == ano]
            if not df_ano.empty:
                st.write(f"**Ranking para o ano de {ano}:**")
                ranking_anual = df_ano['empresa'].value_counts().nlargest(3)
                
                num_cols = min(len(ranking_anual), 3)
                cols = st.columns(num_cols)
                
                for i, (empresa, contagem) in enumerate(ranking_anual.items()):
                    with cols[i]:
                        st.metric(label=f"{i+1}º Lugar", value=empresa, delta=f"{contagem} atrasos", delta_color="off")
        
        st.markdown("---")
        st.write("O gráfico abaixo detalha a contagem de atrasos para as 15 principais companhias em cada ano selecionado.")

        g6 = sns.catplot(data=df_top_empresas, x='empresa', col='ano', kind='count', palette='cividis', height=6, aspect=2, order=top_15_empresas, col_wrap=1)
        g6.fig.suptitle('Contagem de Atrasos por Companhia Aérea (Top 15)', y=1.03, fontsize=16)
        g6.set_axis_labels("Companhia Aérea", "Número de Atrasos")
        g6.set_xticklabels(rotation=45)
        st.pyplot(g6.fig)