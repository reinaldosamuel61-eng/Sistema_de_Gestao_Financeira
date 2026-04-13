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
    .historico-card { background-color: #1e293b; border-radius: 15px; padding: 18px; margin-bottom: 12px; border-left: 6px solid transparent; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); }
    .card-entrada { border-left-color: #10b981; }
    .card-saida { border-left-color: #f43f5e; }
    .card-transferencia { border-left-color: #facc15; }
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
    /* Estilo customizado para o popover de notas no histórico */
    div[data-testid="stPopover"] > button { background-color: transparent !important; border: 1px solid #475569 !important; color: #94a3b8 !important; padding: 0px 10px !important; height: 2.2em !important; }
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
    if db is None: 
        return {"entrada": ["Oferta"], "saida": ["Lanches"]}
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
if 'msg_import' not in st.session_state: st.session_state.msg_import = ""
if 'confirmar_importacao' not in st.session_state: st.session_state.confirmar_importacao = False
if 'up_key' not in st.session_state: st.session_state.up_key = 0

if 'categorias' not in st.session_state and db is not None:
    st.session_state.categorias = carregar_categorias()

def confirmar_exclusao(doc_id):
    excluir_lancamento_db(doc_id)
    st.session_state.id_excluir = None
    st.session_state.msg_sucesso = "🗑️ Lançamento excluído com sucesso!"

def cancelar_exclusao(): st.session_state.id_excluir = None

# Função callback para voltar ao Resumo sem dar erro no Menu
def cancelar_saida():
    st.session_state.menu_principal = "Resumo"

# --- 5. SISTEMA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        .main .block-container { display: flex; flex-direction: column; justify-content: center; min-height: 85vh; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1e293b !important; border-radius: 15px !important; padding: 25px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important; border: none !important; border-left: 6px solid #6366f1 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: center; font-weight: 900; margin-bottom: 40px; color: #f8fafc; letter-spacing: 1px;'>SISTEMA DE GESTÃO FINANCEIRA</h2>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #f8fafc; margin-bottom: 25px;'><i class='bi bi-lock-fill' style='color: #6366f1; margin-right: 10px;'></i>Acesso Restrito</h4>", unsafe_allow_html=True)
            chave = st.text_input("Senha", type="password", placeholder="Digite a senha de acesso...", label_visibility="collapsed", autocomplete="new-password")
            if st.button("ACESSAR SISTEMA"):
                senha_esperada = st.secrets.get("chave_grupo", "admin")
                if chave == senha_esperada:
                    st.session_state.autenticado = True; st.rerun()
                else: st.error("❌ Chave incorreta!")
else:
    if db is None: st.error("🔥 Erro de conexão."); st.stop()

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

    elif menu == "Lançar":
        st.markdown("<h3><i class='bi bi-pencil-square' style='color: #6366f1;'></i> Novo Lançamento</h3>", unsafe_allow_html=True)
        if st.session_state.msg_sucesso: st.success(st.session_state.msg_sucesso); st.session_state.msg_sucesso = ""
        
        if st.session_state.confirmar_lancamento:
            d = st.session_state.dados_temp
            st.warning("⚠️ Confirme os dados abaixo:")
            st.info(f"**{d['Tipo']}** | **Valor:** R$ {abs(d['Valor']):,.2f} | **Local:** {d['Local']}")
            if d.get('Nota'): st.info(f"**Nota:** {d['Nota']}")
            c1, c2 = st.columns(2)
            if c1.button("✅ Confirmar"):
                salvar_lancamento(d); st.session_state.confirmar_lancamento = False; st.session_state.msg_sucesso = "✅ Sucesso!"; st.rerun()
            if c2.button("❌ Cancelar"): st.session_state.confirmar_lancamento = False; st.rerun()
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
        with st.form("f_trans"):
            orig = st.selectbox("De:", ["Espécie", "Pix"])
            val = st.number_input("Valor R$", min_value=0.0, format="%.2f")
            nota_t = st.text_input("Nota / Observação (Opcional)")
            if st.form_submit_button("EXECUTAR"):
                dest = "Pix" if orig == "Espécie" else "Espécie"
                salvar_lancamento({"Data": datetime.now().strftime("%d/%m/%Y"), "Descrição": f"TRANSFERÊNCIA: {orig.upper()} > {dest.upper()}", "Categoria": "Transferência", "Tipo": "Transferência", "Local": f"{orig} -> {dest}", "Valor": val, "Nota": nota_t.strip()})
                st.success("✅ Transferência concluída!"); st.rerun()

    elif menu == "Histórico":
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

        st.divider()
        col_tit, col_cnt = st.columns([6, 4])
        col_tit.markdown("#### Lançamentos")
        col_cnt.markdown(f"<div style='text-align: right; color: #94a3b8;'>Total: {len(df)} | Mostrando: {len(df_f)}</div>", unsafe_allow_html=True)

        for _, row in df_f.iterrows():
            if row['Tipo'] == 'Entrada': cl, cor, pre = "card-entrada", "#10b981", "+"
            elif row['Tipo'] == 'Saída': cl, cor, pre = "card-saida", "#f43f5e", "-"
            else: cl, cor, pre = "card-transferencia", "#facc15", ""
            
            meses_map = {"01": "Jan", "02": "Fev", "03": "Mar", "04": "Abril", "05": "Maio", "06": "Jun", "07": "Jul", "08": "Ago", "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"}
            mes_nome = meses_map.get(row['Data'][3:5], row['Data'][3:5])

            with st.container():
                st.markdown(f"""<div class="historico-card {cl}">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <div style="text-align: center; min-width: 50px; border-right: 1px solid rgba(255,255,255,0.1); padding-right: 10px;">
                            <b style="font-size: 1.2rem; display: block;">{row['Data'][:2]}</b>
                            <small style="color: #94a3b8; text-transform: uppercase;">{mes_nome}</small>
                        </div>
                        <div>
                            <b style="font-size: 1.05rem; text-transform: uppercase;">{str(row['Descrição']).strip()}</b><br>
                            <small style="color: #94a3b8;">{row['Categoria']} | {row['Local']}</small>
                        </div>
                    </div>
                    <div style="text-align: right;"><b style="color: {cor}; font-size: 1.3rem;">{pre} R$ {abs(row['Valor']):,.2f}</b></div>
                </div>""", unsafe_allow_html=True)
                
                # Coluna de ferramentas (Nota e Lixeira)
                c_tools = st.columns([10, 1.2, 1.2])
                with c_tools[1]:
                    nota_val = row.get('Nota')
                    if pd.notna(nota_val) and str(nota_val).strip() != "":
                        with st.popover("💬", use_container_width=True):
                            st.info(f"**Observação:**\n\n{nota_val}")
                
                with c_tools[2]:
                    if st.session_state.id_excluir == row['id']:
                        cx1, cx2 = st.columns(2)
                        cx1.button("✓", key=f"s_{row['id']}", on_click=confirmar_exclusao, args=(row['id'],), type="primary")
                        cx2.button("✗", key=f"n_{row['id']}", on_click=cancelar_exclusao)
                    else:
                        st.button("🗑️", key=f"d_{row['id']}", on_click=lambda id=row['id']: st.session_state.update({"id_excluir": id}))

    elif menu == "Ajustes":
        st.markdown("<h3><i class='bi bi-sliders'></i> Ajustes</h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Ganhos**")
            new_e = st.text_input("Nova Entrada")
            if st.button("Adicionar", key="add_e") and new_e:
                st.session_state.categorias["entrada"].append(new_e.strip()); salvar_categorias_db(st.session_state.categorias); st.rerun()
            for c in st.session_state.categorias["entrada"]:
                col_a, col_b = st.columns([8, 2])
                col_a.write(f"• {c}")
                if col_b.button("🗑️", key=f"de_{c}"):
                    st.session_state.categorias["entrada"].remove(c); salvar_categorias_db(st.session_state.categorias); st.rerun()
        with c2:
            st.write("**Gastos**")
            new_s = st.text_input("Nova Saída")
            if st.button("Adicionar", key="add_s") and new_s:
                st.session_state.categorias["saida"].append(new_s.strip()); salvar_categorias_db(st.session_state.categorias); st.rerun()
            for c in st.session_state.categorias["saida"]:
                col_a, col_b = st.columns([8, 2])
                col_a.write(f"• {c}")
                if col_b.button("🗑️", key=f"ds_{c}"):
                    st.session_state.categorias["saida"].remove(c); salvar_categorias_db(st.session_state.categorias); st.rerun()

    elif menu == "Sair":
        st.warning("Deseja sair?")
        if st.button("Sim, sair agora", type="primary"): st.session_state.autenticado = False; st.rerun()
        # Uso do callback para evitar o erro do widget
        st.button("Cancelar", on_click=cancelar_saida)
