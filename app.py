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

# --- 2. ESTILO CSS GERAL E CONFIGURAÇÕES ---
st.markdown("""
    <meta name="google" content="notranslate">
    <style>
    @import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css");
    .stApp, .main { background-color: #0f172a; color: #f8fafc; }
    [data-testid="collapsedControl"] { display: none; }
    h1, h2, h3, h4, p, span, label { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    div[data-testid="stMetric"] { background-color: #1e293b !important; border-radius: 20px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); border-left: 6px solid #6366f1; }
    [data-testid="stMetricValue"] > div { color: #ffffff !important; font-weight: 900; }
    [data-testid="stMetricLabel"] > div { color: #94a3b8 !important; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button, .stDownloadButton>button { width: 100%; border-radius: 12px; height: 3em; background-color: #6366f1; color: white !important; font-weight: 800; border: none; transition: 0.3s; text-transform: uppercase; }
    .stButton>button:hover, .stDownloadButton>button:hover { background-color: #4f46e5; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4); }
    button[kind="secondary"] { background-color: #1e293b !important; border: 1px solid #475569 !important; color: #f43f5e !important; }
    button[kind="secondary"]:hover { background-color: #334155 !important; border-color: #f43f5e !important; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stNumberInput>div>div>input { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; border-radius: 10px; }
    .stDataFrame { background-color: #1e293b; }
    
    /* CSS DO BOTÃO UPLOAD/IMPORTAR */
    [data-testid="stFileUploader"] { padding: 0 !important; margin-bottom: 0 !important; }
    [data-testid="stFileUploadDropzone"] { border: none !important; background-color: transparent !important; padding: 0 !important; min-height: 0 !important; }
    [data-testid="stFileUploadDropzone"] > div > svg, [data-testid="stFileUploadDropzone"] > div > small, [data-testid="stFileUploadDropzone"] > div > span { display: none !important; }
    [data-testid="stFileUploadDropzone"] button { width: 100% !important; height: 3em !important; border-radius: 12px !important; background-color: #6366f1 !important; border: none !important; color: transparent !important; position: relative !important; display: block !important; margin: 0 !important; padding: 0 !important; box-shadow: none !important; }
    [data-testid="stFileUploadDropzone"] button:hover { background-color: #4f46e5 !important; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4) !important; }
    [data-testid="stFileUploadDropzone"] button::after { content: "📥 IMPORTAR BACKUP"; position: absolute !important; top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important; display: flex !important; align-items: center !important; justify-content: center !important; color: white !important; font-size: 14px !important; font-weight: 800 !important; text-transform: uppercase !important; }
    </style>
""", unsafe_allow_html=True)

# Cores para os gráficos
COLORS_ENTRADA = ['#10b981', '#34d399', '#6ee7b7', '#059669']
COLORS_SAIDA = ['#f43f5e', '#fb7185', '#fda4af', '#be123c']

# --- 3. INICIALIZAÇÃO FIREBASE ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" not in st.secrets:
                st.error("Configuração '[firebase]' não encontrada no secrets.toml.")
                return None
            cred_dict = dict(st.secrets["firebase"])
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            st.error(f"Erro ao ligar ao Firebase: {e}")
            return None
    else:
        return firestore.client()

db = init_firebase()

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_dados():
    if db is None: return pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor", "id"])
    docs = db.collection('movimentacoes').stream()
    data = []
    for doc in docs:
        d = doc.to_dict()
        d['id'] = doc.id
        data.append(d)
    df = pd.DataFrame(data)
    if not df.empty:
        colunas_ordem = ["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor", "id"]
        for col in colunas_ordem:
            if col not in df.columns: df[col] = None
        df = df[colunas_ordem]
    else:
        df = pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor", "id"])
    return df

def salvar_lancamento(dados):
    if db: db.collection('movimentacoes').add(dados)

def excluir_lancamento_db(doc_id):
    if db: db.collection('movimentacoes').document(doc_id).delete()

def salvar_em_lote(df_import, df_existente):
    """Salva múltiplos registros ignorando duplicados (mesma data, descrição, valor e local)"""
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
    if db is None: 
        return {"entrada": ["Mensalidade", "Oferta"], "saida": ["Lanches", "Materiais"]}
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


# --- 4. INICIALIZAÇÃO DE ESTADOS ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'confirmar_lancamento' not in st.session_state: st.session_state.confirmar_lancamento = False
if 'dados_temp' not in st.session_state: st.session_state.dados_temp = {}
if 'confirmar_transf' not in st.session_state: st.session_state.confirmar_transf = False
if 'dados_transf_temp' not in st.session_state: st.session_state.dados_transf_temp = {}
if 'id_excluir' not in st.session_state: st.session_state.id_excluir = None
if 'msg_sucesso' not in st.session_state: st.session_state.msg_sucesso = ""
if 'msg_import' not in st.session_state: st.session_state.msg_import = ""
if 'confirmar_importacao' not in st.session_state: st.session_state.confirmar_importacao = False
if 'up_key' not in st.session_state: st.session_state.up_key = 0
if 'cat_pendente_add' not in st.session_state: st.session_state.cat_pendente_add = None
if 'cat_pendente_del' not in st.session_state: st.session_state.cat_pendente_del = None

if 'categorias' not in st.session_state and db is not None:
    st.session_state.categorias = carregar_categorias()

# Callbacks
def pedir_exclusao(doc_id): st.session_state.id_excluir = doc_id
def cancelar_exclusao(): st.session_state.id_excluir = None
def confirmar_exclusao(doc_id):
    excluir_lancamento_db(doc_id)
    st.session_state.id_excluir = None
    st.session_state.msg_sucesso = "🗑️ Lançamento excluído com sucesso!"

def cancelar_saida():
    st.session_state.menu_principal = "Resumo"

def resetar_estado_exportacao():
    st.session_state.confirmar_exportacao = False
    st.session_state.msg_sucesso = "✅ Arquivo exportado com sucesso!"


# --- 5. SISTEMA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center; margin-top: 50px; font-weight: 900;'>CAIXA LOUVOR ETERNO</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.container(border=True):
            chave = st.text_input("Senha", type="password", placeholder="Digite a senha de acesso...", label_visibility="collapsed", autocomplete="new-password")
            if st.button("ACESSAR SISTEMA"):
                senha_esperada = "admin"
                try: senha_esperada = st.secrets.get("chave_grupo", "admin")
                except: pass 
                if chave == senha_esperada:
                    st.session_state.autenticado = True; st.rerun()
                else:
                    st.error("Chave incorreta!")
else:
    if db is None:
        st.error("🔥 Conexão com o Banco de Dados falhou. Verifique o secrets.")
        st.stop()

    st.markdown("<h2 style='text-align: center; color: #6366f1; font-weight: 900; margin-top: 0;'>CAIXA LOUVOR ETERNO</h2>", unsafe_allow_html=True)
    
    menu = option_menu(
        menu_title=None,
        options=["Resumo", "Lançar", "Transferir", "Histórico", "Ajustes", "Sair"],
        icons=['house', 'plus-circle', 'arrow-left-right', 'clock-history', 'gear', 'box-arrow-right'],
        default_index=0,
        orientation="horizontal",
        key="menu_principal",
        styles={
            "container": {"padding": "0!important", "background-color": "#1e293b", "border-radius": "15px", "margin-bottom": "20px"},
            "icon": {"color": "#f8fafc", "font-size": "18px"}, 
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "color": "#94a3b8", "font-weight": "bold"},
            "nav-link-selected": {"background-color": "#6366f1", "color": "#ffffff"},
        }
    )
    
    if 'menu_atual' not in st.session_state: st.session_state.menu_atual = menu
    if st.session_state.menu_atual != menu:
        st.session_state.confirmar_importacao = False
        st.session_state.cat_pendente_add = None
        st.session_state.cat_pendente_del = None
        st.session_state.id_excluir = None
        st.session_state.menu_atual = menu

    df = carregar_dados()
    
    especie = 0.0
    pix = 0.0
    if not df.empty:
        mask_especie = df['Local'].isin(['Espécie', 'Dinheiro'])
        mask_pix = df['Local'] == 'Pix'
        especie += df[mask_especie & df['Tipo'].isin(['Entrada', 'Saída'])]['Valor'].sum()
        pix += df[mask_pix & df['Tipo'].isin(['Entrada', 'Saída'])]['Valor'].sum()
        transf_to_pix = df[(df['Tipo'] == 'Transferência') & df['Local'].isin(['Espécie -> Pix', 'Dinheiro -> Pix'])]['Valor'].sum()
        transf_to_especie = df[(df['Tipo'] == 'Transferência') & df['Local'].isin(['Pix -> Espécie', 'Pix -> Dinheiro'])]['Valor'].sum()
        especie = especie - transf_to_pix + transf_to_especie
        pix = pix - transf_to_especie + transf_to_pix

    if menu not in ["Lançar", "Transferir", "Histórico", "Ajustes"]:
        st.session_state.msg_sucesso = ""; st.session_state.msg_import = ""

    # -- DASHBOARD / RESUMO --
    if menu == "Resumo":
        def cartao_customizado(icone, titulo, valor):
            st.markdown(f"""
                <div style="background-color: #1e293b; border-radius: 20px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); border-left: 6px solid #6366f1;">
                    <div style="color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; font-size: 0.9rem; margin-bottom: 8px;">
                        <i class="{icone}" style="font-size: 1.2rem; margin-right: 8px; color: #f8fafc;"></i>{titulo}
                    </div>
                    <div style="color: #ffffff; font-weight: 900; font-size: 2rem;">{valor}</div>
                </div>
            """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: cartao_customizado("bi bi-cash-stack", "Saldo Espécie", f"R$ {especie:,.2f}")
        with c2: cartao_customizado("bi bi-phone", "Saldo Pix", f"R$ {pix:,.2f}")
        with c3: cartao_customizado("bi bi-bank", "Saldo Total", f"R$ {especie + pix:,.2f}")
        st.divider()
        st.markdown("<div style='text-align: center; color: #94a3b8; font-style: italic; margin-top: 10px;'><i class='bi bi-info-circle'></i> Use a aba <b>Histórico</b> para filtrar dados e gerar relatórios em PDF.</div>", unsafe_allow_html=True)

    # -- LANÇAMENTOS --
    elif menu == "Lançar":
        st.markdown("<h3><i class='bi bi-pencil-square' style='color: #6366f1; margin-right: 10px;'></i>Novo Lançamento</h3>", unsafe_allow_html=True)
        if st.session_state.msg_sucesso != "":
            st.success(st.session_state.msg_sucesso); st.session_state.msg_sucesso = ""
            
        if st.session_state.confirmar_lancamento:
            dados = st.session_state.dados_temp
            st.warning("⚠️ **Confirme os dados antes de salvar na nuvem.**")
            st.info(f"**Operação:** {dados['Tipo']} | **Valor:** R$ {abs(dados['Valor']):,.2f} | **Local:** {dados['Local']}")
            c1, c2 = st.columns(2)
            if c1.button("✅ Confirmar Lançamento", type="primary"):
                salvar_lancamento(dados)
                st.session_state.confirmar_lancamento = False; st.session_state.dados_temp = {}
                st.session_state.msg_sucesso = "✅ Lançamento registrado com sucesso!"; st.rerun()
            if c2.button("❌ Cancelar Operação", type="secondary"):
                st.session_state.confirmar_lancamento = False; st.rerun()
        else:
            with st.form("form_registro"):
                col_a, col_b = st.columns(2)
                with col_a:
                    tipo = st.radio("Tipo", ["Entrada", "Saída"], horizontal=True)
                    local = st.selectbox("Local", ["Espécie", "Pix"])
                    valor = st.number_input("Valor R$", min_value=0.0, step=1.0, format="%.2f")
                with col_b:
                    desc = st.text_input("Descrição")
                    cat = st.selectbox("Categoria", st.session_state.categorias["entrada"] if tipo == "Entrada" else st.session_state.categorias["saida"])
                    data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
                if st.form_submit_button("AVANÇAR"):
                    if not desc.strip() or valor <= 0: st.warning("⚠️ Preencha todos os campos.")
                    else:
                        st.session_state.dados_temp = {"Data": data.strftime("%d/%m/%Y"), "Descrição": desc.strip(), "Categoria": cat, "Tipo": tipo, "Local": local, "Valor": valor if tipo == "Entrada" else -valor}
                        st.session_state.confirmar_lancamento = True; st.rerun()

    # -- TRANSFERÊNCIAS --
    elif menu == "Transferir":
        st.markdown("<h3><i class='bi bi-arrow-left-right' style='color: #6366f1; margin-right: 10px;'></i>Transferência entre Caixas</h3>", unsafe_allow_html=True)
        if st.session_state.msg_sucesso != "":
            st.success(st.session_state.msg_sucesso); st.session_state.msg_sucesso = ""
        if st.session_state.confirmar_transf:
            dados = st.session_state.dados_transf_temp
            st.warning("⚠️ **Confirme a transferência abaixo.**")
            st.info(f"**De:** {dados['origem']} ➡ **Para:** {dados['destino']} | **Valor:** R$ {dados['valor_tr']:,.2f}")
            c1, c2 = st.columns(2)
            if c1.button("✅ Confirmar Transferência", type="primary"):
                nova_linha = {"Data": dados['hoje'], "Descrição": f"Transferência: {dados['origem']} para {dados['destino']}", "Categoria": "Transferência", "Tipo": "Transferência", "Local": f"{dados['origem']} -> {dados['destino']}", "Valor": dados['valor_tr']}
                salvar_lancamento(nova_linha)
                st.session_state.confirmar_transf = False; st.session_state.msg_sucesso = "✅ Transferência concluída!"; st.rerun()
            if c2.button("❌ Cancelar", type="secondary"): st.session_state.confirmar_transf = False; st.rerun()
        else:
            with st.form("form_transf"):
                origem = st.selectbox("Retirar de:", ["Espécie", "Pix"])
                valor_tr = st.number_input("Valor a Transferir (R$)", min_value=0.0, format="%.2f")
                if st.form_submit_button("AVANÇAR"):
                    saldo_origem = especie if origem == "Espécie" else pix
                    if valor_tr <= 0 or valor_tr > saldo_origem: st.error("❌ Saldo insuficiente ou valor inválido.")
                    else:
                        st.session_state.dados_transf_temp = {"origem": origem, "destino": "Pix" if origem == "Espécie" else "Espécie", "valor_tr": valor_tr, "hoje": datetime.now().strftime("%d/%m/%Y")}
                        st.session_state.confirmar_transf = True; st.rerun()

    # -- HISTÓRICO --
    elif menu == "Histórico":
        st.markdown("<h3><i class='bi bi-file-earmark-bar-graph' style='color: #6366f1; margin-right: 10px;'></i>Histórico Analítico</h3>", unsafe_allow_html=True)
        if st.session_state.msg_sucesso != "":
            st.success(st.session_state.msg_sucesso); st.session_state.msg_sucesso = ""
            
        cf1, cf2, cf3 = st.columns([2, 1.5, 1.5])
        with cf1: datas_sel = st.date_input("Período:", value=[], format="DD/MM/YYYY")
        with cf2: f_tipo = st.selectbox("Tipo:", ["Todos", "Entrada", "Saída", "Transferência"])
        with cf3: f_cat = st.selectbox("Categoria:", ["Todas"] + sorted(df['Categoria'].unique().tolist()) if not df.empty else ["Todas"])
        
        df_f = df.copy()
        if not df_f.empty:
            df_f['Data_dt'] = pd.to_datetime(df_f['Data'], format='%d/%m/%Y', errors='coerce')
            if datas_sel:
                if isinstance(datas_sel, tuple) and len(datas_sel) == 2:
                    df_f = df_f[(df_f['Data_dt'].dt.date >= datas_sel[0]) & (df_f['Data_dt'].dt.date <= datas_sel[1])]
                elif not isinstance(datas_sel, tuple): df_f = df_f[df_f['Data_dt'].dt.date == datas_sel]
            if f_tipo != "Todos": df_f = df_f[df_f['Tipo'] == f_tipo]
            if f_cat != "Todas": df_f = df_f[df_f['Categoria'] == f_cat]
            df_f['orig_idx'] = df_f.index
            df_f = df_f.sort_values(by=['Data_dt', 'id'], ascending=[False, False])

        st.divider()
        col_tit, col_cnt = st.columns([6, 4])
        col_tit.markdown("#### Lançamentos")
        col_cnt.markdown(f"<div style='text-align: right; color: #94a3b8;'>Total: {len(df)} | Mostrando: {len(df_f)}</div>", unsafe_allow_html=True)

        for _, row in df_f.iterrows():
            with st.container():
                c_data, c_info, c_valor, c_del = st.columns([1, 4, 3, 1])
                desc_limpa = str(row['Descrição']).strip().upper()
                dia = row['Data'][:2]
                mes = row['Data'][3:5]
                
                c_data.markdown(f"<b>{dia}</b><br>{mes}", unsafe_allow_html=True)
                c_info.markdown(f"<b>{desc_limpa}</b><br><small>{row['Local']} | {row['Categoria']}</small>", unsafe_allow_html=True)
                
                cor = "#10b981" if row['Tipo'] == 'Entrada' else "#f43f5e" if row['Tipo'] == 'Saída' else "#94a3b8"
                c_valor.markdown(f"<h4 style='text-align: right; color: {cor};'>R$ {abs(row['Valor']):,.2f}</h4>", unsafe_allow_html=True)
                if st.session_state.id_excluir == row['id']:
                    cx1, cx2 = c_del.columns(2)
                    cx1.button("✓", key=f"s_{row['id']}", on_click=confirmar_exclusao, args=(row['id'],), type="primary")
                    cx2.button("✗", key=f"n_{row['id']}", on_click=cancelar_exclusao)
                else: c_del.button("🗑️", key=f"d_{row['id']}", on_click=pedir_exclusao, args=(row['id'],))
            st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)

        # --- FUNÇÃO GERADORA DE PDF (RESTAURO DO PADRÃO PREMIUM) ---
        if not df_f.empty:
            def gerar_relatorio_pdf(df_filtrado, dt_sel):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_margins(15, 15, 15)
                def s_str(text): return str(text).encode('latin-1', 'replace').decode('latin-1')

                # CABEÇALHO
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, s_str("LOUVOR ETERNO"), ln=True, align='C')
                pdf.set_font("Arial", 'B', 11)
                
                periodo = "RELATÓRIO FINANCEIRO GERAL"
                if dt_sel:
                    d_i = dt_sel[0] if isinstance(dt_sel, tuple) else dt_sel
                    d_f = dt_sel[1] if isinstance(dt_sel, tuple) and len(dt_sel)==2 else d_i
                    periodo = f"RELATÓRIO: {d_i.strftime('%d/%m/%Y')} A {d_f.strftime('%d/%m/%Y')}"
                pdf.cell(0, 10, s_str(periodo), ln=True, align='C')
                pdf.ln(8)

                # RESUMO FINANCEIRO
                df_rep = df_filtrado[df_filtrado['Tipo'] != 'Transferência']
                tg = df_rep[df_rep['Tipo'] == 'Entrada']['Valor'].sum()
                ts = abs(df_rep[df_rep['Tipo'] == 'Saída']['Valor'].sum())
                
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(40, 6, "Total de Entradas:", 0, 0); pdf.set_font("Arial", '', 10)
                pdf.cell(0, 6, s_str(f"R$ {tg:,.2f}"), 0, 1)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(40, 6, "Total de Saídas:", 0, 0); pdf.set_font("Arial", '', 10)
                pdf.cell(0, 6, s_str(f"R$ {ts:,.2f}"), 0, 1)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(40, 6, "Saldo Líquido:", 0, 0); pdf.set_font("Arial", '', 10)
                pdf.cell(0, 6, s_str(f"R$ {(tg-ts):,.2f}"), 0, 1)
                pdf.ln(10)

                # TABELA
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 10, s_str("MOVIMENTAÇÕES DETALHADAS"), 0, 1)
                pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 8)
                pdf.cell(22, 8, "DATA", 1, 0, 'C', fill=True); pdf.cell(78, 8, s_str("DESCRIÇÃO"), 1, 0, 'L', fill=True)
                pdf.cell(35, 8, "CATEGORIA", 1, 0, 'C', fill=True); pdf.cell(20, 8, "TIPO", 1, 0, 'C', fill=True); pdf.cell(25, 8, "VALOR (R$)", 1, 1, 'C', fill=True)

                if df_rep.empty:
                    pdf.cell(180, 8, "Nenhum registro de entrada ou saida.", 1, 1, 'C')
                else:
                    df_sort = df_rep.sort_values(by=['Data_dt', 'orig_idx'], ascending=[True, True])
                    m_pt = {1:"JANEIRO",2:"FEVEREIRO",3:"MARÇO",4:"ABRIL",5:"MAIO",6:"JUNHO",7:"JULHO",8:"AGOSTO",9:"SETEMBRO",10:"OUTUBRO",11:"NOVEMBRO",12:"DEZEMBRO"}
                    m_atual = ""
                    for _, r in df_sort.iterrows():
                        g_mes = f"{m_pt.get(r['Data_dt'].month, '')} {r['Data_dt'].year}"
                        if g_mes != m_atual:
                            m_atual = g_mes
                            pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(245, 245, 245)
                            pdf.cell(180, 8, s_str(m_atual), 1, 1, 'L', fill=True)
                        pdf.set_font("Arial", '', 8)
                        pdf.cell(22, 8, s_str(r['Data']), 1, 0, 'C')
                        pdf.cell(78, 8, s_str(str(r['Descrição'])[:45]), 1, 0, 'L')
                        pdf.cell(35, 8, s_str(str(r['Categoria'])[:20]), 1, 0, 'C')
                        pdf.cell(20, 8, s_str(str(r['Tipo']).upper()), 1, 0, 'C')
                        pdf.cell(25, 8, s_str(f"R$ {abs(r['Valor']):,.2f}"), 1, 1, 'R')

                # ASSINATURAS
                if pdf.get_y() > 240: pdf.add_page()
                pdf.ln(30); pdf.set_font("Arial", '', 10)
                pdf.cell(60, 5, "_________________________", 0, 0, 'C'); pdf.cell(60, 5, "_________________________", 0, 0, 'C'); pdf.cell(60, 5, "_________________________", 0, 1, 'C')
                pdf.cell(60, 5, "Pastor", 0, 0, 'C'); pdf.cell(60, 5, s_str("Líder de Jovens"), 0, 0, 'C'); pdf.cell(60, 5, "Tesoureiro", 0, 1, 'C')
                return pdf.output(dest="S").encode('latin-1')
            
            st.download_button("📄 Gerar Relatório em PDF", data=gerar_relatorio_pdf(df_f, datas_sel), file_name=f"Relatorio_{datetime.now().strftime('%d%m%Y')}.pdf", type="primary")

    # -- AJUSTES --
    elif menu == "Ajustes":
        st.markdown("<h3><i class='bi bi-sliders' style='color: #6366f1; margin-right: 10px;'></i>Ajustes</h3>", unsafe_allow_html=True)
        if st.session_state.msg_sucesso != "":
            st.success(st.session_state.msg_sucesso); st.session_state.msg_sucesso = ""

        c_ent, c_sai = st.columns(2)
        with c_ent:
            st.write("**Categorias de Entrada**")
            new_e = st.text_input("Nova Entrada", key="ne")
            if st.button("Adicionar") and new_e.strip():
                st.session_state.categorias["entrada"].append(new_e.strip()); salvar_categorias_db(st.session_state.categorias); st.rerun()
            for c in st.session_state.categorias["entrada"]: st.write(f"• {c}")
        with c_sai:
            st.write("**Categorias de Saída**")
            new_s = st.text_input("Nova Saída", key="ns")
            if st.button("Adicionar", key="be") and new_s.strip():
                st.session_state.categorias["saida"].append(new_s.strip()); salvar_categorias_db(st.session_state.categorias); st.rerun()
            for c in st.session_state.categorias["saida"]: st.write(f"• {c}")

        st.divider()
        st.markdown("#### Backup e Sincronização")
        if st.session_state.msg_import: 
            if "✅" in st.session_state.msg_import: st.success(st.session_state.msg_import)
            else: st.error(st.session_state.msg_import)
            st.session_state.msg_import = ""

        b1, b2 = st.columns(2)
        with b1:
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as wr: df.to_excel(wr, index=False)
            # NOME DO ARQUIVO COM DATA E HORA
            nome_backup = f"backup {datetime.now().strftime('%d%m%Y %Hh%M')}.xlsx"
            st.download_button("📤 EXPORTAR BACKUP", data=out.getvalue(), file_name=nome_backup, type="primary", use_container_width=True)
        with b2:
            up = st.file_uploader("Upload", type=['xlsx', 'csv'], label_visibility="collapsed", key=f"up_{st.session_state.up_key}")
            if up is not None:
                st.warning("⚠️ Mesclar dados na nuvem?")
                if st.button("✅ Confirmar Mesclagem", type="primary", use_container_width=True):
                    try:
                        df_in = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                        df_in = df_in[['Data', 'Descrição', 'Categoria', 'Tipo', 'Local', 'Valor']]
                        df_in['Valor'] = df_in['Valor'].astype(float)
                        novos = salvar_em_lote(df_in, df)
                        st.session_state.msg_import = f"✅ {novos} novos registros salvos na nuvem!"; st.session_state.up_key += 1; st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

    # -- SAIR --
    elif menu == "Sair":
        st.markdown("<h3><i class='bi bi-box-arrow-right' style='color: #f43f5e; margin-right: 10px;'></i>Encerrar Sessão</h3>", unsafe_allow_html=True)
        st.warning("Deseja sair?")
        if st.button("Sim, sair agora", type="primary"): st.session_state.autenticado = False; st.rerun()
        st.button("Cancelar", on_click=cancelar_saida)