import streamlit as st
import pandas as pd
import pdfplumber
import trimesh
import plotly.graph_objects as go
import numpy as np
import os

# --- CONFIGURAÇÃO VISUAL (Anti-Gravity) ---
st.set_page_config(layout="wide", page_title="IndustriAI Pro | RCC", page_icon="⚙️")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    div[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    h1, h2, h3 { color: #e6edf3; }
    div.stButton > button { background-color: #00FFFF; color: black; border: none; font-weight: bold; }
    div.stButton > button:hover { background-color: #00cccc; color: white; }
    .success-box { padding: 1rem; background-color: #1f2937; border: 1px solid #22c55e; border-radius: 8px; margin-bottom: 1rem; }
    .info-box { padding: 1rem; background-color: #1f2937; border: 1px solid #3b82f6; border-radius: 8px; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DADOS (Ground Truth RCC Lâminas) ---
DB_HISTORICO = {
    "Calcador Temperado Interior": {
        "material": "Aço 1.2379 (D2)", "peso": 1.642, "preco": 309.52, "dims": "100x70x34 mm"
    },
    "Estrutura para embutir calcador interior": {
        "material": "Aço 1.1730 (C45)", "peso": 3.796, "preco": 308.88, "dims": "140x128x59 mm"
    },
    "Estrutura para embutir calcador exterior": {
        "material": "Aço 1.1730 (C45)", "peso": 7.782, "preco": 361.92, "dims": "190x115x82.5 mm"
    }
}

# --- FUNÇÕES ---
def ler_pdf_rcc(file):
    """Lê PDF e procura correspondência exata no histórico"""
    try:
        with pdfplumber.open(file) as pdf:
            if not pdf.pages: return False, None, None
            text = pdf.pages[0].extract_text() or ""
            
            for key, data in DB_HISTORICO.items():
                if key.lower() in text.lower():
                    return True, key, data
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
    return False, None, None

def carregar_3d(uploaded_file, file_ext):
    """Carrega STL usando Trimesh (Mais leve que CadQuery)"""
    temp_filename = f"temp_mesh{file_ext}"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    try:
        mesh = trimesh.load(temp_filename)
        return mesh
    except Exception as e:
        return None

# --- UI SIDEBAR ---
with st.sidebar:
    st.title("IndustriAI Pro")
    st.caption("RCC Lâminas Edition v2.0")
    menu = st.radio("Navegação", ["Orçamentação Inteligente", "Engenharia & Design", "Base de Moldes", "Produção"])
    st.divider()
    st.markdown("### Estado do Sistema")
    st.code("Cloud Server: ONLINE\nEngine: Trimesh\nGPU: Virtualized", language="yaml")

# --- VISTA 1: ORÇAMENTAÇÃO ---
if menu == "Orçamentação Inteligente":
    st.title("⚡ Orçamentação Automática")
    
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.markdown("### 1. Upload de Ficheiro")
        uploaded_file = st.file_uploader("Arraste Desenho Técnico (PDF) ou 3D (STL)", type=["pdf", "stl", "step"])
        
        # Área de Preview 3D
        chart_container = st.container()

    with col_right:
        st.markdown("### 2. Análise e Custos")
        
        if uploaded_file:
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            # --- CENÁRIO A: FICHEIRO PDF (Histórico) ---
            if file_ext == ".pdf":
                found, name, data = ler_pdf_rcc(uploaded_file)
                
                if found:
                    st.markdown(f"""
                    <div class="success-box">
                        <h3 style="margin:0; color:#22c55e">✅ Projeto Histórico Reconhecido</h3>
                        <p style="margin:0;">Ficheiro: {name}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns(2)
                    c1.metric("Material Detetado", data['material'])
                    c1.metric("Dimensões", data['dims'])
                    c2.metric("Peso Real", f"{data['peso']} kg")
                    c2.metric("Orçamento Histórico", f"€ {data['preco']:.2f}", delta="Validado")
                    
                    st.info("ℹ️ Visualização 3D indisponível para PDF 2D. A usar metadados do histórico.")
                    
                else:
                    st.warning("⚠️ Ficheiro PDF não reconhecido na base de dados histórica.")

            # --- CENÁRIO B: FICHEIRO 3D (STL) ---
            elif file_ext in [".stl", ".step"]:
                # Se for STEP, avisar, mas tentar carregar se o trimesh conseguir (ou avisar para converter)
                if file_ext == ".step":
                     st.warning("⚠️ Nota: Para visualização web rápida, converta STEP para STL. A tentar processar...")
                
                mesh = carregar_3d(uploaded_file, file_ext)
                
                if mesh and hasattr(mesh, 'volume'):
                    st.markdown("""
                    <div class="info-box">
                        <h3 style="margin:0; color:#3b82f6">⚡ Geometria Processada</h3>
                        <p style="margin:0;">Cálculo em tempo real baseado na física.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Cálculos Físicos
                    vol_cm3 = mesh.volume / 1000
                    if vol_cm3 < 0: vol_cm3 *= -1
                    peso = (vol_cm3 * 7.85) / 1000 # Aço
                    preco = (peso * 18.5) + 120    # Lógica de preço simulada
                    
                    c1, c2 = st.columns(2)
                    c1.metric("Volume Real", f"{vol_cm3:.2f} cm³")
                    c1.metric("Peso Estimado (Aço)", f"{peso:.2f} kg")
                    c2.metric("Preço Calculado", f"€ {preco:.2f}")

                    # Visualização Plotly
                    if len(mesh.faces) > 10000:
                         mesh = mesh.simplify_quadratic_decimation(5000) # Simplificar para web
                    
                    x, y, z = mesh.vertices.T
                    i, j, k = mesh.faces.T
                    
                    fig = go.Figure(data=[go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color='cyan', opacity=0.8, name='Peça')])
                    fig.update_layout(scene=dict(aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor="rgba(0,0,0,0)")
                    
                    with chart_container:
                        st.plotly_chart(fig, use_container_width=True)

# --- VISTA 2: ENGENHARIA ---
elif menu == "Engenharia & Design":
    st.title("🌪️ Simulação e Engenharia")
    
    tab1, tab2 = st.tabs(["Design Generativo", "Túnel de Vento (CFD)"])
    
    with tab1:
        st.subheader("Otimização de Refrigeração")
        st.markdown("Algoritmo genético para criação de canais conformais.")
        if st.button("Gerar Canais (Demo)"):
            st.success("Estrutura otimizada gerada com sucesso! Ganho térmico: +34%")
            # Demo visual dummy
            x = np.linspace(-2, 2, 50)
            y = np.linspace(-2, 2, 50)
            X, Y = np.meshgrid(x, y)
            Z = np.sin(np.sqrt(X**2 + Y**2))
            fig = go.Figure(data=[go.Surface(z=Z, colorscale='Electric')])
            fig.update_layout(scene=dict(aspectmode='cube'), margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig)

    with tab2:
        st.subheader("Análise de Fluido")
        st.info("Visualização do vetor de velocidade do fluido refrigerante.")
        # Cone plot demo
        x, y, z = np.meshgrid(np.arange(-5, 5, 2), np.arange(-5, 5, 2), np.arange(-5, 5, 2))
        u = y; v = -x; w = z*0.1
        fig = go.Figure(data=go.Cone(x=x.flatten(), y=y.flatten(), z=z.flatten(), u=u.flatten(), v=v.flatten(), w=w.flatten(), sizemode="absolute", sizeref=2))
        st.plotly_chart(fig)

# --- VISTA 3: BASE DE MOLDES ---
elif menu == "Base de Moldes":
    st.title("📦 Configurador Standard")
    c1, c2 = st.columns(2)
    with c1:
        fornecedor = st.selectbox("Fornecedor", ["Hasco", "Meusburger", "DME"])
        material = st.selectbox("Aço das Placas", ["1.1730", "1.2311", "1.2312"])
    with c2:
        tamanho = st.selectbox("Dimensões da Estrutura", ["296 x 296", "396 x 396", "496 x 496"])
        
    if st.button("⬇️ Download Assembly .STEP"):
        st.toast("A gerar geometria CAD...", icon="⚙️")
        import time
        time.sleep(1)
        st.success(f"Download pronto: Base_{fornecedor}_{tamanho}.step")

# --- VISTA 4: PRODUÇÃO ---
elif menu == "Produção":
    st.title("🏭 Chão de Fábrica")
    st.error("⚠️ ALERTA CRÍTICO: Vibração excessiva no Fuso da CNC-02")
    
    data = pd.DataFrame(np.random.randn(50, 3), columns=["CNC-01", "CNC-02", "EDM-01"])
    st.line_chart(data)
