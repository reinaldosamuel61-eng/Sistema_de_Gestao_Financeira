import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import io
from streamlit_option_menu import option_menu
from fpdf import FPDF
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GESTÃO FINANCEIRA", page_icon="💰", layout="wide")

# --- 2. ESTILO CSS GERAL (PADRONIZAÇÃO ABSOLUTA E BOTÕES DE APAGAR) ---
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)
st.markdown(r"""<style>
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css");
.stApp, .main { background-color: #0f172a; color: #f8fafc; }
[data-testid="collapsedControl"] { display: none; }

/* ESTILO DOS CARDS DE HISTÓRICO */
.historico-card { 
    background-color: #1e293b; 
    border-radius: 15px; 
    padding: 18px; 
    margin-bottom: 12px; 
    border-left: 6px solid transparent; 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); 
}
.card-entrada { border-left-color: #10b981; }
.card-saida { border-left-color: #f43f5e; }
.card-transferencia { border-left-color: #facc15; }

/* FONTES E CORES GLOBAIS */
h1, h2, h3, h4, p, span, label { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
div[data-testid="stMetric"] { background-color: #1e293b !important; border-radius: 20px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); border-left: 6px solid #6366f1; }
[data-testid="stMetricValue"] > div { color: #ffffff !important; font-weight: 900; }
[data-testid="stMetricLabel"] > div { color: #94a3b8 !important; text-transform: uppercase; letter-spacing: 1px; }

/* PADRONIZAÇÃO DE TODOS OS BOTÕES DO SISTEMA */
.stButton>button, .stDownloadButton>button, .nav-btn-premium, [data-testid="stFileUploadDropzone"] button { 
    width: 100% !important; border-radius: 12px !important; height: 3.2em !important; 
    background-color: #6366f1 !important; color: white !important; font-weight: 800 !important; 
    border: none !important; transition: 0.3s !important; text-transform: uppercase !important; 
    font-size: 14px !important; display: flex !important; align-items: center !important; 
    justify-content: center !important; text-decoration: none !important; cursor: pointer !important; gap: 10px !important; 
}
.stButton>button:hover, .stDownloadButton>button:hover, .nav-btn-premium:hover, [data-testid="stFileUploadDropzone"] button:hover { 
    background-color: #4f46e5 !important; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4) !important; color: white !important; 
}

/* BOTÃO APAGAR (VISUAL COM TEXTO) */
.delete-btn [data-testid="baseButton-secondary"] {
    background-color: rgba(244, 63, 94, 0.1) !important;
    border: 1px solid #f43f5e !important;
    color: #f43f5e !important;
    height: 2.2em !important;
    width: 100% !important;
    padding: 0 10px !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    font-size: 12px !important;
}
.delete-btn [data-testid="baseButton-secondary"]:hover {
    background-color: #f43f5e !important;
    color: white !important;
}

/* ESTILO DO UPLOAD */
[data-testid="stFileUploader"] { padding: 0 !important; }
[data-testid="stFileUploadDropzone"] { border: none !important; background-color: transparent !important; padding: 0 !important; min-height: 0 !important; }
[data-testid="stFileUploadDropzone"] > div > svg, [data-testid="stFileUploadDropzone"] > div > small, [data-testid="stFileUploadDropzone"] > div > span { display: none !important; }
[data-testid="stFileUploadDropzone"] button { color: transparent !important; position: relative !important; }
[data-testid="stFileUploadDropzone"] button::after { content: "\F2B8  IMPORTAR BACKUP"; font-family: "bootstrap-icons"; position: absolute !important; top: 0; left: 0; right: 0; bottom: 0; display: flex !important; align-items: center !important; justify-content: center !important; color: white !important; font-size: 14px !important; }

/* FORMULÁRIOS E INPUTS */
.stTextInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stNumberInput>div>div>input { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; border-radius: 10px; }
.stDataFrame { background-color: #1e293b; }
div[data-testid="stPopover"] > button { background-color: transparent !important; border: 1px solid #475569 !important; color: #94a3b8 !important; padding: 0px 10px !important; height: 2.2em !important; }

/* FEEDBACKS FLUTUANTES */
.feedback-float { position: fixed; top: 80px; left: 50%; transform: translateX(-50%); z-index: 999999; min-width: 320px; background-color: #10b981; color: white; padding: 14px 28px; border-radius: 12px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6); border: 1px solid rgba(255,255,255,0.3); font-weight: bold; text-align: center; pointer-events: none; display: flex; align-items: center; justify-content: center; gap: 10px; animation: toastAutoClose 3s ease-in-out forwards; }
.feedback-float-delayed { position: fixed; top: 80px; left: 50%; transform: translateX(-50%); z-index: 999998; min-width: 320px; background-color: #6366f1; color: white; padding: 14px 28px; border-radius: 12px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.7); border: 1px solid rgba(255,255,255,0.3); font-weight: bold; text-align: center; pointer-events: none; display: flex; align-items: center; justify-content: center; gap: 10px; opacity: 0; animation: toastAutoClose 3s ease-in-out 3s forwards; }

@keyframes toastAutoClose { 0% { opacity: 0; transform: translate(-50%, -30px); } 15% { opacity: 1; transform: translate(-50%, 0); } 85% { opacity: 1; transform: translate(-50%, 0); } 100% { opacity: 0; transform: translate(-50%, -30px); visibility: hidden; } }
</style>""", unsafe_allow_html=True)

# Cores para os gráficos
COLORS_ENTRADA = ['#10b981', '#34d399', '#6ee7b7', '#059669']
COLORS_SAIDA = ['#f43f5e', '#fb7185', '#fda4af', '#be123c']

# --- 3. INICIALIZAÇÃO FIREBASE ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" not in st.secrets:
                st.error("Configuração '[firebase]' não encontrada.")
                return None
            cred_dict = dict(st.secrets["firebase"])
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.error(f"Erro Firebase: {e}")
            return None
    else:
        return firestore.client()

db = init_firebase()

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_dados():
    if db is None: return pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor", "id", "Nota"])
    docs = db.collection('movimentacoes').stream()
    data = []
    for doc in docs:
        d = doc.to_dict(); d['id'] = doc.id; data.append(d)
    df = pd.DataFrame(data)
    if not df.empty:
        colunas_ordem = ["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor", "id", "Nota"]
        for col in colunas_ordem:
            if col not in df.columns: df[col] = None
        df = df[colunas_ordem]
        df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    else:
        df = pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor", "id", "Nota", "Data_dt"])
    return df

def salvar_lancamento(dados):
    if db: db.collection('movimentacoes').add(dados)

def excluir_lancamento_db(doc_id):
    if db: db.collection('movimentacoes').document(doc_id).delete()

def salvar_em_lote(df_import, df_existente):
    if db:
        existentes = set()
        if not df_existente.empty:
            for _, r in df_existente.iterrows():
                sig = f"{r['Data']}|{r['Descrição']}|{r['Valor']}|{r['Local']}"; existentes.add(sig)
        batch = db.batch(); cont_novos = 0
        for _, row in df_import.iterrows():
            sig_nova = f"{row['Data']}|{row['Descrição']}|{row['Valor']}|{row['Local']}"
            if sig_nova not in existentes:
                doc_ref = db.collection('movimentacoes').document()
                batch.set(doc_ref, row.to_dict()); cont_novos += 1; existentes.add(sig_nova)
        if cont_novos > 0: batch.commit()
        return cont_novos
    return 0

def carregar_categorias():
    if db is None: return {"entrada": ["Oferta"], "saida": ["Lanches"]}
    doc_ref = db.collection('configuracoes').document('categorias')
    doc = doc_ref.get()
    if doc.exists: return doc.to_dict()
    else:
        cats_padrao = {"entrada": ["Mensalidade", "Oferta", "Doação", "Cantina", "Venda"], "saida": ["Lanches", "Materiais", "Retiro", "Som", "Ajuda Social"]}
        doc_ref.set(cats_padrao); return cats_padrao

def salvar_categorias_db(categorias):
    if db: db.collection('configuracoes').document('categorias').set(categorias)

# --- 4. INICIALIZAÇÃO DE ESTADOS ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'login_sequence' not in st.session_state: st.session_state.login_sequence = False
if 'confirmar_lancamento' not in st.session_state: st.session_state.confirmar_lancamento = False
if 'dados_temp' not in st.session_state: st.session_state.dados_temp = {}
if 'confirmar_transf' not in st.session_state: st.session_state.confirmar_transf = False
if 'dados_transf_temp' not in st.session_state: st.session_state.dados_transf_temp = {}
if 'id_excluir' not in st.session_state: st.session_state.id_excluir = None
if 'msg_sucesso' not in st.session_state: st.session_state.msg_sucesso = ""
if 'msg_icon' not in st.session_state: st.session_state.msg_icon = ""
if 'msg_import' not in st.session_state: st.session_state.msg_import = ""
if 'up_key' not in st.session_state: st.session_state.up_key = 0

if 'categorias' not in st.session_state and db is not None:
    st.session_state.categorias = carregar_categorias()

def confirmar_exclusao(doc_id):
    excluir_lancamento_db(doc_id)
    st.session_state.id_excluir = None
    st.session_state.msg_icon = "bi bi-trash-fill"
    st.session_state.msg_sucesso = "LANÇAMENTO EXCLUÍDO COM SUCESSO!"

def cancelar_exclusao(): st.session_state.id_excluir = None
def cancelar_saida(): st.session_state.menu_principal = "Resumo"

# --- 5. SISTEMA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<style>.main .block-container { display: flex; flex-direction: column; justify-content: center; min-height: 85vh; } div[data-testid='stVerticalBlockBorderWrapper'] { background-color: #1e293b !important; border-radius: 15px !important; padding: 25px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important; border: none !important; border-left: 6px solid #6366f1 !important; }</style>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-weight: 900; margin-bottom: 40px; color: #f8fafc; letter-spacing: 1px;'>SISTEMA DE GESTÃO FINANCEIRA</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #f8fafc; margin-bottom: 25px;'><i class='bi bi-lock-fill' style='color: #6366f1; margin-right: 10px;'></i>Acesso Restrito</h4>", unsafe_allow_html=True)
            chave = st.text_input("Senha", type="password", placeholder="Digite a senha de acesso...", label_visibility="collapsed", autocomplete="new-password")
            if st.button("ACESSAR SISTEMA"):
                if chave == st.secrets.get("chave_grupo", "admin"):
                    st.session_state.autenticado = True; st.session_state.login_sequence = True; st.rerun()
                else: st.error("Senha incorreta!")
else:
    if db is None: st.error("Erro de conexão."); st.stop()

    if st.session_state.login_sequence:
        st.markdown(r"""<div class="feedback-float"><i class="bi bi-person-check"></i> BEM-VINDO AO SISTEMA!</div>""", unsafe_allow_html=True)
        st.markdown(r"""<div class="feedback-float-delayed"><i class="bi bi-database-check"></i> BANCO DE DADOS CONECTADO COM SUCESSO!</div>""", unsafe_allow_html=True)
        st.session_state.login_sequence = False
    
    if st.session_state.msg_sucesso:
        st.markdown(f"""<div class="feedback-float"><i class="{st.session_state.msg_icon}"></i> {st.session_state.msg_sucesso}</div>""", unsafe_allow_html=True)
        st.session_state.msg_sucesso = ""

    st.markdown("<h2 style='text-align: center; color: #6366f1; font-weight: 900; margin-top: 0;'>CAIXA LOUVOR ETERNO</h2>", unsafe_allow_html=True)
    
    menu = option_menu(
        menu_title=None,
        options=["Resumo", "Histórico", "Lançar", "Transferir", "Ajustes", "Sair"],
        icons=['house', 'clock-history', 'plus-circle', 'arrow-left-right', 'gear', 'box-arrow-right'],
        default_index=0, orientation="horizontal", key="menu_principal",
        styles={"container": {"padding": "0!important", "background-color": "#1e293b", "border-radius": "15px", "margin-bottom": "20px"},
                "nav-link": {"font-size": "14px", "text-align": "center", "color": "#94a3b8", "font-weight": "bold"},
                "nav-link-selected": {"background-color": "#6366f1", "color": "#ffffff"}}
    )
    
    df_geral = carregar_dados()

    # Saldo Real (Soma de tudo)
    especie = 0.0; pix = 0.0
    if not df_geral.empty:
        especie += df_geral[(df_geral['Local'].isin(['Espécie', 'Dinheiro'])) & (df_geral['Tipo'].isin(['Entrada', 'Saída']))]['Valor'].sum()
        pix += df_geral[(df_geral['Local'] == 'Pix') & (df_geral['Tipo'].isin(['Entrada', 'Saída']))]['Valor'].sum()
        transf_to_pix = df_geral[(df_geral['Tipo'] == 'Transferência') & df_geral['Local'].str.contains('-> Pix', na=False)]['Valor'].sum()
        transf_to_esp = df_geral[(df_geral['Tipo'] == 'Transferência') & df_geral['Local'].str.contains('-> Espécie', na=False)]['Valor'].sum()
        especie = especie - transf_to_pix + transf_to_esp
        pix = pix - transf_to_esp + transf_to_pix

    if menu == "Resumo":
        def cartao_customizado(icone, titulo, valor):
            st.markdown(f"""<div style="background-color: #1e293b; border-radius: 20px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); border-left: 6px solid #6366f1;"><div style="color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; font-size: 0.9rem; margin-bottom: 8px;"><i class="{icone}" style="font-size: 1.2rem; margin-right: 8px; color: #f8fafc;"></i>{titulo}</div><div style="color: #ffffff; font-weight: 900; font-size: 2rem;">{valor}</div></div>""", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: cartao_customizado("bi bi-cash-stack", "Saldo Espécie", f"R$ {especie:,.2f}")
        with c2: cartao_customizado("bi bi-phone", "Saldo Pix", f"R$ {pix:,.2f}")
        with c3: cartao_customizado("bi bi-bank", "Saldo Total", f"R$ {especie + pix:,.2f}")
        st.divider()

    elif menu == "Histórico":
        st.markdown('<div id="topo_hist"></div>', unsafe_allow_html=True)
        st.markdown("<h3><i class='bi bi-file-earmark-bar-graph' style='color: #6366f1;'></i> Histórico Analítico</h3>", unsafe_allow_html=True)
        
        cf1, cf2, cf3 = st.columns([2, 1.5, 1.5])
        if not df_geral.empty:
            min_data_db = df_geral['Data_dt'].min().date()
            max_data_db = df_geral['Data_dt'].max().date()
            default_datas = (min_data_db, max_data_db)
        else:
            hoje = date.today(); default_datas = (hoje.replace(day=1), hoje)
        
        datas_sel = cf1.date_input("Período:", value=default_datas, format="DD/MM/YYYY")
        f_tipo = cf2.selectbox("Tipo:", ["Todos", "Entrada", "Saída", "Transferência"])
        f_cat = cf3.selectbox("Categoria:", ["Todas"] + sorted(df_geral['Categoria'].unique().tolist()) if not df_geral.empty else ["Todas"])
        
        df_f = df_geral.copy(); saldo_anterior = 0.0
        if not df_geral.empty:
            if isinstance(datas_sel, (list, tuple)) and len(datas_sel) == 2:
                data_ini, data_fim = datas_sel
                df_anterior = df_geral[df_geral['Data_dt'].dt.date < data_ini]
                saldo_anterior = df_anterior[df_anterior['Tipo'].isin(['Entrada', 'Saída'])]['Valor'].sum()
                df_f = df_geral[(df_geral['Data_dt'].dt.date >= data_ini) & (df_geral['Data_dt'].dt.date <= data_fim)]
            elif isinstance(datas_sel, (list, tuple)) and len(datas_sel) == 1:
                df_f = df_geral[df_geral['Data_dt'].dt.date == datas_sel[0]]
            
            if f_tipo != "Todos": df_f = df_f[df_f['Tipo'] == f_tipo]
            if f_cat != "Todas": df_f = df_f[df_f['Categoria'] == f_cat]
            df_f = df_f.sort_values(by=['Data_dt', 'id'], ascending=[True, True])

        ent_periodo = df_f[df_f['Tipo'] == 'Entrada']['Valor'].sum()
        sai_periodo = abs(df_f[df_f['Tipo'] == 'Saída']['Valor'].sum())
        saldo_liquido_atual = saldo_anterior + ent_periodo - sai_periodo

        st.markdown("#### Resumo do Período")
        cda1, cda2, cda3, cda4 = st.columns(4)
        def card_hist(t, v, c, icon): st.markdown(f"<div style='background-color: rgba({c}, 0.05); border: 1px solid rgba({c}, 0.3); border-radius: 15px; padding: 15px; text-align: center;'><div style='color: rgb({c}); font-size: 0.7rem; font-weight: 800; text-transform: uppercase;'><i class='bi bi-{icon}'></i> {t}</div><div style='color: white; font-size: 1.4rem; font-weight: 900;'>R$ {v:,.2f}</div></div>", unsafe_allow_html=True)
        with cda1: card_hist("Saldo Inicial", saldo_anterior, "148, 163, 184", "skip-start-fill")
        with cda2: card_hist("Entradas (+)", ent_periodo, "16, 185, 129", "plus-circle")
        with cda3: card_hist("Saídas (-)", sai_periodo, "244, 63, 94", "dash-circle")
        with cda4: card_hist("Saldo Final", saldo_liquido_atual, "99, 102, 241", "wallet2")

        if not df_f.empty:
            def gerar_relatorio_pdf_pro(df_filtrado, dt_sel, s_ant):
                pdf = FPDF(); pdf.add_page(); pdf.set_margins(15, 15, 15)
                def s_str(text): return str(text).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font("Arial", 'B', 18); pdf.cell(0, 12, s_str("LOUVOR ETERNO"), ln=True, align='C')
                pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, s_str("RELATÓRIO FINANCEIRO GERAL"), ln=True, align='C')
                if isinstance(dt_sel, (list, tuple)) and len(dt_sel) == 2:
                    pdf.set_font("Arial", 'I', 10); pdf.cell(0, 6, s_str(f"Período: {dt_sel[0].strftime('%d/%m/%Y')} a {dt_sel[1].strftime('%d/%m/%Y')}"), ln=True, align='C')
                pdf.ln(8); pdf.set_font("Arial", 'B', 11); pdf.cell(55, 7, s_str("Saldo do Período Anterior:"), 0, 0); pdf.set_font("Arial", '', 11); pdf.cell(0, 7, s_str(f"R$ {s_ant:,.2f}"), 0, 1)
                df_rep = df_filtrado[df_filtrado['Tipo'] != 'Transferência']; tg = df_rep[df_rep['Tipo'] == 'Entrada']['Valor'].sum(); ts = abs(df_rep[df_rep['Tipo'] == 'Saída']['Valor'].sum())
                pdf.set_font("Arial", 'B', 11); pdf.cell(55, 7, s_str("Total de Entradas:"), 0, 0); pdf.set_font("Arial", '', 11); pdf.cell(0, 7, s_str(f"R$ {tg:,.2f}"), 0, 1)
                pdf.set_font("Arial", 'B', 11); pdf.cell(55, 7, s_str("Total de Saídas:"), 0, 0); pdf.set_font("Arial", '', 11); pdf.cell(0, 7, s_str(f"R$ {ts:,.2f}"), 0, 1)
                pdf.set_font("Arial", 'B', 11); pdf.cell(55, 7, s_str("Saldo Líquido Atual:"), 0, 0); pdf.set_font("Arial", '', 11); pdf.cell(0, 7, s_str(f"R$ {(s_ant+tg-ts):,.2f}"), 0, 1); pdf.ln(10)
                pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, s_str("MOVIMENTAÇÕES DETALHADAS"), 0, 1, 'L'); pdf.ln(2)
                pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 10)
                pdf.cell(25, 10, s_str("DATA"), 1, 0, 'C', True); pdf.cell(75, 10, s_str("DESCRIÇÃO"), 1, 0, 'L', True); pdf.cell(40, 10, s_str("CATEGORIA"), 1, 0, 'C', True); pdf.cell(20, 10, s_str("TIPO"), 1, 0, 'C', True); pdf.cell(20, 10, s_str("VALOR"), 1, 1, 'C', True)
                pdf.set_font("Arial", '', 9); cur_m_y = None; meses_ext = {1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL", 5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO", 9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"}
                for _, r in df_rep.iterrows():
                    m_y = f"{meses_ext[r['Data_dt'].month]} {r['Data_dt'].year}"
                    if m_y != cur_m_y:
                        pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(245, 245, 245); pdf.cell(180, 8, s_str(m_y), 1, 1, 'L', True); cur_m_y = m_y; pdf.set_font("Arial", '', 9)
                    tipo_pdf = "ENTRADA" if r['Tipo'] == "Entrada" else "SAIDA"
                    pdf.cell(25, 8, s_str(r['Data']), 1, 0, 'C'); pdf.cell(75, 8, s_str(str(r['Descrição'])[:40]), 1, 0, 'L'); pdf.cell(40, 8, s_str(str(r['Categoria'])[:18]), 1, 0, 'C'); pdf.cell(20, 8, s_str(tipo_pdf), 1, 0, 'C'); pdf.cell(20, 8, s_str(f"{r['Valor']:,.2f}"), 1, 1, 'R')
                pdf.ln(20); pdf.set_font("Arial", '', 10); pdf.cell(60, 5, "_______________________", 0, 0, 'C'); pdf.cell(60, 5, "_______________________", 0, 0, 'C'); pdf.cell(60, 5, "_______________________", 0, 1, 'C')
                pdf.cell(60, 5, s_str("Pastor"), 0, 0, 'C'); pdf.cell(60, 5, s_str("Líder de Jovens"), 0, 0, 'C'); pdf.cell(60, 5, s_str("Tesoureiro"), 0, 1, 'C'); return pdf.output(dest="S").encode('latin-1')
            st.markdown("<br>", unsafe_allow_html=True)
            cb1, cb2 = st.columns(2)
            with cb1: st.download_button(label="📄 GERAR RELATÓRIO PDF", data=gerar_relatorio_pdf_pro(df_f, datas_sel, saldo_anterior), file_name=f"Relatorio_{datetime.now().strftime('%d%m%Y')}.pdf", type="primary", use_container_width=True)
            with cb2: st.markdown('<a href="#graficos_secao" target="_self" class="nav-btn-premium"><i class="bi bi-bar-chart"></i> VER DESEMPENHO</a>', unsafe_allow_html=True)
        
        st.divider()
        st.markdown(f"<div style='text-align: right; color: #94a3b8; font-weight: 900; letter-spacing: 1px; font-size: 0.8rem; margin-bottom: 15px;'>TOTAL: {len(df_geral)} | MOSTRANDO: {len(df_f)}</div>", unsafe_allow_html=True)
        
        df_display = df_f.sort_values(by=['Data_dt', 'id'], ascending=[False, False])
        for _, row in df_display.iterrows():
            if row['Tipo'] == 'Entrada': cl, cor, pre = "card-entrada", "#10b981", "+"
            elif row['Tipo'] == 'Saída': cl, cor, pre = "card-saida", "#f43f5e", "-"
            else: cl, cor, pre = "card-transferencia", "#facc15", ""
            mes_curto = {"01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr", "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago", "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"}
            m_n = mes_curto.get(row['Data'][3:5], row['Data'][3:5])
            with st.container():
                st.markdown(f"""<div class="historico-card {cl}"><div style="display: flex; align-items: center; gap: 15px;"><div style="text-align: center; min-width: 50px; border-right: 1px solid rgba(255,255,255,0.1); padding-right: 10px;"><b style="font-size: 1.2rem; display: block;">{row['Data'][:2]}</b><small style="color: #94a3b8; text-transform: uppercase;">{m_n}</small></div><div><b style="font-size: 1.05rem; text-transform: uppercase;">{str(row['Descrição']).strip()}</b><br><small style="color: #94a3b8;">{row['Categoria'].upper()} | {row['Local'].upper()}</small></div></div><div style="text-align: right;"><b style="color: {cor}; font-size: 1.3rem;">{pre} R$ {abs(row['Valor']):,.2f}</b></div></div>""", unsafe_allow_html=True)
                c_tools = st.columns([10, 1.2, 1.2])
                with c_tools[1]:
                    if pd.notna(row.get('Nota')) and str(row['Nota']).strip() != "":
                        with st.popover("💬", use_container_width=True): st.info(f"OBS:\n{row['Nota']}")
                with c_tools[2]:
                    if st.session_state.id_excluir == row['id']:
                        cx1, cx2 = st.columns(2)
                        cx1.button("✓", key=f"s_{row['id']}", on_click=confirmar_exclusao, args=(row['id'],), type="primary")
                        cx2.button("✗", key=f"n_{row['id']}", on_click=cancelar_exclusao)
                    else:
                        st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                        st.button("APAGAR", key=f"d_{row['id']}", on_click=lambda id=row['id']: st.session_state.update({"id_excluir": id}))
                        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div id="graficos_secao"></div>', unsafe_allow_html=True); st.divider()
        st.markdown("<div style='text-align: center;'><i class='bi bi-bar-chart-fill' style='font-size: 2rem; color: #10b981;'></i><h2 style='font-weight: 900;'>DESEMPENHO FINANCEIRO</h2></div>", unsafe_allow_html=True)
        if not df_f[df_f['Tipo'] == 'Entrada'].empty or not df_f[df_f['Tipo'] == 'Saída'].empty:
            cg1, spacer_g, cg2 = st.columns([1, 0.2, 1])
            with cg1:
                dg_ent = df_f[df_f['Tipo'] == 'Entrada'].groupby('Categoria')['Valor'].sum().sort_values(ascending=False).reset_index()
                if not dg_ent.empty:
                    st.markdown("<h5 style='text-align: center; color: #10b981; font-size: 0.8rem;'>ORIGEM DAS ENTRADAS (R$)</h5>", unsafe_allow_html=True)
                    fig = go.Figure(go.Bar(x=dg_ent['Categoria'], y=dg_ent['Valor'], marker_color='#10b981', text=[f"R$ {v:,.2f}" for v in dg_ent['Valor']], textposition='auto'))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), height=350, font=dict(color="#f8fafc"), xaxis=dict(showgrid=False, tickangle=-45), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
                    st.plotly_chart(fig, use_container_width=True)
            with cg2:
                dg_sai = df_f[df_f['Tipo'] == 'Saída'].groupby('Categoria')['Valor'].apply(lambda x: abs(x.sum())).sort_values(ascending=False).reset_index()
                if not dg_sai.empty:
                    st.markdown("<h5 style='text-align: center; color: #f43f5e; font-size: 0.8rem;'>DESTINO DOS GASTOS (R$)</h5>", unsafe_allow_html=True)
                    fig = go.Figure(go.Bar(x=dg_sai['Categoria'], y=dg_sai['Valor'], marker_color='#f43f5e', text=[f"R$ {v:,.2f}" for v in dg_sai['Valor']], textposition='auto'))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), height=350, font=dict(color="#f8fafc"), xaxis=dict(showgrid=False, tickangle=-45), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
                    st.plotly_chart(fig, use_container_width=True)
        st.markdown('<a href="#topo_hist" target="_self" class="nav-btn-premium" style="margin-top: 60px;"><i class="bi bi-arrow-up-circle"></i> VOLTAR AO TOPO</a>', unsafe_allow_html=True)

    elif menu == "Lançar":
        st.markdown("<h3><i class='bi bi-pencil-square' style='color: #6366f1;'></i> Novo Lançamento</h3>", unsafe_allow_html=True)
        tipo_sel = st.radio("TIPO", ["ENTRADA", "SAÍDA"], horizontal=True, key="radio_tipo_lanc")
        if st.session_state.confirmar_lancamento:
            d = st.session_state.dados_temp; st.warning("Verifique os dados antes de confirmar:")
            st.info(f"TIPO: {d['Tipo'].upper()} | VALOR: R$ {abs(d['Valor']):,.2f} | LOCAL: {d['Local'].upper()}"); c1, c2 = st.columns(2)
            if c1.button("✅ CONFIRMAR"): salvar_lancamento(d); st.session_state.confirmar_lancamento = False; st.session_state.msg_icon="bi bi-check-circle-fill"; st.session_state.msg_sucesso = "LANÇAMENTO REGISTRADO!"; st.rerun()
            if c2.button("❌ CANCELAR"): st.session_state.confirmar_lancamento = False; st.rerun()
        else:
            with st.form("f_lan_new"):
                col1, col2 = st.columns(2)
                local = col1.selectbox("LOCAL", ["Espécie", "Pix"])
                valor = col1.number_input("VALOR R$", min_value=0.0, format="%.2f")
                desc = col2.text_input("DESCRIÇÃO")
                cats_list = st.session_state.categorias["entrada"] if tipo_sel == "ENTRADA" else st.session_state.categorias["saida"]
                cat = col2.selectbox("CATEGORIA", cats_list)
                data = col2.date_input("DATA", date.today(), format="DD/MM/YYYY")
                nota = st.text_input("Nota (Opcional)")
                if st.form_submit_button("AVANÇAR"):
                    if desc.strip() and valor > 0:
                        tipo_db = "Entrada" if tipo_sel == "ENTRADA" else "Saída"
                        st.session_state.dados_temp = {"Data": data.strftime("%d/%m/%Y"), "Descrição": desc.strip().upper(), "Categoria": cat, "Tipo": tipo_db, "Local": local, "Valor": valor if tipo_db == "Entrada" else -valor, "Nota": nota.strip()}; st.session_state.confirmar_lancamento = True; st.rerun()

    elif menu == "Transferir":
        st.markdown("<h3><i class='bi bi-arrow-left-right' style='color: #6366f1;'></i> Transferência</h3>", unsafe_allow_html=True)
        if st.session_state.confirmar_transf:
            d = st.session_state.dados_transf_temp; st.warning("Confirme a transferência:")
            st.info(f"DE: {d['origem'].upper()} PARA: {d['destino'].upper()} | VALOR: R$ {d['Valor']:,.2f}"); c1, c2 = st.columns(2)
            if c1.button("✅ CONFIRMAR"): salvar_lancamento({"Data": d['Data'], "Descrição": d['Descrição'], "Categoria": d['Categoria'], "Tipo": d['Tipo'], "Local": d['Local'], "Valor": d['Valor'], "Nota": d['Nota']}); st.session_state.confirmar_transf = False; st.session_state.msg_icon="bi bi-arrow-repeat"; st.session_state.msg_sucesso = "TRANSFERÊNCIA CONCLUÍDA!"; st.rerun()
            if c2.button("❌ CANCELAR"): st.session_state.confirmar_transf = False; st.rerun()
        else:
            with st.form("f_trans"):
                orig = st.selectbox("De:", ["Espécie", "Pix"]); val = st.number_input("Valor R$", min_value=0.0, format="%.2f"); nota_t = st.text_input("Nota (Opcional)")
                if st.form_submit_button("AVANÇAR"):
                    if val > 0:
                        dest = "Pix" if orig == "Espécie" else "Espécie"; st.session_state.dados_transf_temp = {"Data": date.today().strftime("%d/%m/%Y"), "Descrição": f"TRANSF: {orig.upper()} > {dest.upper()}", "Categoria": "Transferência", "Tipo": "Transferência", "Local": f"{orig} -> {dest}", "Valor": val, "Nota": nota_t.strip(), "origem": orig, "destino": dest}; st.session_state.confirmar_transf = True; st.rerun()

    elif menu == "Ajustes":
        st.markdown("<h3><i class='bi bi-sliders'></i> AJUSTES</h3>", unsafe_allow_html=True); c1, c2 = st.columns(2)
        with c1:
            st.write("**GANHOS**"); new_e = st.text_input("NOVA ENTRADA")
            if st.button("ADICIONAR", key="add_e") and new_e: st.session_state.categorias["entrada"].append(new_e.strip()); salvar_categorias_db(st.session_state.categorias); st.rerun()
            for c in st.session_state.categorias["entrada"]:
                col_a, col_b = st.columns([8, 2]); col_a.write(f"• {c}")
                with col_b: st.markdown('<div class="delete-btn">', unsafe_allow_html=True); st.button("APAGAR", key=f"de_{c}", on_click=lambda cat=c: (st.session_state.categorias["entrada"].remove(cat), salvar_categorias_db(st.session_state.categorias))); st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.write("**GASTOS**"); new_s = st.text_input("NOVA SAÍDA")
            if st.button("ADICIONAR", key="add_s") and new_s: st.session_state.categorias["saida"].append(new_s.strip()); salvar_categorias_db(st.session_state.categorias); st.rerun()
            for c in st.session_state.categorias["saida"]:
                col_a, col_b = st.columns([8, 2]); col_a.write(f"• {c}")
                with col_b: st.markdown('<div class="delete-btn">', unsafe_allow_html=True); st.button("APAGAR", key=f"ds_{c}", on_click=lambda cat=c: (st.session_state.categorias["saida"].remove(cat), salvar_categorias_db(st.session_state.categorias))); st.markdown('</div>', unsafe_allow_html=True)
        st.divider(); st.markdown("#### BACKUP E SINCRONIZAÇÃO")
        if st.session_state.msg_import: st.markdown(f"""<div class="feedback-float"><i class="bi bi-cloud-check"></i> {st.session_state.msg_import}</div>""", unsafe_allow_html=True); st.session_state.msg_import = ""
        b1, b2 = st.columns(2)
        with b1: out = io.BytesIO(); df_geral.to_excel(out, index=False); st.download_button(label="EXPORTAR BACKUP", data=out.getvalue(), file_name=f"backup_{datetime.now().strftime('%d%m%Y')}.xlsx", type="primary", use_container_width=True)
        with b2:
            up = st.file_uploader("Upload", type=['xlsx', 'csv'], label_visibility="collapsed", key=f"up_{st.session_state.up_key}")
            if up is not None:
                if st.button("✅ CONFIRMAR IMPORTAÇÃO", type="primary", use_container_width=True):
                    try:
                        df_in = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up); df_in['Valor'] = df_in['Valor'].astype(float); novos = salvar_em_lote(df_in, df_geral)
                        st.session_state.msg_icon = "bi bi-cloud-download"; st.session_state.msg_sucesso = f"{novos} REGISTROS IMPORTADOS!"; st.session_state.up_key += 1; st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

    elif menu == "Sair":
        st.warning("Deseja terminar a sessão?"); col1, col2 = st.columns(2)
        if col1.button("SIM, SAIR AGORA", type="primary"): st.session_state.autenticado = False; st.rerun()
        col2.button("CANCELAR", on_click=cancelar_saida)
