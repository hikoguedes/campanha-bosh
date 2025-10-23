import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Análise de Campanhas",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Análise Completa de Campanhas de Marketing")
st.subheader("Período: 23/09/2025 a 22/10/2025")

# --- Função de Pré-processamento de Dados ---
# O cache_data é importante para o desempenho do Streamlit
@st.cache_data
def load_and_preprocess_data():
    """Carrega todos os CSVs e aplica o pré-processamento de limpeza."""
    data = {}
    file_mapping = {
        "Campanhas": "Campanhas(2025.09.23-2025.10.22).csv",
        "Dispositivos": "Dispositivos(2025.09.23-2025.10.22).csv",
        "Dia": "Dia_e_hora(Dia_2025.09.23-2025.10.22).csv",
        "Dia_Hora": "Dia_e_hora(Dia_Hora_2025.09.23-2025.10.22).csv",
        "Hora": "Dia_e_hora(Hora_2025.09.23-2025.10.22).csv",
        "Idade": "Informações_demográficas(Idade_2025.09.23-2025.10.22).csv",
        "Sexo": "Informações_demográficas(Sexo_2025.09.23-2025.10.22).csv",
        "Sexo_Idade": "Informações_demográficas(Sexo_Idade_2025.09.23-2025.10.22).csv",
        "Alteracoes": "Maiores_alterações(2025.09.23-2025.10.22_em_comparação_com_2025.08.24-2025.09.22).csv",
        "Palavras_Chave": "Palavras-chave_de_pesquisa(2025.09.23-2025.10.22).csv",
    }

    def clean_currency_value(series):
        """Limpa valores de moeda (R$) e converte para float, tratando erros."""
        return series.astype(str).str.replace('R$\xa0', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip().apply(lambda x: float(x) if x else 0)

    def clean_numeric_value(series):
        """Limpa valores numéricos com separador de milhar/decimal e converte para float."""
        return series.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip().apply(lambda x: float(x) if x else 0)

    for key, filename in file_mapping.items():
        try:
            # Detectar o separador (vírgula ou ponto e vírgula)
            try:
                df = pd.read_csv(filename, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(filename, encoding='latin-1')

            # Limpeza específica para cada arquivo
            if key == "Campanhas":
                df['Custo'] = clean_currency_value(df['Custo'])
                df['Conversões'] = clean_numeric_value(df['Conversões'])
                df['Custo / conv.'] = clean_currency_value(df['Custo / conv.'])
            
            elif key == "Dispositivos":
                df['Custo'] = clean_currency_value(df['Custo'])
                df['Cliques'] = clean_numeric_value(df['Cliques'])
                df['Conversões'] = clean_numeric_value(df['Conversões'])

            elif key in ["Dia", "Hora"]:
                df['Impressões'] = clean_numeric_value(df['Impressões'])
            
            elif key == "Dia_Hora":
                # Adicionar um tratamento para 'Hora de início' que pode ser lido como string
                if 'Hora de início' in df.columns:
                    df['Hora de início'] = df['Hora de início'].astype(str).str.zfill(2)
                df['Impressões'] = clean_numeric_value(df['Impressões'])
            
            elif key in ["Idade", "Sexo", "Sexo_Idade"]:
                df['Impressões'] = clean_numeric_value(df['Impressões'])

            elif key == "Alteracoes":
                for col in ['Custo', 'Custo (Comparação)']:
                    df[col] = clean_currency_value(df[col])
                for col in ['Cliques', 'Cliques (Comparação)', 'Interações', 'Interações (Comparação)']:
                    df[col] = clean_numeric_value(df[col])
            
            elif key == "Palavras_Chave":
                df['Custo'] = clean_currency_value(df['Custo'])
                df['Cliques'] = clean_numeric_value(df['Cliques'])
                # Converter CTR para float (removendo '%')
                df['CTR'] = df['CTR'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).str.strip().apply(lambda x: float(x) if x else 0)
            
            data[key] = df
        except FileNotFoundError:
            st.error(f"Arquivo não encontrado: {filename}. Certifique-se de que o nome do arquivo está correto e ele está no mesmo diretório.")
            return None
        except Exception as e:
            st.error(f"Erro ao processar o arquivo {filename}: {e}")
            return None
            
    return data

# Carregar dados
data = load_and_preprocess_data()

if data is None:
    st.stop()

df_campanhas = data['Campanhas']
df_dispositivos = data['Dispositivos']
df_dia = data['Dia']
df_hora = data['Hora']
df_dia_hora = data['Dia_Hora']
df_idade = data['Idade']
df_sexo = data['Sexo']
df_sexo_idade = data['Sexo_Idade']
df_alteracoes = data['Alteracoes']
df_palavras_chave = data['Palavras_Chave']


# --- 1. Visão Geral das Campanhas ---
st.header("1. Desempenho das Campanhas")

# Métricas Totais
total_custo = df_campanhas['Custo'].sum()
total_conversoes = df_campanhas['Conversões'].sum()
total_cpa = total_custo / total_conversoes if total_conversoes > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("💰 Custo Total", f"R$ {total_custo:,.2f}")
col2.metric("✅ Conversões Totais", f"{total_conversoes:,.0f}")
col3.metric("🎯 CPA Médio", f"R$ {total_cpa:,.2f}")

st.markdown("---")

# Gráfico de Desempenho por Campanha
st.subheader("Desempenho por Campanha (Custo vs. Conversões)")
# Tratar campanhas sem conversão para CPA infinito (representado por NaN/inf)
df_campanhas['CPA_Calc'] = df_campanhas.apply(
    lambda row: row['Custo'] / row['Conversões'] if row['Conversões'] > 0 else np.nan, 
    axis=1
)

fig_campanhas = px.scatter(
    df_campanhas.fillna({'CPA_Calc': df_campanhas['CPA_Calc'].max() * 1.5 if not df_campanhas['CPA_Calc'].empty and df_campanhas['CPA_Calc'].max() > 0 else 1}), # Substituir NaN por um valor alto para visualização
    x='Custo',
    y='Conversões',
    size='CPA_Calc',
    color='Nome da campanha',
    hover_name='Nome da campanha',
    log_x=True,
    title="Custo vs. Conversões por Campanha (Tamanho = CPA)",
    labels={'CPA_Calc': 'CPA (Custo/Conversão)'}
)
fig_campanhas.update_layout(height=500)
st.plotly_chart(fig_campanhas, use_container_width=True)

# --- 2. Análise de Dispositivos ---
st.header("2. Desempenho por Dispositivo")

# KPI de Dispositivos
total_custo_disp = df_dispositivos['Custo'].sum()
total_conversoes_disp = df_dispositivos['Conversões'].sum()
df_dispositivos['Porcentagem Custo'] = (df_dispositivos['Custo'] / total_custo_disp) * 100
df_dispositivos['Porcentagem Conversões'] = (df_dispositivos['Conversões'] / total_conversoes_disp) * 100
# Calcular CPA com tratamento para evitar divisão por zero
df_dispositivos['CPA'] = df_dispositivos.apply(
    lambda row: row['Custo'] / row['Conversões'] if row['Conversões'] > 0 else (row['Custo'] if row['Custo'] > 0 else 0),
    axis=1
)


col_disp1, col_disp2 = st.columns(2)

with col_disp1:
    st.subheader("Distribuição de Custo por Dispositivo")
    # Excluir 'Telas de TV' se o custo for zero
    df_disp_pie = df_dispositivos[df_dispositivos['Custo'] > 0]
    fig_custo_disp = px.pie(
        df_disp_pie,
        values='Custo',
        names='Dispositivo',
        title='Custo por Dispositivo',
        hole=.3
    )
    st.plotly_chart(fig_custo_disp, use_container_width=True)

with col_disp2:
    st.subheader("Conversões e CPA por Dispositivo")
    fig_conv_cpa = px.bar(
        df_dispositivos.sort_values(by='Conversões', ascending=False),
        x='Dispositivo',
        y='Conversões',
        color='CPA',
        title='Conversões por Dispositivo (Cor = CPA)',
        text='Conversões',
        color_continuous_scale=px.colors.sequential.Inferno
    )
    st.plotly_chart(fig_conv_cpa, use_container_width=True)


# --- 3. Análise Temporal ---
st.header("3. Análise Temporal de Impressões")

col_temp1, col_temp2 = st.columns(2)

with col_temp1:
    st.subheader("Impressões por Dia da Semana")
    # Garantir a ordem correta dos dias da semana
    day_order = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    df_dia_ordered = df_dia.set_index('Dia').reindex(day_order).reset_index()

    fig_dia = px.bar(
        df_dia_ordered,
        x='Dia',
        y='Impressões',
        title='Total de Impressões por Dia da Semana',
        text='Impressões',
        color='Impressões'
    )
    fig_dia.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_dia.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig_dia, use_container_width=True)

with col_temp2:
    st.subheader("Impressões por Hora do Dia")
    
    fig_hora = px.line(
        df_hora,
        x='Hora de início',
        y='Impressões',
        title='Total de Impressões por Hora',
        markers=True
    )
    # A hora de início já é um índice no eixo X, não precisa de dtick
    st.plotly_chart(fig_hora, use_container_width=True)

st.subheader("Mapa de Calor: Impressões por Dia e Hora")

# Pivotar para criar a matriz para o mapa de calor
df_heatmap = df_dia_hora.pivot_table(index='Hora de início', columns='Dia', values='Impressões', fill_value=0)
df_heatmap = df_heatmap[day_order] # Reordenar colunas

fig_heatmap = px.imshow(
    df_heatmap.values,
    x=df_heatmap.columns,
    y=df_heatmap.index,
    color_continuous_scale='Reds',
    aspect="auto",
    labels=dict(x="Dia da Semana", y="Hora", color="Impressões")
)
fig_heatmap.update_xaxes(side="top")
fig_heatmap.update_layout(
    title='Mapa de Calor de Impressões (Dia vs. Hora)',
    height=600
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# --- 4. Análise Demográfica ---
st.header("4. Informações Demográficas (Impressões)")

col_demo1, col_demo2 = st.columns(2)

with col_demo1:
    st.subheader("Impressões por Faixa Etária")
    fig_idade = px.bar(
        df_idade.sort_values(by='Impressões', ascending=False),
        x='Faixa de idade',
        y='Impressões',
        title='Impressões por Idade',
        text='Porcentagem do total conhecido',
        color='Porcentagem do total conhecido'
    )
    st.plotly_chart(fig_idade, use_container_width=True)

with col_demo2:
    st.subheader("Impressões por Sexo e Idade")
    fig_sexo_idade = px.bar(
        df_sexo_idade.sort_values(by='Impressões', ascending=False),
        x='Faixa de idade',
        y='Impressões',
        color='Sexo',
        title='Impressões por Sexo e Faixa Etária',
        barmode='group'
    )
    st.plotly_chart(fig_sexo_idade, use_container_width=True)

# --- 5. Palavras-chave ---
st.header("5. Desempenho das Palavras-chave")

top_n_keywords = st.slider("Selecione o Top N de Palavras-chave:", 5, 50, 15)

# Remover linhas onde Custo é 0 para top_custo
df_palavras_chave_custo = df_palavras_chave[df_palavras_chave['Custo'] > 0]
df_kw_top_custo = df_palavras_chave_custo.nlargest(top_n_keywords, 'Custo').sort_values(by='Custo', ascending=True)

# Remover linhas onde CTR é 0 (ou seja, Cliques = 0) para top_ctr
df_palavras_chave_ctr = df_palavras_chave[df_palavras_chave['Cliques'] > 0]
df_kw_top_ctr = df_palavras_chave_ctr.nlargest(top_n_keywords, 'CTR').sort_values(by='CTR', ascending=True)


# Gráfico de Custo
fig_kw_custo = px.bar(
    df_kw_top_custo,
    x='Custo',
    y='Palavra-chave da rede de pesquisa',
    orientation='h',
    title=f'Top {top_n_keywords} Palavras-chave por Custo',
    text='Custo'
)
fig_kw_custo.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
fig_kw_custo.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)

# Gráfico de CTR
fig_kw_ctr = px.bar(
    df_kw_top_ctr,
    x='CTR',
    y='Palavra-chave da rede de pesquisa',
    orientation='h',
    title=f'Top {top_n_keywords} Palavras-chave por CTR',
    text='CTR'
)
fig_kw_ctr.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
fig_kw_ctr.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)


st.plotly_chart(fig_kw_custo, use_container_width=True)
st.plotly_chart(fig_kw_ctr, use_container_width=True)

# --- 6. Comparativo de Períodos ---
st.header("6. Maiores Alterações (Comparação Mês a Mês)")

# Calcular a diferença e a porcentagem de alteração
df_alteracoes['Custo_Diferenca'] = df_alteracoes['Custo'] - df_alteracoes['Custo (Comparação)']
df_alteracoes['Cliques_Diferenca'] = df_alteracoes['Cliques'] - df_alteracoes['Cliques (Comparação)']

# Cálculo Percentual com tratamento para evitar divisão por zero (Comparação = 0)
df_alteracoes['Custo_Percentual'] = df_alteracoes.apply(
    lambda row: ((row['Custo'] - row['Custo (Comparação)']) / row['Custo (Comparação)']) * 100 if row['Custo (Comparação)'] != 0 else (100 if row['Custo'] > 0 else 0),
    axis=1
)

df_alteracoes['Cliques_Percentual'] = df_alteracoes.apply(
    lambda row: ((row['Cliques'] - row['Cliques (Comparação)']) / row['Cliques (Comparação)']) * 100 if row['Cliques (Comparação)'] != 0 else (100 if row['Cliques'] > 0 else 0),
    axis=1
)


st.subheader("Alteração Percentual de Custo e Cliques por Campanha")
df_alteracoes_sorted = df_alteracoes.sort_values(by='Custo_Percentual', ascending=False)

fig_alteracoes = px.bar(
    df_alteracoes_sorted,
    x='Custo_Percentual',
    y='Nome da campanha',
    color='Cliques_Percentual',
    title='Alteração Percentual de Custo (Cor = Alteração Percentual de Cliques)',
    orientation='h',
    # CORREÇÃO APLICADA AQUI: Mudança de .sequential para .diverging
    color_continuous_scale=px.colors.diverging.RdYlGn,
    labels={'Custo_Percentual': 'Custo % de Mudança', 'Cliques_Percentual': 'Cliques % de Mudança'}
)
fig_alteracoes.update_traces(texttemplate='%{x:.1f}%', textposition='outside')
fig_alteracoes.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
st.plotly_chart(fig_alteracoes, use_container_width=True)

# --- 7. Insights e Recomendações ---
st.header("💡 Insights e Recomendações")

st.markdown("---")

# --- Insights ---
st.subheader("Descobertas Chave (Insights)")

# Precalculo para Insights
# Insight 1: Dispositivo
smartphone_row = df_dispositivos[df_dispositivos['Dispositivo'] == 'Smartphones']
if not smartphone_row.empty:
    smartphone_share = smartphone_row['Porcentagem Custo'].iloc[0]
    cpa_computadores = df_dispositivos[df_dispositivos['Dispositivo'] == 'Computadores']['CPA'].iloc[0]
    cpa_tablets = df_dispositivos[df_dispositivos['Dispositivo'] == 'Tablets']['CPA'].iloc[0]
    cpa_smartphone = smartphone_row['CPA'].iloc[0]
    st.info(f"""
    **Domínio Mobile:** O **Smartphone** é o dispositivo dominante, representando **{smartphone_share:,.1f}% do Custo Total**. O CPA no Smartphone (**R$ {cpa_smartphone:.2f}**) é geralmente mais eficiente que em Computadores (**R$ {cpa_computadores:.2f}**) e Tablets (**R$ {cpa_tablets:.2f}**).
    """)

# Insight 2: Temporal
highest_day = df_dia_ordered.iloc[df_dia_ordered['Impressões'].argmax()]['Dia']
highest_hour = df_hora.iloc[df_hora['Impressões'].argmax()]['Hora de início']
st.info(f"""
**Pico Temporal:** O **{highest_day}** e a **Hora {int(highest_hour)} (20h)** são os horários de pico de impressões. O mapa de calor mostra um alto volume de impressões nas noites de **Terça, Quarta e Quinta-feira** (entre 18h e 22h).
""")

# Insight 3: Demográfico
top_age_group = df_idade.iloc[df_idade['Impressões'].argmax()]['Faixa de idade']
top_age_percentage = df_idade.iloc[df_idade['Impressões'].argmax()]['Porcentagem do total conhecido']
sex_ratio_m = df_sexo[df_sexo['Sexo'] == 'Masculino']['Porcentagem do total conhecido'].iloc[0]
st.info(f"""
**Público-alvo Forte:** O público **Masculino ({sex_ratio_m})** domina as impressões. A faixa etária mais forte é **{top_age_group}**, representando **{top_age_percentage}** das impressões conhecidas.
""")

# Insight 4: Palavras-chave
if not df_kw_top_custo.empty:
    kw_alto_custo = df_kw_top_custo.iloc[-1]['Palavra-chave da rede de pesquisa']
if not df_kw_top_ctr.empty:
    kw_alto_ctr = df_kw_top_ctr.iloc[-1]['Palavra-chave da rede de pesquisa']
st.info(f"""
**Oportunidades de Otimização (KW):** Palavras-chave como **'{kw_alto_custo}'** consomem muito custo. Palavras com alto CTR, como **'{kw_alto_ctr}'**, indicam alta relevância e merecem atenção especial.
""")

# Insight 5: Comparativo
if not df_alteracoes_sorted.empty:
    camp_crescimento_custo = df_alteracoes_sorted.iloc[0]['Nome da campanha']
    camp_crescimento_cliques = df_alteracoes_sorted[df_alteracoes_sorted['Cliques_Percentual'] == df_alteracoes_sorted['Cliques_Percentual'].max()]['Nome da campanha'].iloc[0]
    st.info(f"""
    **Maiores Alterações:** A campanha **'{camp_crescimento_custo}'** teve o maior crescimento percentual no Custo, enquanto a **'{camp_crescimento_cliques}'** teve o maior aumento percentual de Cliques. Isso indica mudanças drásticas no volume de tráfego, possivelmente devido a alterações de lance, orçamento ou status (PMAX, neste caso).
    """)

# --- Recomendações ---
st.subheader("Recomendações de Otimização")

st.markdown("""
1.  **Otimização Mobile:**
    * **Ajuste de Lance (Bid Adjustment):** **Aumente** o ajuste de lance (bid adjustment) para Smartphones, onde as conversões são mais eficientes.
    * **Computadores/Tablets:** Se o CPA nesses dispositivos for insatisfatório, considere **reduzir o ajuste de lance** ou revisar a experiência do usuário nessas plataformas.

2.  **Ajuste Temporal:**
    * **Programação de Anúncios (Ad Scheduling):** Concentre seus maiores lances e/ou maior parte do orçamento nas noites de **Terça, Quarta e Quinta** (principalmente entre **18h e 22h**) e na **Hora 20 (20h)** para aproveitar o pico de impressões.
    * **Redução:** Reduza lances nas madrugadas e inícios de manhã para otimizar o orçamento.

3.  **Segmentação Demográfica:**
    * **Foco no Core:** Reforce a segmentação para o público **Masculino, 35 a 54 anos**, que é o seu público mais engajado.
    * **Exclusão/Redução:** Considere diminuir lances para a faixa **18 a 24** e o público **Feminino** para focar o investimento em segmentos com melhor desempenho.

4.  **Gestão de Palavras-chave:**
    * **Análise de Custo (KW: '{kw_alto_custo}'):** Verifique se o alto custo dessa palavra-chave está gerando um CPA aceitável. Caso contrário, refine a correspondência (de Ampla para Frase/Exata) ou adicione termos de pesquisa negativos relacionados para evitar gastos irrelevantes.
    * **Aproveitamento de CTR (KW: '{kw_alto_ctr}'):** Aumente o orçamento e/ou o lance para palavras-chave de alto CTR, pois elas indicam alta relevância e qualidade do anúncio.

5.  **Análise de Campanha (Comparativo):**
    * **Investigar Mudanças:** A campanha com maior crescimento de Cliques ({camp_crescimento_cliques}) deve ser **analisada em detalhe** para garantir que o aumento de volume de tráfego (Cliques) está acompanhado por um aumento proporcional de Conversões e um CPA saudável.
""")