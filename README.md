# 💰 Sistema de Caixa - Louvor Eterno

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B.svg)
![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28.svg)

Um sistema web completo e responsivo para a gestão financeira do departamento/grupo **Louvor Eterno**. Desenvolvido para facilitar o controle de fluxo de caixa (entradas, saídas e transferências), gerar relatórios automáticos e manter os dados seguros e sincronizados na nuvem.

---

## ✨ Funcionalidades

* **🔒 Autenticação Segura:** Acesso restrito por senha definida nas variáveis de ambiente (Secrets).
* **📊 Dashboard Intuitivo:** Visualização rápida dos saldos atualizados separados por "Espécie" e "Pix", além do saldo total.
* **💸 Gestão de Lançamentos:** Registro simplificado de ganhos e gastos, com categorização e descrição.
* **🔄 Transferências:** Controle de movimentação de valores entre o caixa físico e a conta digital (Pix).
* **📈 Histórico e Analytics:**
  * Filtros avançados por período, tipo e categoria.
  * Gráficos interativos (tipo Donut) mostrando a origem das entradas e o destino das saídas.
  * Cards premium visuais para cada transação (Verde para entrada, Vermelho para saída).
* **📄 Relatórios Profissionais em PDF:** Geração de relatórios financeiros mensais ou por período formatados com áreas de assinatura (Pastor, Líder, Tesoureiro) prontos para impressão.
* **⚙️ Ajustes Dinâmicos:** Criação e exclusão de categorias de ganhos e gastos diretamente pela interface.
* **☁️ Nuvem e Backup:**
  * Sincronização em tempo real com **Google Firebase (Firestore)**.
  * Exportação de todo o banco de dados para Excel (`.xlsx`) com um clique.
  * Importação de planilhas de backup com **sistema anti-duplicação** inteligente.

---

## 🛠️ Tecnologias Utilizadas

* **[Python](https://www.python.org/):** Linguagem principal.
* **[Streamlit](https://streamlit.io/):** Framework para a construção da interface web interativa.
* **[Firebase Admin SDK](https://firebase.google.com/docs/admin/setup):** Conexão e manipulação do banco de dados NoSQL (Firestore).
* **[Pandas](https://pandas.pydata.org/):** Estruturação, filtragem e manipulação de dados e planilhas Excel.
* **[Plotly](https://plotly.com/python/):** Geração dos gráficos dinâmicos de desempenho financeiro.
* **[FPDF](https://pyfpdf.github.io/fpdf2/):** Construção programática dos relatórios em PDF.

---

## 🚀 Como Executar o Projeto Localmente

### 1. Pré-requisitos
Certifique-se de ter o Python instalado na sua máquina. É recomendável o uso de um ambiente virtual (venv).

### 2. Instalação
Clone o repositório e instale as dependências:

```bash
# Clone o repositório
git clone [https://github.com/seu-usuario/caixa-louvor-eterno.git](https://github.com/seu-usuario/caixa-louvor-eterno.git)

# Entre na pasta do projeto
cd caixa-louvor-eterno

# Instale as bibliotecas necessárias
pip install -r requirements.txt
