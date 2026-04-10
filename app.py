import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DE CORES (Baseado no seu código React) ---
COLOR_ENTRADA = ['#059669', '#10b981', '#34d399']
COLOR_SAIDA = ['#be123c', '#e11d48', '#f43f5e']

st.set_page_config(page_title="Caixa Louvor Eterno", layout="wide")

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS para parecer o React) ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stMetric { 
        background-color: white; 
        padding: 20px; 
        border-radius: 20px; 
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
    }
    div[data-testid="stSidebar"] { background-color: #0f172a; }
    h1 { font-weight: 900 !important; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN (Usando Secrets do Streamlit) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 CAIXA LOUVOR ETERNO")
    chave = st.text_input("DIGITE A CHAVE DO GRUPO", type="password")
    if st.button("ENTRAR NO SISTEMA"):
        if chave == st.secrets["chave_grupo"]:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Chave incorreta")
else:
    # --- HEADER ---
    st.title("💸 Caixa Louvor Eterno")
    
    # --- CARDS DE TOTAIS (Estilo o seu código React) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Em Mãos (Espécie)", "R$ 1.200,00")
    with col2:
        st.metric("No Pix (Banco)", "R$ 850,00")
    with col3:
        st.metric("Saldo Total", "R$ 2.050,00")

    st.divider()

    # --- ÁREA CENTRAL ---
    col_form, col_graph = st.columns([1, 2])

    with col_form:
        st.subheader("📝 Registrar")
        with st.container(border=True):
            tipo = st.radio("Tipo", ["Entrada (+)", "Saída (-)"], horizontal=True)
            local = st.selectbox("Local", ["Dinheiro (Espécie)", "Pix"])
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor R$", min_value=0.0)
            if st.button("Registrar Agora", use_container_width=True):
                st.success("Registrado com sucesso!")

    with col_graph:
        st.subheader("📊 Distribuição")
        # Criando um gráfico de pizza igual ao do React usando Plotly
        fig = go.Figure(data=[go.Pie(labels=['Entradas', 'Saídas'], 
                             values=[1200, 450], 
                             hole=.6,
                             marker_colors=[COLOR_ENTRADA[0], COLOR_SAIDA[0]])])
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig, use_container_width=True)

    # --- TABELA DE HISTÓRICO ---
    st.subheader("📜 Histórico de Lançamentos")
    dados_exemplo = pd.DataFrame({
        "Data": ["10 Abr", "08 Abr"],
        "Descrição": ["Oferta Culto", "Lanche Ensaio"],
        "Categoria": ["Oferta", "Lanches"],
        "Valor": ["+ R$ 500,00", "- R$ 120,00"]
    })
    st.table(dados_exemplo)