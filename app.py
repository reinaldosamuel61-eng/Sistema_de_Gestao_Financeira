import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
from streamlit_option_menu import option_menu

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Caixa Louvor Eterno", page_icon="💰", layout="wide")

# --- 2. ESTILO CSS (Dark Mode Premium & Mobile Friendly) ---
st.markdown("""
    <style>
    @import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css");
    
    /* Fundo da página e textos */
    .stApp, .main { background-color: #0f172a; color: #f8fafc; }
    
    /* Esconder o botão padrão de abrir menu lateral do Streamlit */
    [data-testid="collapsedControl"] { display: none; }
    
    /* Títulos e labels */
    h1, h2, h3, h4, p, span, label { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    
    /* Cards de métricas */
    div[data-testid="stMetric"] {
        background-color: #1e293b !important;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        border-left: 6px solid #6366f1;
    }
    
    /* Valores das métricas */
    [data-testid="stMetricValue"] > div { color: #ffffff !important; font-weight: 900; }
    [data-testid="stMetricLabel"] > div { color: #94a3b8 !important; text-transform: uppercase; letter-spacing: 1px; }

    /* Botões */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        background-color: #6366f1;
        color: white !important;
        font-weight: 800;
        border: none;
        transition: 0.3s;
        text-transform: uppercase;
    }
    .stButton>button:hover { background-color: #4f46e5; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4); }
    
    /* Botões secundários (Cancelar, Lixeira, etc) */
    button[kind="secondary"] {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        color: #f43f5e !important;
    }
    button[kind="secondary"]:hover {
        background-color: #334155 !important;
        border-color: #f43f5e !important;
    }
    
    /* Inputs, Selects e Tabelas */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 10px;
    }
    .stDataFrame { background-color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# Cores para os gráficos
COLORS_ENTRADA = ['#10b981', '#34d399', '#6ee7b7', '#059669']
COLORS_SAIDA = ['#f43f5e', '#fb7185', '#fda4af', '#be123c']

# --- 3. INICIALIZAÇÃO DO BANCO DE DADOS EM MEMÓRIA E ESTADOS DE CONFIRMAÇÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'movimentacoes' not in st.session_state:
    st.session_state.movimentacoes = pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Tipo", "Local", "Valor"])
if 'categorias' not in st.session_state:
    st.session_state.categorias = {
        "entrada": ["Mensalidade", "Oferta", "Doação", "Cantina", "Venda"],
        "saida": ["Lanches", "Materiais", "Retiro", "Som", "Ajuda Social"]
    }

# Variáveis de Estado para Telas de Confirmação
if 'confirmar_lancamento' not in st.session_state:
    st.session_state.confirmar_lancamento = False
if 'dados_temp' not in st.session_state:
    st.session_state.dados_temp = {}
if 'confirmar_transf' not in st.session_state:
    st.session_state.confirmar_transf = False
if 'dados_transf_temp' not in st.session_state:
    st.session_state.dados_transf_temp = {}
if 'idx_excluir' not in st.session_state:
    st.session_state.idx_excluir = None
if 'msg_sucesso' not in st.session_state:
    st.session_state.msg_sucesso = ""
if 'msg_import' not in st.session_state:
    st.session_state.msg_import = ""
if 'confirmar_importacao' not in st.session_state:
    st.session_state.confirmar_importacao = False
if 'confirmar_exportacao' not in st.session_state:
    st.session_state.confirmar_exportacao = False

# Estados para confirmação de categorias
if 'cat_pendente_add' not in st.session_state:
    st.session_state.cat_pendente_add = None
if 'cat_pendente_del' not in st.session_state:
    st.session_state.cat_pendente_del = None

# Funções Callback para os botões do Histórico e Menus
def cancelar_saida():
    st.session_state.menu_principal = "Resumo"

def pedir_exclusao(idx):
    st.session_state.idx_excluir = idx

def cancelar_exclusao():
    st.session_state.idx_excluir = None

def confirmar_exclusao(idx):
    st.session_state.movimentacoes = st.session_state.movimentacoes.drop(idx)
    st.session_state.idx_excluir = None
    st.session_state.msg_sucesso = "🗑️ Lançamento excluído com sucesso!"

def resetar_estado_exportacao():
    st.session_state.confirmar_exportacao = False
    st.session_state.msg_sucesso = "✅ Backup exportado com sucesso!"

# --- 4. SISTEMA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center; margin-top: 50px; font-weight: 900;'>CAIXA LOUVOR ETERNO</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.container(border=True):
            chave = st.text_input("Senha", type="password", placeholder="Digite a senha de acesso...", label_visibility="collapsed")
            if st.button("ACESSAR SISTEMA"):
                
                # Define a senha padrão para testes locais
                senha_esperada = "admin"
                
                # Tenta obter a senha real da nuvem se estiver configurada
                try:
                    senha_esperada = st.secrets["chave_grupo"]
                except:
                    pass # Se falhar ou não achar o arquivo, mantém o 'admin' tranquilamente
                
                # Verifica se o que foi digitado bate com a senha esperada
                if chave == senha_esperada:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Chave incorreta!")
else:
    # --- 5. CABEÇALHO ---
    st.markdown("<h2 style='text-align: center; color: #6366f1; font-weight: 900; margin-top: 0;'>CAIXA LOUVOR ETERNO</h2>", unsafe_allow_html=True)
    
    # --- 6. MENU HORIZONTAL ---
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
            "nav-link": {
                "font-size": "14px", 
                "text-align": "center", 
                "margin": "0px", 
                "color": "#94a3b8", 
                "font-weight": "bold",
            },
            "nav-link-selected": {"background-color": "#6366f1", "color": "#ffffff"},
        }
    )
    
    # Limpa estados de confirmação caso o menu seja trocado
    if 'menu_atual' not in st.session_state:
        st.session_state.menu_atual = menu
    if st.session_state.menu_atual != menu:
        st.session_state.confirmar_importacao = False
        st.session_state.confirmar_exportacao = False
        st.session_state.cat_pendente_add = None
        st.session_state.cat_pendente_del = None
        st.session_state.menu_atual = menu

    df = st.session_state.movimentacoes
    
    # ---- CÁLCULOS GLOBAIS DE SALDO ----
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

    # Limpa mensagens globais ao trocar de tela
    if menu not in ["Lançar", "Transferir", "Histórico", "Ajustes"]:
        st.session_state.msg_sucesso = ""
        st.session_state.msg_import = ""

    # --- 7. PÁGINAS DO SISTEMA ---

    # -- DASHBOARD / RESUMO (Apenas Saldos) --
    if menu == "Resumo":
        def cartao_customizado(icone, titulo, valor):
            st.markdown(f"""
                <div style="background-color: #1e293b; border-radius: 20px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); border-left: 6px solid #6366f1;">
                    <div style="color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; font-size: 0.9rem; margin-bottom: 8px;">
                        <i class="{icone}" style="font-size: 1.2rem; margin-right: 8px; color: #f8fafc;"></i>{titulo}
                    </div>
                    <div style="color: #ffffff; font-weight: 900; font-size: 2rem;">
                        {valor}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            cartao_customizado("bi bi-cash-stack", "Saldo Espécie", f"R$ {especie:,.2f}")
        with c2:
            cartao_customizado("bi bi-phone", "Saldo Pix", f"R$ {pix:,.2f}")
        with c3:
            cartao_customizado("bi bi-bank", "Saldo Total", f"R$ {especie + pix:,.2f}")

        st.divider()
        st.markdown("""
            <div style="text-align: center; color: #94a3b8; font-style: italic; margin-top: 10px;">
                <i class="bi bi-info-circle"></i> Navegue até a aba <b>Histórico</b> para ver os relatórios de desempenho financeiro e filtrar por período.
            </div>
        """, unsafe_allow_html=True)


    # -- LANÇAMENTOS --
    elif menu == "Lançar":
        st.markdown("<h3><i class='bi bi-pencil-square' style='color: #6366f1; margin-right: 10px;'></i>Novo Lançamento</h3>", unsafe_allow_html=True)
        
        if st.session_state.msg_sucesso != "":
            st.success(st.session_state.msg_sucesso)
            st.session_state.msg_sucesso = ""
            
        if st.session_state.confirmar_lancamento:
            dados = st.session_state.dados_temp
            st.warning("⚠️ **ATENÇÃO: Confirme os dados da operação abaixo antes de salvar.**")
            
            st.info(f"""
            **Operação:** {dados['Tipo']}  
            **Valor:** R$ {abs(dados['Valor']):,.2f}  
            **Local:** {dados['Local']}  
            **Descrição:** {dados['Descrição']}  
            **Categoria:** {dados['Categoria']}  
            **Data:** {dados['Data']}
            """)
            
            c1, c2 = st.columns(2)
            if c1.button("✅ Confirmar Lançamento", type="primary"):
                st.session_state.movimentacoes = pd.concat([st.session_state.movimentacoes, pd.DataFrame([dados])], ignore_index=True)
                st.session_state.confirmar_lancamento = False
                st.session_state.dados_temp = {}
                st.session_state.msg_sucesso = f"✅ Lançamento de R$ {abs(dados['Valor']):,.2f} registrado com sucesso!"
                st.rerun()
                
            if c2.button("❌ Cancelar Operação", type="secondary"):
                st.session_state.confirmar_lancamento = False
                st.session_state.dados_temp = {}
                st.rerun()
                
        else:
            with st.form("form_registro", clear_on_submit=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    tipo = st.radio("Tipo", ["Entrada", "Saída"], horizontal=True)
                    local = st.selectbox("Local", ["Espécie", "Pix"])
                    valor = st.number_input("Valor R$", min_value=0.0, step=1.0, format="%.2f")
                with col_b:
                    desc = st.text_input("Descrição (Ex: Oferta Culto)")
                    lista_cats = st.session_state.categorias["entrada"] if tipo == "Entrada" else st.session_state.categorias["saida"]
                    cat = st.selectbox("Categoria", lista_cats)
                    data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
                
                if st.form_submit_button("AVANÇAR"):
                    saldo_atual_local = especie if local in ["Espécie", "Dinheiro"] else pix
                    if not desc.strip() or valor <= 0:
                        st.warning("⚠️ Atenção: Preencha a descrição e insira um valor maior que R$ 0,00.")
                    elif tipo == "Saída" and valor > saldo_atual_local:
                        st.error(f"❌ Operação Negada: O saldo em {local} (R$ {saldo_atual_local:,.2f}) é insuficiente para esta saída!")
                    else:
                        st.session_state.dados_temp = {
                            "Data": data.strftime("%d/%m/%Y"), 
                            "Descrição": desc.strip(), 
                            "Categoria": cat, 
                            "Tipo": tipo, 
                            "Local": local, 
                            "Valor": valor if tipo == "Entrada" else -valor
                        }
                        st.session_state.confirmar_lancamento = True
                        st.rerun()

    # -- TRANSFERÊNCIAS --
    elif menu == "Transferir":
        st.markdown("<h3><i class='bi bi-arrow-left-right' style='color: #6366f1; margin-right: 10px;'></i>Transferência entre Caixas</h3>", unsafe_allow_html=True)
        
        if st.session_state.msg_sucesso != "":
            st.success(st.session_state.msg_sucesso)
            st.session_state.msg_sucesso = ""

        if st.session_state.confirmar_transf:
            dados = st.session_state.dados_transf_temp
            st.warning("⚠️ **ATENÇÃO: Confirme a transferência abaixo.**")
            st.info(f"**De:** {dados['origem']} ➡ **Para:** {dados['destino']} | **Valor:** R$ {dados['valor_tr']:,.2f}")
            
            c1, c2 = st.columns(2)
            if c1.button("✅ Confirmar Transferência", type="primary"):
                nova_linha = pd.DataFrame([{
                    "Data": dados['hoje'], 
                    "Descrição": f"Transferência: {dados['origem']} para {dados['destino']}", 
                    "Categoria": "Transferência", "Tipo": "Transferência", 
                    "Local": f"{dados['origem']} -> {dados['destino']}", "Valor": dados['valor_tr']
                }])
                st.session_state.movimentacoes = pd.concat([st.session_state.movimentacoes, nova_linha], ignore_index=True)
                st.session_state.confirmar_transf = False
                st.session_state.msg_sucesso = f"✅ Transferência concluída!"
                st.rerun()
            if c2.button("❌ Cancelar", type="secondary"):
                st.session_state.confirmar_transf = False
                st.rerun()
        else:
            with st.form("form_transf", clear_on_submit=False):
                origem = st.selectbox("Retirar de:", ["Espécie", "Pix"])
                destino = "Pix" if origem == "Espécie" else "Espécie"
                valor_tr = st.number_input("Valor a Transferir (R$)", min_value=0.0, step=1.0, format="%.2f")
                if st.form_submit_button("AVANÇAR"):
                    saldo_atual_origem = especie if origem in ["Espécie", "Dinheiro"] else pix
                    if valor_tr <= 0:
                        st.warning("⚠️ Insira um valor válido.")
                    elif valor_tr > saldo_atual_origem:
                        st.error(f"❌ Saldo insuficiente em {origem}.")
                    else:
                        st.session_state.dados_transf_temp = {"origem": origem, "destino": destino, "valor_tr": valor_tr, "hoje": datetime.now().strftime("%d/%m/%Y")}
                        st.session_state.confirmar_transf = True
                        st.rerun()

    # -- HISTÓRICO E DESEMPENHO --
    elif menu == "Histórico":
        st.markdown("<h3><i class='bi bi-file-earmark-bar-graph' style='color: #6366f1; margin-right: 10px;'></i>Relatórios Analíticos e Histórico</h3>", unsafe_allow_html=True)
        if st.session_state.msg_sucesso != "":
            st.success(st.session_state.msg_sucesso)
            st.session_state.msg_sucesso = ""
            
        c_filt1, c_filt2 = st.columns(2)
        with c_filt1:
            datas_selecionadas = st.date_input("🗓️ Definir Período (Vazio = Mostrar Tudo):", value=[], format="DD/MM/YYYY")
        with c_filt2:
            f_tipo = st.selectbox("🏷️ Filtrar por Tipo:", ["Todos", "Entrada", "Saída", "Transferência"])
        
        df_f = df.copy()
        if not df_f.empty:
            df_f['Data_dt'] = pd.to_datetime(df_f['Data'], format='%d/%m/%Y', errors='coerce')
            if datas_selecionadas:
                if isinstance(datas_selecionadas, tuple) and len(datas_selecionadas) == 2:
                    df_f = df_f[(df_f['Data_dt'].dt.date >= datas_selecionadas[0]) & (df_f['Data_dt'].dt.date <= datas_selecionadas[1])]
                elif not isinstance(datas_selecionadas, tuple):
                    df_f = df_f[df_f['Data_dt'].dt.date == datas_selecionadas]
            if f_tipo != "Todos":
                df_f = df_f[df_f['Tipo'] == f_tipo]
            df_f['orig_idx'] = df_f.index
            df_f = df_f.sort_values(by=['Data_dt', 'orig_idx'], ascending=[False, False])

        st.divider()
        st.markdown("<h4 style='color: #f8fafc; margin-bottom: 20px;'><i class='bi bi-list-ul' style='margin-right: 8px;'></i> Lançamentos do Período</h4>", unsafe_allow_html=True)

        if not df_f.empty:
            meses_pt = {"01": "JAN", "02": "FEV", "03": "MAR", "04": "ABR", "05": "MAI", "06": "JUN", "07": "JUL", "08": "AGO", "09": "SET", "10": "OUT", "11": "NOV", "12": "DEZ"}
            for idx, row in df_f.iterrows():
                try:
                    dia, mes, _ = row['Data'].split('/')
                    mes_texto = meses_pt.get(mes, mes)
                except: dia, mes_texto = "00", "---"

                cor_valor = "#10b981" if row['Tipo'] == 'Entrada' else "#f43f5e" if row['Tipo'] == 'Saída' else "#94a3b8"
                valor_str = f"R$ {abs(row['Valor']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                with st.container():
                    c_data, c_info, c_valor, c_del = st.columns([1.5, 3.5, 3, 2])
                    with c_data:
                        st.markdown(f"<div style='text-align: center; color: #94a3b8; font-weight: 900; padding-top: 15px;'><span style='font-size: 1.4rem; color: #cbd5e1;'>{dia}</span><br><span style='font-size: 0.75rem;'>DE {mes_texto}</span></div>", unsafe_allow_html=True)
                    with c_info:
                        st.markdown(f"<div style='padding-top: 10px;'><div style='color: #f8fafc; font-weight: 900; font-size: 1.1rem; text-transform: uppercase;'>{row['Descrição']}</div><span style='border: 1px solid #3b82f6; color: #60a5fa; border-radius: 12px; padding: 2px 8px; font-size: 0.6rem;'>{row['Local']}</span> <span style='border: 1px solid #475569; color: #cbd5e1; border-radius: 12px; padding: 2px 8px; font-size: 0.6rem;'>{row['Categoria']}</span></div>", unsafe_allow_html=True)
                    with c_valor:
                        st.markdown(f"<div style='text-align: right; color: {cor_valor}; font-weight: 900; font-size: 1.5rem; padding-top: 15px;'>{valor_str}</div>", unsafe_allow_html=True)
                    with c_del:
                        if st.session_state.idx_excluir == idx:
                            st.markdown("<div style='padding-top: 5px; text-align: center; color: #f43f5e; font-size: 0.7rem;'>Confirmar?</div>", unsafe_allow_html=True)
                            cx1, cx2 = st.columns(2)
                            cx1.button("✓", key=f"s_{idx}", on_click=confirmar_exclusao, args=(idx,), type="primary")
                            cx2.button("✗", key=f"n_{idx}", on_click=cancelar_exclusao, type="secondary")
                        else:
                            st.markdown("<div style='padding-top: 12px; text-align: center;'>", unsafe_allow_html=True)
                            st.button("🗑️", key=f"d_{idx}", on_click=pedir_exclusao, args=(idx,), type="secondary")
                            st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #334155;'>", unsafe_allow_html=True)
            
            nome_arq = f"backup {datetime.now().strftime('%d%m%Y %Hh%M')}.xlsx"
            if not st.session_state.confirmar_exportacao:
                if st.button("📤 Exportar Dados (Excel)", type="primary"):
                    st.session_state.confirmar_exportacao = True
                    st.rerun()
            else:
                st.warning("⚠️ Gerar arquivo Excel?")
                cex1, cex2 = st.columns([3, 7])
                with cex1:
                    out = io.BytesIO()
                    with pd.ExcelWriter(out, engine='openpyxl') as wr:
                        df_f.drop(columns=['Data_dt', 'orig_idx'], errors='ignore').to_excel(wr, index=False)
                    st.download_button("✅ Baixar", data=out.getvalue(), file_name=nome_arq, on_click=resetar_estado_exportacao)
                with cex2:
                    if st.button("❌ Cancelar"): st.session_state.confirmar_exportacao = False; st.rerun()
        else:
            st.info("Sem lançamentos no período.")

        # --- ÁREA DE DESEMPENHO (GRÁFICOS) ---
        st.divider()
        st.markdown("<div style='text-align: center;'><i class='bi bi-bar-chart-fill' style='font-size: 2rem; color: #10b981;'></i><h2 style='font-weight: 900;'>Desempenho Financeiro</h2></div>", unsafe_allow_html=True)
        df_ent_f = df_f[df_f['Tipo'] == 'Entrada']; df_sai_f = df_f[df_f['Tipo'] == 'Saída']
        tg = df_ent_f['Valor'].sum(); ts = abs(df_sai_f['Valor'].sum())
        
        cda1, cda2, cda3 = st.columns(3)
        def card_d(t, v, c): st.markdown(f"<div style='background-color: rgba({c}, 0.05); border: 1px solid rgba({c}, 0.3); border-radius: 20px; padding: 20px; text-align: center;'><div style='color: rgb({c}); font-size: 0.8rem; font-weight: 800;'>{t}</div><div style='color: rgb({c}); font-size: 1.8rem; font-weight: 900;'>R$ {v:,.2f}</div></div>", unsafe_allow_html=True)
        with cda1: card_d("GANHOS (+)", tg, "16, 185, 129")
        with cda2: card_d("GASTOS (-)", ts, "244, 63, 94")
        with cda3: card_d("SALDO PERÍODO", tg-ts, "99, 102, 241")

        st.markdown("<div style='margin-top: 35px;'></div>", unsafe_allow_html=True)

        if not df_ent_f.empty or not df_sai_f.empty:
            cg1, cg2 = st.columns(2)
            with cg1:
                if not df_ent_f.empty:
                    st.markdown("<h5 style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>ORIGEM DAS ENTRADAS</h5>", unsafe_allow_html=True)
                    dg = df_ent_f.groupby('Categoria')['Valor'].sum().reset_index()
                    fig = go.Figure(data=[go.Pie(labels=dg['Categoria'], values=dg['Valor'], hole=.65, marker_colors=COLORS_ENTRADA, textinfo='none')])
                    fig.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), height=250, legend=dict(font=dict(color="#f8fafc")))
                    st.plotly_chart(fig, use_container_width=True)
            with cg2:
                if not df_sai_f.empty:
                    st.markdown("<h5 style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>DESTINO DOS GASTOS</h5>", unsafe_allow_html=True)
                    dg = df_sai_f.groupby('Categoria')['Valor'].sum().reset_index()
                    fig = go.Figure(data=[go.Pie(labels=dg['Categoria'], values=abs(dg['Valor']), hole=.65, marker_colors=COLORS_SAIDA, textinfo='none')])
                    fig.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), height=250, legend=dict(font=dict(color="#f8fafc")))
                    st.plotly_chart(fig, use_container_width=True)

    # -- AJUSTES --
    elif menu == "Ajustes":
        st.markdown("<h3><i class='bi bi-sliders' style='color: #6366f1; margin-right: 10px;'></i>Ajustes do Sistema</h3>", unsafe_allow_html=True)
        
        # --- GESTÃO DE CATEGORIAS ---
        st.write("Personalize as categorias de lançamentos:")
        col_c_ent, col_c_sai = st.columns(2)
        
        # Coluna Entradas
        with col_c_ent:
            st.markdown("<h4 style='color: #10b981;'><i class='bi bi-arrow-down-short'></i> Entradas</h4>", unsafe_allow_html=True)
            new_ent = st.text_input("Nova Categoria de Ganho", key="n_ent")
            if st.button("Adicionar Ganho"):
                if new_ent.strip(): st.session_state.cat_pendente_add = {"nome": new_ent.strip(), "tipo": "entrada"}
            
            if st.session_state.cat_pendente_add and st.session_state.cat_pendente_add['tipo'] == "entrada":
                st.warning(f"Adicionar '{st.session_state.cat_pendente_add['nome']}'?")
                ca1, ca2 = st.columns(2)
                if ca1.button("Sim", key="ya_ent"):
                    if st.session_state.cat_pendente_add['nome'] not in st.session_state.categorias["entrada"]:
                        st.session_state.categorias["entrada"].append(st.session_state.cat_pendente_add['nome'])
                    st.session_state.cat_pendente_add = None; st.rerun()
                if ca2.button("Não", key="na_ent"): st.session_state.cat_pendente_add = None; st.rerun()

            for cat in st.session_state.categorias["entrada"]:
                cc1, cc2 = st.columns([8, 2])
                cc1.markdown(f"• {cat}")
                if cc2.button("🗑️", key=f"dc_e_{cat}"): st.session_state.cat_pendente_del = {"nome": cat, "tipo": "entrada"}
            
        # Coluna Saídas
        with col_c_sai:
            st.markdown("<h4 style='color: #f43f5e;'><i class='bi bi-arrow-up-short'></i> Saídas</h4>", unsafe_allow_html=True)
            new_sai = st.text_input("Nova Categoria de Gasto", key="n_sai")
            if st.button("Adicionar Gasto"):
                if new_sai.strip(): st.session_state.cat_pendente_add = {"nome": new_sai.strip(), "tipo": "saida"}
            
            if st.session_state.cat_pendente_add and st.session_state.cat_pendente_add['tipo'] == "saida":
                st.warning(f"Adicionar '{st.session_state.cat_pendente_add['nome']}'?")
                ca1, ca2 = st.columns(2)
                if ca1.button("Sim", key="ya_sai"):
                    if st.session_state.cat_pendente_add['nome'] not in st.session_state.categorias["saida"]:
                        st.session_state.categorias["saida"].append(st.session_state.cat_pendente_add['nome'])
                    st.session_state.cat_pendente_add = None; st.rerun()
                if ca2.button("Não", key="na_sai"): st.session_state.cat_pendente_add = None; st.rerun()

            for cat in st.session_state.categorias["saida"]:
                cc1, cc2 = st.columns([8, 2])
                cc1.markdown(f"• {cat}")
                if cc2.button("🗑️", key=f"dc_s_{cat}"): st.session_state.cat_pendente_del = {"nome": cat, "tipo": "saida"}

        # Confirmação de Exclusão de Categoria (Centralizado)
        if st.session_state.cat_pendente_del:
            st.error(f"⚠️ Excluir categoria '{st.session_state.cat_pendente_del['nome']}'?")
            cx1, cx2 = st.columns(2)
            if cx1.button("Confirmar Exclusão", key="cd_y"):
                st.session_state.categorias[st.session_state.cat_pendente_del['tipo']].remove(st.session_state.cat_pendente_del['nome'])
                st.session_state.cat_pendente_del = None; st.rerun()
            if cx2.button("Cancelar", key="cd_n"): st.session_state.cat_pendente_del = None; st.rerun()

        st.divider()

        # --- IMPORTAÇÃO DE DADOS ---
        st.markdown("<h4 style='color: #f8fafc;'><i class='bi bi-cloud-upload'></i> Importar Dados (Excel/CSV)</h4>", unsafe_allow_html=True)
        st.info("💡 Faça o upload da planilha (Excel ou CSV) no modelo gerado pelo histórico.")
        
        uploaded_file = st.file_uploader("Selecione o arquivo", type=['xlsx', 'csv'], label_visibility="collapsed")
        
        # Feedback da importação posicionado logo abaixo do uploader
        if st.session_state.msg_import != "":
            if "✅" in st.session_state.msg_import: st.success(st.session_state.msg_import)
            else: st.error(st.session_state.msg_import)
            # Limpa a mensagem após exibir
            st.session_state.msg_import = ""

        if uploaded_file is not None:
            if not st.session_state.confirmar_importacao:
                if st.button("PROCESSAR IMPORTAÇÃO", type="primary"):
                    st.session_state.confirmar_importacao = True; st.rerun()
            else:
                st.warning("⚠️ Mesclar dados ao sistema?")
                ci1, ci2 = st.columns(2)
                if ci1.button("✅ Confirmar"):
                    try:
                        df_in = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                        df_in.columns = df_in.columns.str.strip()
                        if 'Valor (R$)' not in df_in.columns:
                            st.session_state.msg_import = "❌ Coluna 'Valor (R$)' não encontrada."
                        else:
                            rev_tipo = {'entrada': 'Entrada', 'saida': 'Saída', 'transferencia': 'Transferência'}
                            df_in['Tipo'] = df_in['Tipo'].astype(str).str.lower().map(rev_tipo).fillna(df_in['Tipo'])
                            rev_loc = {'fisico': 'Espécie', 'dinheiro': 'Espécie', 'pix': 'Pix', 'fisico > pix': 'Espécie -> Pix', 'pix > fisico': 'Pix -> Espécie'}
                            df_in['Local'] = df_in['Local'].astype(str).str.lower().map(rev_loc).fillna(df_in['Local'])
                            
                            if df_in['Valor (R$)'].dtype == 'O': 
                                df_in['Valor (R$)'] = df_in['Valor (R$)'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                            df_in['Valor'] = df_in['Valor (R$)'].astype(float)
                            df_in.loc[df_in['Tipo'] == 'Saída', 'Valor'] = -df_in['Valor'].abs()
                            
                            df_in['Data'] = pd.to_datetime(df_in['Data'], dayfirst=True, errors='coerce').dt.strftime("%d/%m/%Y").fillna(datetime.now().strftime("%d/%m/%Y"))
                            
                            # Adiciona categorias novas
                            for _, r in df_in.iterrows():
                                c = str(r['Categoria']).strip()
                                if r['Tipo'] == 'Entrada' and c not in st.session_state.categorias['entrada']: st.session_state.categorias['entrada'].append(c)
                                elif r['Tipo'] == 'Saída' and c not in st.session_state.categorias['saida']: st.session_state.categorias['saida'].append(c)

                            st.session_state.movimentacoes = pd.concat([st.session_state.movimentacoes, df_in[['Data', 'Descrição', 'Categoria', 'Tipo', 'Local', 'Valor']]], ignore_index=True)
                            st.session_state.msg_import = f"✅ {len(df_in)} registros importados!"
                        st.session_state.confirmar_importacao = False; st.rerun()
                    except Exception as e:
                        st.session_state.msg_import = f"❌ Erro: {e}"; st.session_state.confirmar_importacao = False; st.rerun()
                if ci2.button("❌ Cancelar"): st.session_state.confirmar_importacao = False; st.rerun()

    # -- SAIR --
    elif menu == "Sair":
        st.markdown("<h3 style='color: #f43f5e;'><i class='bi bi-box-arrow-right'></i> Encerrar Sessão</h3>", unsafe_allow_html=True)
        st.warning("Encerrar sessão?")
        cs1, cs2 = st.columns(2)
        if cs1.button("Sim, sair agora", type="primary"): st.session_state.autenticado = False; st.rerun()
        if cs2.button("Cancelar", type="secondary", on_click=cancelar_saida): pass