import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Caixa Louvor Eterno", page_icon="💰", layout="wide")

# --- 2. ESTILO CSS (Modo Escuro / Dark Mode) ---
st.markdown("""
    <style>
    /* Fundo da página */
    .stApp, .main { background-color: #0f172a; color: #f8fafc; }
    
    /* Estilização dos Cards de métricas */
    div[data-testid="stMetric"] {
        background-color: #1e293b !important;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        border-left: 5px solid #6366f1; /* Linha roxa na lateral */
        border-top: none; border-right: none; border-bottom: none;
    }
    
    /* Títulos e textos globais forçados para branco/cinza claro */
    h1, h2, h3, h4, h5, h6, p, span, label, div { 
        font-family: 'Inter', sans-serif; 
        color: #f8fafc; 
    }
    
    /* Forçar cor específica dos valores nas métricas */
    [data-testid="stMetricValue"] > div { color: #ffffff !important; font-weight: 900; }
    [data-testid="stMetricLabel"] > div { color: #94a3b8 !important; }
    
    /* Botões personalizados */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        background-color: #6366f1;
        color: white !important;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { 
        background-color: #4f46e5; 
        transform: translateY(-2px); 
    }

    /* Campos de input, formulários e selects */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🔑 Acesso ao Caixa</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
    with col_l2:
        with st.container():
            chave = st.text_input("Chave do Grupo", type="password")
            if st.button("ACESSAR PAINEL"):
                if chave == st.secrets["chave_grupo"]:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Chave inválida!")
else:
    # --- 4. CABEÇALHO ---
    st.markdown("# 💎 Caixa Louvor Eterno")
    st.markdown(f"📅 Hoje é dia {datetime.now().strftime('%d/%m/%Y')}")

    # --- 5. BANCO DE DADOS TEMPORÁRIO ---
    if 'movimentacoes' not in st.session_state:
        st.session_state.movimentacoes = pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor"])

    df = st.session_state.movimentacoes

    # --- 6. BARRA LATERAL ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/552/552791.png", width=80)
    st.sidebar.title("Menu de Gestão")
    menu = st.sidebar.radio("Selecione a página:", ["📊 Dashboard", "📝 Lançamentos", "📜 Histórico"])
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.autenticado = False
        st.rerun()

    # --- 7. LÓGICA DAS PÁGINAS ---
    if menu == "📊 Dashboard":
        # Métricas de Saldo
        valor_especie = df[df['Local'] == 'Dinheiro']['Valor'].sum() if not df.empty else 0.0
        valor_pix = df[df['Local'] == 'Pix']['Valor'].sum() if not df.empty else 0.0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Em Mãos", f"R$ {valor_especie:,.2f}")
        c2.metric("📱 No Pix", f"R$ {valor_pix:,.2f}")
        c3.metric("🏦 Saldo Total", f"R$ {valor_especie + valor_pix:,.2f}")

        st.divider()

        # Gráfico Donut Chart (Estilo Profissional)
        col_graf, col_resumo = st.columns([2, 1])
        with col_graf:
            if not df.empty:
                entradas = df[df['Tipo'] == 'Entrada']['Valor'].abs().sum()
                saidas = df[df['Tipo'] == 'Saída']['Valor'].abs().sum()
                
                fig = go.Figure(data=[go.Pie(
                    labels=['Entradas', 'Saídas'],
                    values=[entradas, saidas],
                    hole=.6,
                    marker_colors=['#10b981', '#f43f5e']
                )])
                fig.update_layout(title="Distribuição de Fluxo", margin=dict(t=50, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Lance valores para ver o gráfico.")

    elif menu == "📝 Lançamentos":
        st.subheader("Registrar Nova Movimentação")
        with st.form("meu_formulario"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
                local = st.selectbox("Local", ["Dinheiro", "Pix"])
                valor = st.number_input("Valor R$", min_value=0.0, step=1.0)
            with col_f2:
                desc = st.text_input("Descrição (Ex: Oferta Culto)")
                cat = st.selectbox("Categoria", ["Oferta", "Lanches", "Evento", "Materiais", "Outros"])
                data = st.date_input("Data", datetime.now())
            
            if st.form_submit_button("Confirmar Lançamento"):
                valor_final = valor if tipo == "Entrada" else -valor
                nova_linha = pd.DataFrame([[data.strftime("%d/%m/%Y"), desc, cat, tipo, local, valor_final]], columns=df.columns)
                st.session_state.movimentacoes = pd.concat([df, nova_linha], ignore_index=True)
                st.success("Lançado com sucesso!")

    elif menu == "📜 Histórico":
        st.subheader("Histórico de Transações")
        if not df.empty:
            st.dataframe(df.iloc[::-1], use_container_width=True)
            
            # Botão de Exportar Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Baixar Planilha Excel", data=output.getvalue(), file_name="caixa.xlsx")
        else:
            st.info("Nenhum registro encontrado.")
