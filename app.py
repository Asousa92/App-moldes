import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import pdfplumber
import tempfile
import os
import time
from datetime import datetime

# --- CADQUERY HANDLING ---
try:
    import cadquery as cq
    # Helper to convert CQ shape to Plotly Mesh3d
    def get_plotly_mesh(shape, tolerance=0.1):
        # Tessellate
        mesh = shape.val().tessellate(tolerance)
        vertices = []
        for v in mesh[0]:
            vertices.append([v.x, v.y, v.z])
        triangles = mesh[1]
        
        vertices = np.array(vertices)
        
        x, y, z = vertices.T
        i = [t[0] for t in triangles]
        j = [t[1] for t in triangles]
        k = [t[2] for t in triangles]
        
        return go.Mesh3d(
            x=x, y=y, z=z,
            i=i, j=j, k=k,
            color='#00FFFF',  # Neon Cyan
            opacity=0.50,
            flatshading=True,
            showscale=False,
            lighting=dict(ambient=0.5, diffuse=0.8, specular=0.5),
            lightposition=dict(x=100, y=100, z=1000)
        )
except ImportError:
    cq = None

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MetaMold AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Anti-Gravity / MetalMold Style) ---
st.markdown("""
<style>
    /* Global Reset & Background */
    .stApp {
        background-color: #0e1117; /* Deep Void Black */
        color: #e0e0e0;
        font-family: 'Roboto Mono', monospace;
    }
    
    /* Hide Streamlit Header/Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Typography */
    h1, h2, h3 {
        color: #f0f0f0;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
        letter-spacing: 1px;
    }
    
    /* Glassmorphism Cards */
    .css-1y4p8pa {
        padding: 2rem;
    }
    div[data-testid="stMetric"], div.stDataFrame, .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    
    /* Neon Accents */
    .neon-text {
        color: #00FFFF;
        text-shadow: 0 0 5px #00FFFF, 0 0 10px #00FFFF;
    }
    .alert-text {
        color: #FF5722; /* Industrial Orange */
        font-weight: bold;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: rgba(0, 255, 255, 0.1);
        color: #00FFFF;
        border: 1px solid #00FFFF;
        border-radius: 4px;
        text-transform: uppercase;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #00FFFF;
        color: #000;
        box-shadow: 0 0 15px #00FFFF;
    }
    
    /* Inputs */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05);
        color: #fff;
        border: 1px solid #333;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #050608;
        border-right: 1px solid #222;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("# ⬢ MetaMold AI")
st.sidebar.markdown(f"**Status:** `ONLINE`")
st.sidebar.markdown(f"**Kernel:** `{'CadQuery Loaded' if cq else 'Render Only'}`")

nav_options = [
    "A. Orçamentação Inteligente",
    "B. Engenharia & Design",
    "C. Gestão de Moldes",
    "D. Dashboard Live"
]
selection = st.sidebar.radio("Navegação", nav_options)

# --- MODULE A: ORÇAMENTAÇÃO ---
if selection == "A. Orçamentação Inteligente":
    st.markdown("## A. Orçamentação Inteligente")
    st.markdown("Analyze Technical Drawings (.PDF) or 3D Models (.STEP) for instant quoting.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Upload Zone")
        uploaded_file = st.file_uploader("Drop Files Here", type=['pdf', 'step', 'stp', 'stl'])
        
        quote_data = {}
        
        if uploaded_file:
            file_ext = uploaded_file.name.split('.')[-1].lower()
            
            # --- PDF LOGIC (Hardcoded Cases) ---
            if file_ext == "pdf":
                st.info("Parsing PDF Document...")
                with pdfplumber.open(uploaded_file) as pdf:
                    text_content = ""
                    for page in pdf.pages:
                        text_content += page.extract_text() or ""
                
                # Check Cases
                if "Calcador Temperado Interior" in text_content:
                    quote_data = {
                        "Ref": "Case 1: Calcador Temperado Interior",
                        "Material": "Aço 1.2379 (D2)",
                        "Weight": 1.642,
                        "Price": 309.52
                    }
                elif "Estrutura para embutir calcador interior" in text_content:
                    quote_data = {
                        "Ref": "Case 2: Estrutura para embutir calcador interior",
                        "Material": "Aço 1.1730 (C45)",
                        "Weight": 3.796,
                        "Price": 308.88
                    }
                elif "Estrutura para embutir calcador exterior" in text_content:
                    quote_data = {
                        "Ref": "Case 3: Estrutura para embutir calcador exterior",
                        "Material": "Aço 1.1730 (C45)",
                        "Weight": 7.782,
                        "Price": 361.92
                    }
                
                if quote_data:
                    st.markdown("<span class='neon-text'>⚡ Reconhecimento Histórico</span>", unsafe_allow_html=True)
                else:
                    st.warning("No historical match found.")

            # --- STEP/STP LOGIC ---
            elif file_ext in ["step", "stp"]:
                if cq:
                    try:
                        # Save temp file for CadQuery to read
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        # Import Shape
                        model = cq.importers.importShape(tmp_path)
                        vol = model.val().Volume() # mm^3
                        
                        # Calculations
                        # Steel density ~ 7.85 g/cm3 -> 0.00785 g/mm3 -> 7.85e-6 kg/mm3
                        density_kg_mm3 = 0.00000785
                        mass_kg = vol * density_kg_mm3
                        
                        # Simulation Price Formula
                        # (mass * 4.5) + (volume_cm3 * 0.05) + 150
                        vol_cm3 = vol / 1000.0
                        price = (mass_kg * 4.5) + (vol_cm3 * 0.05) + 150.0
                        
                        quote_data = {
                            "Ref": uploaded_file.name,
                            "Material": "Generic Steel (7.85g/cc)",
                            "Volume (cm3)": f"{vol_cm3:.2f}",
                            "Weight": mass_kg,
                            "Price": price
                        }
                        
                        # Visualization
                        with col2:
                            st.markdown("### Geometry Visualization")
                            fig = go.Figure(data=[get_plotly_mesh(model)])
                            fig.update_layout(
                                scene=dict(
                                    xaxis=dict(visible=False),
                                    yaxis=dict(visible=False),
                                    zaxis=dict(visible=False),
                                    bgcolor='rgba(0,0,0,0)'
                                ),
                                paper_bgcolor='rgba(0,0,0,0)',
                                margin=dict(l=0, r=0, t=0, b=0)
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                        os.unlink(tmp_path)
                        
                    except Exception as e:
                        st.error(f"Error processing STEP file: {e}")
                else:
                    st.error("CadQuery library not installed. Cannot process 3D model.")

    if quote_data:
        st.markdown("---")
        q_cols = st.columns(4)
        q_cols[0].metric("Referência", quote_data.get("Ref", "N/A"))
        q_cols[1].metric("Material", quote_data.get("Material", "N/A"))
        q_cols[2].metric("Weight (kg)", f"{quote_data.get('Weight', 0):.4f}")
        
        # Pricing Card
        price_val = quote_data.get('Price', 0)
        
        with col1:
             st.markdown("#### Quote Adjustments")
             qty = st.number_input("Quantity", min_value=1, value=1)
             
             final_price = price_val * qty
             if qty > 10:
                 final_price *= 0.90 # 10% discount
                 st.write("Disount Applied: 10%")
        
        with col2:
             st.markdown(f"""
             <div class="glass-card" style="text-align: center; border: 1px solid #00FFFF;">
                 <h3 style="margin:0;">PREÇO FINAL</h3>
                 <h1 class="neon-text" style="font-size: 3em;">€ {final_price:.2f}</h1>
             </div>
             """, unsafe_allow_html=True)


# --- MODULE B: ENGENHARIA ---
elif selection == "B. Engenharia & Design":
    st.markdown("## B. Engenharia & Design")
    
    tab1, tab2 = st.tabs(["Design Generativo", "Simulação CFD"])
    
    with tab1:
        st.markdown("### Otimização Topológica")
        st.write("Reduces weight while maintaining structural integrity.")
        if st.button("Executar Otimização"):
            with st.spinner("Processing procedural lattice generation..."):
                time.sleep(2)
                
                # Mock procedural visualization
                # Generate random lines within a cube
                x = np.random.rand(100)
                y = np.random.rand(100)
                z = np.random.rand(100)
                
                fig = go.Figure(data=go.Scatter3d(
                    x=x, y=y, z=z,
                    mode='lines+markers',
                    line=dict(color='#00FFFF', width=2),
                    marker=dict(size=3)
                ))
                fig.update_layout(
                    scene=dict(bgcolor='#0e1117'),
                    paper_bgcolor='#0e1117',
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
                st.success("Topology Optimized. Weight reduction: 34%")

    with tab2:
        st.markdown("### Túnel de Vento Virtual (CFD)")
        if st.button("Executar Túnel de Vento"):
            with st.spinner("Solving Navier-Stokes equations..."):
                time.sleep(2.5)
                
                # Mock Streamlines
                x, y, z = np.mgrid[-2:2:20j, -2:2:20j, -2:2:20j]
                u = -1 - x**2 + y
                v = 1 + x - y**2
                w = x*y - z
                
                fig = go.Figure(data=go.Streamtube(
                    x=x.flatten(), y=y.flatten(), z=z.flatten(),
                    u=u.flatten(), v=v.flatten(), w=w.flatten(),
                    colorscale='Cyan', 
                    showscale=False,
                    maxdisplayed=50
                ))
                fig.update_layout(
                    scene=dict(bgcolor='#0e1117'),
                    paper_bgcolor='#0e1117',
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)

# --- MODULE C: GESTÃO ---
elif selection == "C. Gestão de Moldes":
    st.markdown("## C. Gestão & Exportação")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Biblioteca de Normas")
        base_type = st.selectbox("Standard Base", ["Hasco K", "Meusburger P", "Pedrotti"])
        plate_size = st.select_slider("Plate Size (mm)", options=["156x156", "196x196", "246x246", "296x296"])
        
    with c2:
        st.markdown("### Exportação")
        st.info(f"Selected: {base_type} - {plate_size}")
        
        if st.button("Gerar Assembly .STEP"):
            # Mock file generation
            filename = f"Base_Molde_{datetime.now().strftime('%Y%m%d')}_{base_type.replace(' ', '')}.step"
            st.success(f"Assembly generated: {filename}")
            st.download_button(
                label="Download STEP",
                data=b"STEP-21; HEADER; ENDSEC; DATA; ENDSEC; END-ISO-10303-21;", # Mock content
                file_name=filename
            )

# --- MODULE D: DASHBOARD ---
elif selection == "D. Dashboard Live":
    st.markdown("## D. Dashboard & Manutenção")
    
    # 3 Top Cards
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.metric(label="Vibration (Spindle)", value="2.4 mm/s", delta="-0.2 mm/s")
    with m2:
        st.metric(label="Temp (Coolant)", value="24.5 °C", delta="0.5 °C", delta_color="inverse")
    with m3:
        st.metric(label="Load (Axis X)", value="85 %", delta="12 %")

    st.markdown("### Real-time Telemetry")
    
    # Live Chart Simulation
    chart_data = pd.DataFrame(
        np.random.randn(50, 3),
        columns=['Vibration', 'Temperature', 'Noise level']
    )
    st.line_chart(chart_data)
    
    st.markdown("### Alerts")
    st.markdown("""
    <div class="glass-card" style="border-left: 5px solid #FF5722;">
        <h4 class="alert-text">⚠️ PREDICTIVE MAINTENANCE ALERT</h4>
        <p>Anomaly detected in <strong>Fuso 2</strong> (Ball Screw). Estimated failure in 48h.</p>
        <button style="background:none; border:1px solid #FF5722; color:#FF5722; padding:5px;">Schedule Maintenance</button>
    </div>
    """, unsafe_allow_html=True)
