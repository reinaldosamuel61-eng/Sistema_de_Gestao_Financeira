import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import io
from streamlit_option_menu import option_menu
from fpdf import FPDF
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Caixa Louvor Eterno", page_icon="💰", layout="wide")

# --- 2. ESTILO CSS GERAL (PADRONIZAÇÃO COM ÍCONES CSS) ---
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)
st.markdown(r"""<style>
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css");
.stApp, .main { background-color: #0f172a; color: #f8fafc; }
[data-testid="collapsedControl"] { display: none; }
.historico-card { background-color: #1e293b; border-radius: 15px; padding: 18px; margin-bottom: 12px; border-left: 6px solid transparent; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); }
.card-entrada { border-left-color: #10b981; }
.card-saida { border-left-color: #f43f5e; }
.card-transferencia { border-left-color: #facc15; }
h1, h2, h3, h4, p, span, label { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
div[data-testid="stMetric"] { background-color: #1e293b !important; border-radius: 20px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); border-left: 6px solid #6366f1; }
[data-testid="stMetricValue"] > div { color: #ffffff !important; font-weight: 900; }
[data-testid="stMetricLabel"] > div { color: #94a3b8 !important; text-transform: uppercase; letter-spacing: 1px; }

/* PADRONIZAÇÃO DE TODOS OS BOTÕES */
.stButton>button, .stDownloadButton>button, .nav-btn-premium { width: 100%; border-radius: 12px; height: 3em; background-color: #6366f1 !important; color: white !important; font-weight: 800; border: none !important; transition: 0.3s; text-transform: uppercase; font-size: 14px; display: flex; align-items: center; justify-content: center; text-decoration: none !important; cursor: pointer; gap: 10px; }
.stButton>button:hover, .stDownloadButton>button:hover, .nav-btn-premium:hover { background-color: #4f46e5 !important; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4); color: white !important; }

/* AJUSTES NO UPLOAD PARA USAR ÍCONE BOOTSTRAP */
[data-testid="stFileUploader"] { padding: 0 !important; }
[data-testid="stFileUploadDropzone"] { border: none !important; background-color: transparent !important; padding: 0 !important; min-height: 0 !important; }
[data-testid="stFileUploadDropzone"] > div > svg, [data-testid="stFileUploadDropzone"] > div > small, [data-testid="stFileUploadDropzone"] > div > span { display: none !important; }
[data-testid="stFileUploadDropzone"] button { width: 100% !important; height: 3em !important; border-radius: 12px !important; background-color: #6366f1 !important; color: transparent !important; position: relative !important; font-weight: 800 !important; text-transform: uppercase !important; border: none !important; }
[data-testid="stFileUploadDropzone"] button::after { content: "\F2B8  IMPORTAR BACKUP"; font-family: "bootstrap-icons"; position: absolute !important; top: 0; left: 0; right: 0; bottom: 0; display: flex !important; align-items: center !important; justify-content: center !important; color: white !important; font-size: 14px; }

button[kind="secondary"] { background-color: #1e293b !important; border: 1px solid #475569 !important; color: #f43f5e !important; }
button[kind="secondary"]:hover { background-color: #334155 !important; border-color: #f43f5e !important; }
.stTextInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stNumberInput>div>div>input { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; border-radius: 10px; }
.stDataFrame { background-color: #1e293b; }
div[data-testid="stPopover"] > button { background-color: transparent !important; border: 1px solid #475569 !important; color: #94a3b8 !important; padding: 0px 10px !important; height: 2.2em !important; }

/* FEEDBACK FLUTUANTE PROFISSIONAL */
.feedback-float { position: fixed; top: 80px; left: 50%; transform: translateX(-50%); z-index: 999999; min-width: 320px; background-color: #10b981; color: white; padding: 14px 28px; border-radius: 12px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.7); border: 1px solid rgba(255,255,255,0.3); font-weight: bold; text-align: center; animation: fadeInDown 0.5s ease; pointer-events: none; display: flex; align-items: center; justify-content: center; gap: 10px; }
@keyframes fadeInDown { from { opacity: 0; transform: translate(-50%, -30px); } to { opacity: 1; transform: translate(-50%, 0); } }
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
        d = doc.to_dict()
        d['id'] = doc.id
        data.append(d)
    df = pd.DataFrame(data)
    if not df.empty:
        colunas_ordem = ["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor", "id", "Nota"]
        for col in colunas_ordem:
            if col not in df.columns: df[col] = None
        df = df[colunas_ordem]
    else:
        df = pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor", "id", "Nota"])
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
                sig = f"{r['Data']}|{r['Descrição']}|{r['Valor']}|{r['Local']}"
                existentes.add(sig)
        batch = db.batch()
        cont_novos = 0
        for _, row in df_import.iterrows():
            sig_nova = f"{row['Data']}|{row['Descrição']}|{row['Valor']}|{row['Local']}"
            if sig_nova not in existentes:
                doc_ref = db.collection('movimentacoes').document()
                batch.set(doc_ref, row.to_dict())
                cont_novos += 1
                existentes.add(sig_nova)
        if cont_novos > 0: batch.commit()
        return cont_novos
    return 0

def carregar_categorias():
    if db is None: return {"entrada": ["Oferta"], "saida": ["Lanches"]}
    doc_ref = db.collection('configuracoes').document('categorias')
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        cats_padrao = {"entrada": ["Mensalidade", "Oferta", "Doação", "Cantina", "Venda"], "saida": ["Lanches", "Materiais", "Retiro", "Som", "Ajuda Social"]}
        doc_ref.set(cats_padrao)
        return cats_padrao

def salvar_categorias_db(categorias):
    if db: db.collection('configuracoes').document('categorias').set(categorias)


# --- 4. INICIALIZAÇÃO DE ESTADOS E CALLBACKS ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
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
    st.session_state.msg_icon = "bi bi-trash"
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
                    st.session_state.autenticado = True
                    st.session_state.msg_icon = "bi bi-database-check"
                    st.session_state.msg_sucesso = "BANCO DE DADOS CONECTADO COM SUCESSO!"
                    st.rerun()
                else: st.error("Chave incorreta!")
else:
    if db is None: st.error("Erro de conexão."); st.stop()

    if st.session_state.msg_sucesso:
        st.markdown(f"""<div class="feedback-float"><i class="{st.session_state.msg_icon}"></i> {st.session_state.msg_sucesso}</div>""", unsafe_allow_html=True)
        st.session_state.msg_sucesso = ""

    st.markdown("<h2 style='text-align: center; color: #6366f1; font-weight: 900; margin-top: 0;'>CAIXA LOUVOR ETERNO</h2>", unsafe_allow_html=True)
    
    menu = option_menu(
        menu_title=None,
        options=["Resumo", "Lançar", "Transferir", "Histórico", "Ajustes", "Sair"],
        icons=['house', 'plus-circle', 'arrow-left-right', 'clock-history', 'gear', 'box-arrow-right'],
        default_index=0, orientation="horizontal", key="menu_principal",
        styles={"container": {"padding": "0!important", "background-color": "#1e293b", "border-radius": "15px", "margin-bottom": "20px"},
                "nav-link": {"font-size": "14px", "text-align": "center", "color": "#94a3b8", "font-weight": "bold"},
                "nav-link-selected": {"background-color": "#6366f1", "color": "#ffffff"}}
    )
    
    df = carregar_dados()
    
    especie = 0.0
    pix = 0.0
    if not df.empty:
        especie += df[(df['Local'].isin(['Espécie', 'Dinheiro'])) & (df['Tipo'].isin(['Entrada', 'Saída']))]['Valor'].sum()
        pix += df[(df['Local'] == 'Pix') & (df['Tipo'].isin(['Entrada', 'Saída']))]['Valor'].sum()
        transf_to_pix = df[(df['Tipo'] == 'Transferência') & df['Local'].str.contains('-> Pix', na=False)]['Valor'].sum()
        transf_to_esp = df[(df['Tipo'] == 'Transferência') & df['Local'].str.contains('-> Espécie', na=False)]['Valor'].sum()
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
        st.markdown("<div style='text-align: center; color: #94a3b8; font-style: italic; margin-top: 10px;'><i class='bi bi-info-circle'></i> Use o <b>Histórico</b> para filtrar dados e gerar relatórios PDF.</div>", unsafe_allow_html=True)

    elif menu == "Lançar":
        st.markdown("<h3><i class='bi bi-pencil-square' style='color: #6366f1;'></i> Novo Lançamento</h3>", unsafe_allow_html=True)
        if st.session_state.confirmar_lancamento:
            d = st.session_state.dados_temp
            st.warning("Confirme os dados abaixo:")
            st.info(f"TIPO: {d['Tipo'].upper()} | VALOR: R$ {abs(d['Valor']):,.2f} | LOCAL: {d['Local'].upper()}")
            if d.get('Nota'): st.info(f"NOTA: {d['Nota']}")
            c1, c2 = st.columns(2)
            if c1.button("CONFIRMAR"):
                salvar_lancamento(d); st.session_state.confirmar_lancamento = False; st.session_state.msg_icon="bi bi-check-circle"; st.session_state.msg_sucesso = "LANÇAMENTO REGISTRADO!"; st.rerun()
            if c2.button("CANCELAR"): st.session_state.confirmar_lancamento = False; st.rerun()
        else:
            with st.form("f_lan"):
                col1, col2 = st.columns(2)
                tipo = col1.radio("Tipo", ["Entrada", "Saída"], horizontal=True)
                local = col1.selectbox("Local", ["Espécie", "Pix"])
                valor = col1.number_input("Valor R$", min_value=0.0, format="%.2f")
                desc = col2.text_input("Descrição")
                cat = col2.selectbox("Categoria", st.session_state.categorias["entrada"] if tipo == "Entrada" else st.session_state.categorias["saida"])
                data = col2.date_input("Data", datetime.now(), format="DD/MM/YYYY")
                nota = st.text_input("Nota / Observação (Opcional)")
                if st.form_submit_button("AVANÇAR"):
                    if desc.strip() and valor > 0:
                        st.session_state.dados_temp = {"Data": data.strftime("%d/%m/%Y"), "Descrição": desc.strip().upper(), "Categoria": cat, "Tipo": tipo, "Local": local, "Valor": valor if tipo == "Entrada" else -valor, "Nota": nota.strip()}
                        st.session_state.confirmar_lancamento = True; st.rerun()

    elif menu == "Transferir":
        st.markdown("<h3><i class='bi bi-arrow-left-right' style='color: #6366f1;'></i> Transferência</h3>", unsafe_allow_html=True)
        if st.session_state.confirmar_transf:
            d = st.session_state.dados_transf_temp
            st.warning("Confirme a transferência:")
            st.info(f"DE: {d['origem'].upper()} para {d['destino'].upper()} | VALOR: R$ {d['Valor']:,.2f}")
            c1, c2 = st.columns(2)
            if c1.button("CONFIRMAR"):
                salvar_lancamento({"Data": d['Data'], "Descrição": d['Descrição'], "Categoria": d['Categoria'], "Tipo": d['Tipo'], "Local": d['Local'], "Valor": d['Valor'], "Nota": d['Nota']})
                st.session_state.confirmar_transf = False; st.session_state.msg_icon="bi bi-arrow-left-right"; st.session_state.msg_sucesso = "TRANSFERÊNCIA CONCLUÍDA!"; st.rerun()
            if c2.button("CANCELAR"): st.session_state.confirmar_transf = False; st.rerun()
        else:
            with st.form("f_trans"):
                orig = st.selectbox("De:", ["Espécie", "Pix"])
                val = st.number_input("Valor R$", min_value=0.0, format="%.2f")
                nota_t = st.text_input("Nota (Opcional)")
                if st.form_submit_button("AVANÇAR"):
                    if val > 0:
                        dest = "Pix" if orig == "Espécie" else "Espécie"
                        st.session_state.dados_transf_temp = {"Data": datetime.now().strftime("%d/%m/%Y"), "Descrição": f"TRANSF: {orig.upper()} > {dest.upper()}", "Categoria": "Transferência", "Tipo": "Transferência", "Local": f"{orig} -> {dest}", "Valor": val, "Nota": nota_t.strip(), "origem": orig, "destino": dest}
                        st.session_state.confirmar_transf = True; st.rerun()

    elif menu == "Histórico":
        st.markdown('<div id="topo_hist"></div>', unsafe_allow_html=True)
        st.markdown("<h3><i class='bi bi-file-earmark-bar-graph' style='color: #6366f1;'></i> Histórico Analítico</h3>", unsafe_allow_html=True)
        cf1, cf2, cf3 = st.columns([2, 1.5, 1.5])
        datas_sel = cf1.date_input("Período:", value=[], format="DD/MM/YYYY")
        f_tipo = cf2.selectbox("Tipo:", ["Todos", "Entrada", "Saída", "Transferência"])
        f_cat = cf3.selectbox("Categoria:", ["Todas"] + sorted(df['Categoria'].unique().tolist()) if not df.empty else ["Todas"])
        
        df_f = df.copy()
        if not df_f.empty:
            df_f['Data_dt'] = pd.to_datetime(df_f['Data'], format='%d/%m/%Y', errors='coerce')
            if isinstance(datas_sel, tuple) and len(datas_sel) == 2:
                df_f = df_f[(df_f['Data_dt'].dt.date >= datas_sel[0]) & (df_f['Data_dt'].dt.date <= datas_sel[1])]
            if f_tipo != "Todos": df_f = df_f[df_f['Tipo'] == f_tipo]
            if f_cat != "Todas": df_f = df_f[df_f['Categoria'] == f_cat]
            df_f = df_f.sort_values(by=['Data_dt', 'id'], ascending=[False, False])

        if not df_f.empty:
            def gerar_relatorio_pdf(df_filtrado, dt_sel):
                pdf = FPDF()
                pdf.add_page(); pdf.set_margins(15, 15, 15)
                def s_str(text): return str(text).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, s_str("LOUVOR ETERNO"), ln=True, align='C')
                pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, s_str("RELATÓRIO FINANCEIRO"), ln=True, align='C'); pdf.ln(5)
                df_rep = df_filtrado[df_filtrado['Tipo'] != 'Transferência']
                tg = df_rep[df_rep['Tipo'] == 'Entrada']['Valor'].sum()
                ts = abs(df_rep[df_rep['Tipo'] == 'Saída']['Valor'].sum())
                pdf.set_font("Arial", 'B', 10); pdf.cell(40, 6, "Entradas:", 0, 0); pdf.set_font("Arial", '', 10); pdf.cell(0, 6, s_str(f"R$ {tg:,.2f}"), 0, 1)
                pdf.set_font("Arial", 'B', 10); pdf.cell(40, 6, "Saídas:", 0, 0); pdf.set_font("Arial", '', 10); pdf.cell(0, 6, s_str(f"R$ {ts:,.2f}"), 0, 1)
                pdf.set_font("Arial", 'B', 10); pdf.cell(40, 6, "Saldo:", 0, 0); pdf.set_font("Arial", '', 10); pdf.cell(0, 6, s_str(f"R$ {(tg-ts):,.2f}"), 0, 1); pdf.ln(10)
                pdf.set_font("Arial", 'B', 10); pdf.cell(22, 8, "DATA", 1, 0, 'C'); pdf.cell(78, 8, "DESCRIÇÃO", 1, 0, 'L'); pdf.cell(35, 8, "CATEGORIA", 1, 0, 'C'); pdf.cell(20, 8, "TIPO", 1, 0, 'C'); pdf.cell(25, 8, "VALOR", 1, 1, 'C')
                pdf.set_font("Arial", '', 8)
                for _, r in df_rep.iterrows():
                    tipo_pdf = "ENTRADA" if r['Tipo'] == "Entrada" else "SAIDA"
                    pdf.cell(22, 7, s_str(r['Data']), 1, 0, 'C')
                    pdf.cell(78, 7, s_str(str(r['Descrição'])[:40]), 1, 0, 'L')
                    pdf.cell(35, 7, s_str(str(r['Categoria'])[:15]), 1, 0, 'C')
                    pdf.cell(20, 7, s_str(tipo_pdf), 1, 0, 'C')
                    pdf.cell(25, 7, s_str(f"{r['Valor']:,.2f}"), 1, 1, 'R')
                pdf.ln(20); pdf.cell(60, 5, "________________", 0, 0, 'C'); pdf.cell(60, 5, "________________", 0, 0, 'C'); pdf.cell(60, 5, "________________", 0, 1, 'C')
                pdf.cell(60, 5, "Pastor", 0, 0, 'C'); pdf.cell(60, 5, "Liderança", 0, 0, 'C'); pdf.cell(60, 5, "Tesouraria", 0, 1, 'C')
                return pdf.output(dest="S").encode('latin-1')
            
            cb1, cb2 = st.columns(2)
            with cb1:
                st.download_button(label="GERAR RELATÓRIO PDF", data=gerar_relatorio_pdf(df_f, datas_sel), file_name="relatorio.pdf", type="primary", use_container_width=True)
            with cb2:
                st.markdown('<a href="#graficos_secao" target="_self" class="nav-btn-premium"><i class="bi bi-bar-chart"></i> VER DESEMPENHO</a>', unsafe_allow_html=True)

        st.divider()
        col_tit, col_cnt = st.columns([6, 4])
        col_tit.markdown("#### LANÇAMENTOS")
        col_cnt.markdown(f"<div style='text-align: right; color: #94a3b8;'>TOTAL: {len(df)} | MOSTRANDO: {len(df_f)}</div>", unsafe_allow_html=True)

        for _, row in df_f.iterrows():
            if row['Tipo'] == 'Entrada': cl, cor, pre = "card-entrada", "#10b981", "+"
            elif row['Tipo'] == 'Saída': cl, cor, pre = "card-saida", "#f43f5e", "-"
            else: cl, cor, pre = "card-transferencia", "#facc15", ""
            meses_map = {"01": "Jan", "02": "Fev", "03": "Mar", "04": "Abril", "05": "Maio", "06": "Jun", "07": "Jul", "08": "Ago", "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"}
            mes_nome = meses_map.get(row['Data'][3:5], row['Data'][3:5])
            with st.container():
                st.markdown(f"""<div class="historico-card {cl}"><div style="display: flex; align-items: center; gap: 15px;"><div style="text-align: center; min-width: 50px; border-right: 1px solid rgba(255,255,255,0.1); padding-right: 10px;"><b style="font-size: 1.2rem; display: block;">{row['Data'][:2]}</b><small style="color: #94a3b8; text-transform: uppercase;">{mes_nome}</small></div><div><b style="font-size: 1.05rem; text-transform: uppercase;">{str(row['Descrição']).strip()}</b><br><small style="color: #94a3b8;">{row['Categoria'].upper()} | {row['Local'].upper()}</small></div></div><div style="text-align: right;"><b style="color: {cor}; font-size: 1.3rem;">{pre} R$ {abs(row['Valor']):,.2f}</b></div></div>""", unsafe_allow_html=True)
                c_tools = st.columns([10, 1.2, 1.2])
                with c_tools[1]:
                    nota_val = row.get('Nota')
                    if pd.notna(nota_val) and str(nota_val).strip() != "":
                        with st.popover("💬", use_container_width=True): st.info(f"OBS:\n{nota_val}")
                with c_tools[2]:
                    if st.session_state.id_excluir == row['id']:
                        cx1, cx2 = st.columns(2)
                        cx1.button("Sim", key=f"s_{row['id']}", on_click=confirmar_exclusao, args=(row['id'],), type="primary")
                        cx2.button("Não", key=f"n_{row['id']}", on_click=cancelar_exclusao)
                    else: st.button("Remover", key=f"d_{row['id']}", on_click=lambda id=row['id']: st.session_state.update({"id_excluir": id}))

        st.markdown('<div id="graficos_secao"></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("<div style='text-align: center;'><i class='bi bi-bar-chart-fill' style='font-size: 2rem; color: #10b981;'></i><h2 style='font-weight: 900;'>DESEMPENHO FINANCEIRO</h2></div>", unsafe_allow_html=True)
        df_ent_f = df_f[df_f['Tipo'] == 'Entrada']
        df_sai_f = df_f[df_f['Tipo'] == 'Saída']
        tg_f = df_ent_f['Valor'].sum() if not df_ent_f.empty else 0.0
        ts_f = abs(df_sai_f['Valor'].sum()) if not df_sai_f.empty else 0.0
        cda1, cda2, cda3 = st.columns(3)
        def card_d(t, v, c): st.markdown(f"<div style='background-color: rgba({c}, 0.05); border: 1px solid rgba({c}, 0.3); border-radius: 20px; padding: 20px; text-align: center;'><div style='color: rgb({c}); font-size: 0.8rem; font-weight: 800;'>{t}</div><div style='color: rgb({c}); font-size: 1.8rem; font-weight: 900;'>R$ {v:,.2f}</div></div>", unsafe_allow_html=True)
        with cda1: card_d("GANHOS (+)", tg_f, "16, 185, 129")
        with cda2: card_d("GASTOS (-)", ts_f, "244, 63, 94")
        with cda3: card_d("SALDO PERÍODO", tg_f-ts_f, "99, 102, 241")
        
        st.markdown("<div style='margin-top: 45px;'></div>", unsafe_allow_html=True)
        
        if not df_ent_f.empty or not df_sai_f.empty:
            cg1, spacer, cg2 = st.columns([1, 0.4, 1])
            with cg1:
                if not df_ent_f.empty:
                    st.markdown("<h5 style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>ORIGEM DAS ENTRADAS</h5>", unsafe_allow_html=True)
                    dg = df_ent_f.groupby('Categoria')['Valor'].sum().reset_index()
                    fig = go.Figure(data=[go.Pie(labels=dg['Categoria'], values=dg['Valor'], hole=.65, marker_colors=COLORS_ENTRADA, textinfo='none')])
                    fig.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=40, r=10), height=280, legend=dict(font=dict(color="#f8fafc")))
                    st.plotly_chart(fig, use_container_width=True)
            with cg2:
                if not df_sai_f.empty:
                    st.markdown("<h5 style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>DESTINO DOS GASTOS</h5>", unsafe_allow_html=True)
                    dg = df_sai_f.groupby('Categoria')['Valor'].sum().reset_index()
                    fig = go.Figure(data=[go.Pie(labels=dg['Categoria'], values=abs(dg['Valor']), hole=.65, marker_colors=COLORS_SAIDA, textinfo='none')])
                    fig.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=40), height=280, legend=dict(font=dict(color="#f8fafc")))
                    st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<a href="#topo_hist" target="_self" class="nav-btn-premium" style="margin-top: 60px;"><i class="bi bi-arrow-up-circle"></i> VOLTAR AO TOPO</a>', unsafe_allow_html=True)

    elif menu == "Ajustes":
        st.markdown("<h3><i class='bi bi-sliders'></i> AJUSTES</h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.write("**GANHOS**")
            new_e = st.text_input("NOVA ENTRADA")
            if st.button("ADICIONAR", key="add_e") and new_e:
                st.session_state.categorias["entrada"].append(new_e.strip()); salvar_categorias_db(st.session_state.categorias); st.rerun()
            for c in st.session_state.categorias["entrada"]:
                col_a, col_b = st.columns([8, 2]); col_a.write(f"• {c}")
                if col_b.button("Remover", key=f"de_{c}"):
                    st.session_state.categorias["entrada"].remove(c); salvar_categorias_db(st.session_state.categorias); st.rerun()
        with c2:
            st.write("**GASTOS**")
            new_s = st.text_input("NOVA SAÍDA")
            if st.button("ADICIONAR", key="add_s") and new_s:
                st.session_state.categorias["saida"].append(new_s.strip()); salvar_categorias_db(st.session_state.categorias); st.rerun()
            for c in st.session_state.categorias["saida"]:
                col_a, col_b = st.columns([8, 2]); col_a.write(f"• {c}")
                if col_b.button("Remover", key=f"ds_{c}"):
                    st.session_state.categorias["saida"].remove(c); salvar_categorias_db(st.session_state.categorias); st.rerun()

        st.divider(); st.markdown("#### BACKUP E SINCRONIZAÇÃO")
        if st.session_state.msg_import: 
            st.markdown(f"""<div class="feedback-float"><i class="bi bi-check-circle"></i> {st.session_state.msg_import}</div>""", unsafe_allow_html=True)
            st.session_state.msg_import = ""
        
        b1, b2 = st.columns(2)
        with b1:
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as wr: df.to_excel(wr, index=False)
            st.download_button(label="EXPORTAR BACKUP", data=out.getvalue(), file_name=f"backup_{datetime.now().strftime('%d%m%Y')}.xlsx", type="primary", use_container_width=True)
        with b2:
            up = st.file_uploader("Upload", type=['xlsx', 'csv'], label_visibility="collapsed", key=f"up_{st.session_state.up_key}")
            if up is not None:
                if st.button("CONFIRMAR IMPORTAÇÃO", type="primary", use_container_width=True):
                    try:
                        df_in = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                        df_in = df_in[['Data', 'Descrição', 'Categoria', 'Tipo', 'Local', 'Valor']]
                        df_in['Valor'] = df_in['Valor'].astype(float)
                        novos = salvar_em_lote(df_in, df)
                        st.session_state.msg_import = f"{novos} NOVOS REGISTROS!"; st.session_state.up_key += 1; st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

    elif menu == "Sair":
        st.warning("DESEJA SAIR?")
        if st.button("SIM, SAIR AGORA", type="primary"): st.session_state.autenticado = False; st.rerun()
        st.button("CANCELAR", on_click=cancelar_saida)
