import streamlit as st
import numpy as np
import pandas as pd

# ===================================================
# CONFIGURAÇÃO DA PÁGINA
# ===================================================
st.set_page_config(
    page_title="Analisador de Flechas",
    page_icon="📏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📏 Analisador de Flechas - Mudança de Estado")
st.markdown("---")

# ===================================================
# BANCO DE DADOS DOS CABOS
# ===================================================
cabos_data = {
    1: {'nome': 'Grosbeak', 'peso': 1.3028, 'area': 374.8, 'E': 7593, 'alpha': 189e-7, 'CR': 11427, 'D': 0.02515},
    2: {'nome': 'Linnet', 'peso': 0.6883, 'area': 198, 'E': 7593, 'alpha': 189e-7, 'CR': 6393, 'D': 0.0183},
    3: {'nome': 'Penguin', 'peso': 0.433, 'area': 125.06, 'E': 8120, 'alpha': 186e-7, 'CR': 3790, 'D': 0.01431},
    4: {'nome': 'Cairo AAAC 6201', 'peso': 0.651, 'area': 236.38, 'E': 8120, 'alpha': 186e-7, 'CR': 7106.3, 'D': 0.0199},
    5: {'nome': 'Raven', 'peso': 0.217, 'area': 125.09, 'E': 7593, 'alpha': 189e-7, 'CR': 1985, 'D': 0.01011},
    6: {'nome': 'Flint', 'peso': 1.035, 'area': 374.52, 'E': 8120, 'alpha': 186e-7, 'CR': 11012.8, 'D': 0.0251},
    7: {'nome': 'Drake', 'peso': 1.629, 'area': 468, 'E': 7593, 'alpha': 189e-7, 'CR': 14245, 'D': 0.02813}
}

# ===================================================
# FUNÇÕES AUXILIARES
# ===================================================

def mudanca_estado(T_initial, temp_initial, temp_final, peso_initial, peso_final, vao, E, S, alpha):
    B = (E * S * peso_initial**2 * vao**2) / (24 * T_initial**2) + E * S * alpha * (temp_final - temp_initial) - T_initial
    C = (E * S * peso_final**2 * vao**2) / 24
    roots = np.roots([1, B, 0, -C])
    T_final = roots[np.isreal(roots) & (roots > 0)].real
    if len(T_final) == 0:
        return T_initial
    return T_final[0]

# ===================================================
# INTERFACE - 2 COLUNAS
# ===================================================

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.subheader("📦 1. DADOS DO CABO")
    
    cabos_nomes = [cabos_data[i]['nome'] for i in cabos_data.keys()]
    cabo_selecionado = st.selectbox("Tipo de cabo", cabos_nomes, index=1)
    caboid = [i for i in cabos_data.keys() if cabos_data[i]['nome'] == cabo_selecionado][0]
    
    cr = cabos_data[caboid]['CR']
    peso = cabos_data[caboid]['peso']
    area = cabos_data[caboid]['area']
    E = cabos_data[caboid]['E']
    alpha = cabos_data[caboid]['alpha']
    D = cabos_data[caboid]['D']
    
    st.markdown("---")
    st.subheader("🌡️ 2. TEMPERATURAS")
    
    t1 = st.number_input("Temperatura inicial t1 (°C)", value=25.0, step=0.1)
    t2 = st.number_input("Temperatura final t2 (°C)", value=75.0, step=0.1)
    
    st.markdown("---")
    st.subheader("🔄 3. MUDANÇA DE ESTADO")
    
    cond = st.selectbox("Condição da mudança", [
        "Inicial → Inicial",
        "Final → Final",
        "Inicial → Final (com creep)",
        "Final → Inicial (com creep)"
    ], index=2)
    
    if "creep" in cond.lower():
        dt_creep = st.number_input("Equivalente térmico de creep (°C)", value=0.0, step=0.1)
    else:
        dt_creep = 0

with col2:
    st.subheader("⚙️ 4. PARÂMETROS DE CARGA")
    
    modo_tracao = st.selectbox("Modo da tração inicial", ["Valor em kgf", "Percentual CR"], index=1)
    
    if modo_tracao == "Valor em kgf":
        T01 = st.number_input("Tração inicial T01 (kgf)", value=3000.0, step=10.0)
    else:
        perc_T01 = st.number_input("Tração inicial (% CR)", value=10.0, step=0.5, min_value=1.0, max_value=20.0)
        T01 = cr * (perc_T01 / 100)
    
    st.markdown("---")
    st.subheader("🌬️ 5. VENTO")
    
    considerar_vento = st.selectbox("Considerar vento?", ["Não", "Sim"], index=0)
    
    if considerar_vento == "Sim":
        p2 = st.number_input("Pressão de vento (kgf/m²)", value=50.0, step=1.0, min_value=0.0, max_value=200.0)
    else:
        p2 = 0
    
    st.markdown("---")
    st.subheader("📏 6. GEOMETRIA")
    
    A = st.number_input("Vão A (m)", value=100.0, step=1.0, min_value=1.0, max_value=600.0)
    
    analise_flechas = st.checkbox("Analisar flechas", value=True)

# ===================================================
# BOTÃO DE CÁLCULO
# ===================================================

if st.button("🔍 Calcular", type="primary", use_container_width=True):
    try:
        # Peso próprio
        P1 = peso
        
        # Peso com vento
        if considerar_vento == "Sim" and p2 > 0:
            P2 = np.sqrt(P1**2 + (D * p2)**2)
        else:
            P2 = P1
        
        # Temperaturas equivalentes (com creep)
        if cond == "Inicial → Final (com creep)":
            t2_eq = t2 + dt_creep
            t1_eq = t1
            mensagem_creep = f"Temperatura 2 corrigida = {t2_eq:.1f} °C"
        elif cond == "Final → Inicial (com creep)":
            t2_eq = t2 - dt_creep
            t1_eq = t1
            mensagem_creep = f"Temperatura 2 corrigida = {t2_eq:.1f} °C"
        else:
            t1_eq = t1
            t2_eq = t2
            mensagem_creep = None
        
        # Cálculo da mudança de estado
        B = (E * area * P1**2 * A**2) / (24 * T01**2) + E * area * alpha * (t2_eq - t1_eq) - T01
        C = (E * area * P2**2 * A**2) / 24
        
        roots = np.roots([1, B, 0, -C])
        T02 = roots[np.isreal(roots) & (roots > 0)].real
        
        if len(T02) == 0:
            st.error("❌ Nenhuma raiz física encontrada.")
        else:
            T02 = T02[0]
            
            # ===================================================
            # EXIBIR RESULTADOS
            # ===================================================
            st.markdown("---")
            st.subheader("📊 RESULTADOS")
            
            # Métricas
            col_met1, col_met2 = st.columns(2)
            with col_met1:
                st.metric("Tração Inicial (T01)", f"{T01:.2f} kgf", f"{100*T01/cr:.2f} %CR")
            with col_met2:
                st.metric("Tração Final (T02)", f"{T02:.2f} kgf", f"{100*T02/cr:.2f} %CR")
            
            # Detalhes
            st.markdown("---")
            st.subheader("📋 DETALHES")
            
            detalhes = {
                "Cabo": cabo_selecionado,
                "CR": f"{cr:.1f} kgf",
                "Temperatura 1": f"{t1_eq:.1f} °C",
                "Temperatura 2": f"{t2_eq:.1f} °C",
                "Peso próprio (P1)": f"{P1:.4f} kgf/m",
                "Peso com vento (P2)": f"{P2:.4f} kgf/m",
            }
            
            if mensagem_creep:
                detalhes["Creep"] = f"{dt_creep:.1f} °C"
                detalhes["Temperatura 2 corrigida"] = f"{t2_eq:.1f} °C"
            
            for key, value in detalhes.items():
                st.text(f"   {key}: {value}")
            
            # Flechas
            if analise_flechas:
                f1 = (P1 * A**2) / (8 * T01)
                f2 = (P2 * A**2) / (8 * T02)
                
                st.markdown("---")
                st.subheader("📈 FLECHAS")
                
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    st.metric("Flecha inicial (f1)", f"{f1:.3f} m")
                with col_f2:
                    st.metric("Flecha final (f2)", f"{f2:.3f} m")
                with col_f3:
                    st.metric("Δf", f"{f2 - f1:.3f} m")
            
            # Tabela de esticamento
            st.markdown("---")
            st.subheader("📊 TABELA DE ESTICAMENTO")
            
            # Inputs para tabela
            col_tab1, col_tab2 = st.columns(2)
            with col_tab1:
                temp_eds = st.number_input("Temp EDS (°C)", value=20.0, step=0.5)
            with col_tab2:
                eds_percent = st.number_input("EDS (%CR)", value=20.0, step=0.5, min_value=1.0, max_value=100.0)
            
            if st.button("📊 Gerar tabela de esticamento", use_container_width=True):
                # Tração EDS em kgf
                t_eds_kgf = cr * (eds_percent / 100.0)
                
                # Gerar dados da tabela
                dados = []
                for temp in range(15, 36):
                    temp_equivalente = temp - dt_creep
                    
                    B_tab = (E * area * P1**2 * A**2) / (24 * t_eds_kgf**2) + E * area * alpha * (temp_equivalente - temp_eds) - t_eds_kgf
                    C_tab = (E * area * P1**2 * A**2) / 24
                    
                    roots_tab = np.roots([1, B_tab, 0, -C_tab])
                    tracao = roots_tab[np.isreal(roots_tab) & (roots_tab > 0)].real
                    tracao_val = tracao[0] if len(tracao) > 0 else 0
                    
                    percent_cr = (tracao_val / cr) * 100.0 if cr > 0 else 0
                    flecha = (P1 * A**2) / (8 * tracao_val) if tracao_val > 0 else 0
                    
                    dados.append({
                        'Temp (°C)': temp,
                        'Tração (%CR)': f"{percent_cr:.2f}",
                        'Tração (kgf)': f"{tracao_val:.1f}",
                        'Flecha (m)': f"{flecha:.3f}"
                    })
                
                df = pd.DataFrame(dados)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Download Excel
                from io import BytesIO
                import base64
                
                output_excel = BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Tabela Esticamento', index=False)
                
                output_excel.seek(0)
                b64 = base64.b64encode(output_excel.read()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="tabela_esticamento.xlsx">📎 Download Excel</a>'
                st.markdown(href, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Erro no cálculo: {e}")
