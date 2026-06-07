import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

# ===================================================
# BOTÃO DE CÁLCULO
# ===================================================

if st.button("🔍 Calcular", type="primary", use_container_width=True):
    try:
        # Peso próprio
        P1 = peso
        
        # Peso com vento
        if considerar_vento == "Sim" and p2 > 0:
            fv = D * p2
            P2 = np.sqrt(P1**2 + fv**2)
        else:
            P2 = P1
        
        # Temperatura corrigida para cálculo da condição final
        if cond == "Inicial → Final (com creep)":
            t2_calc = t2 + dt_creep
        elif cond == "Final → Inicial (com creep)":
            t2_calc = t2 - dt_creep
        else:
            t2_calc = t2
        
        # Cálculo da mudança de estado para condição final
        B = (E * area * P1**2 * A**2) / (24 * T01**2) + E * area * alpha * (t2_calc - t1) - T01
        C = (E * area * P2**2 * A**2) / 24
        
        roots = np.roots([1, B, 0, -C])
        T02 = roots[np.isreal(roots) & (roots > 0)].real
        
        if len(T02) == 0:
            st.error("❌ Nenhuma raiz física encontrada.")
        else:
            T02 = T02[0]
            
            # Flechas
            f1 = (P1 * A**2) / (8 * T01)
            f2 = (P2 * A**2) / (8 * T02)
            
            # ===================================================
            # EXIBIR RESULTADOS
            # ===================================================
            st.markdown("---")
            st.subheader("📊 RESULTADOS")
            
            # Tabela usando DataFrame
            dados_tabela = []
            
            # Tração
            variacao_t = T02 - T01
            perc_t = (variacao_t / T01) * 100 if T01 != 0 else 0
            seta_t = "▲" if variacao_t > 0 else "▼" if variacao_t < 0 else "●"
            cor_t = "🟢" if variacao_t > 0 else "🔴" if variacao_t < 0 else "⚪"
            
            dados_tabela.append({
                "Parâmetro": "Tração (kgf)",
                "Inicial": f"{T01:.1f} ({100*T01/cr:.1f}% CR)",
                "Final": f"{T02:.1f} ({100*T02/cr:.1f}% CR)",
                "Variação": f"{cor_t} {seta_t} {abs(variacao_t):.1f} ({abs(perc_t):.1f}%)"
            })
            
            # Flecha
            variacao_f = f2 - f1
            perc_f = (variacao_f / f1) * 100 if f1 != 0 else 0
            seta_f = "▲" if variacao_f > 0 else "▼" if variacao_f < 0 else "●"
            cor_f = "🟢" if variacao_f > 0 else "🔴" if variacao_f < 0 else "⚪"
            
            dados_tabela.append({
                "Parâmetro": "Flecha (m)",
                "Inicial": f"{f1:.3f}",
                "Final": f"{f2:.3f}",
                "Variação": f"{cor_f} {seta_f} {abs(variacao_f):.3f} ({abs(perc_f):.1f}%)"
            })
            
            df = pd.DataFrame(dados_tabela)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Detalhes adicionais
            st.markdown("---")
            st.subheader("📋 DETALHES")
            
            col_det1, col_det2, col_det3 = st.columns(3)
            with col_det1:
                st.metric("Cabo", cabo_selecionado)
                st.metric("CR", f"{cr:.1f} kgf")
            with col_det2:
                st.metric("Vão", f"{A} m")
                st.metric("Peso próprio (P1)", f"{P1:.4f} kgf/m")
                if considerar_vento == "Sim" and p2 > 0:
                    st.metric("Peso composto (P2)", f"{P2:.4f} kgf/m")
            with col_det3:
                st.metric("Temperatura 1", f"{t1:.1f} °C")
                st.metric("Temperatura 2", f"{t2:.1f} °C")
                if dt_creep != 0:
                    st.metric("Creep aplicado", f"{dt_creep:.1f} °C")
            
            # ===================================================
            # GRÁFICOS - EVOLUÇÃO COM A TEMPERATURA (0°C a 90°C)
            # ===================================================
            st.markdown("---")
            st.subheader("📈 EVOLUÇÃO COM A TEMPERATURA")
            
            # Gerar pontos de 0°C até 90°C (temperatura ORIGINAL, passo 1°C)
            temperaturas_orig = np.arange(0, 91, 1)
            
            flechas_evol = []
            tracoes_evol = []
            
            for temp_orig in temperaturas_orig:
                # Determinar temperatura corrigida para cálculo (se houver creep)
                if cond == "Inicial → Final (com creep)":
                    temp_calc = temp_orig + dt_creep
                elif cond == "Final → Inicial (com creep)":
                    temp_calc = temp_orig - dt_creep
                else:
                    temp_calc = temp_orig
                
                # Para a curva, SEMPRE usar P2 (peso com vento, se houver)
                peso_curva = P2
                
                # Cálculo da mudança de estado para este ponto
                B_temp = (E * area * P1**2 * A**2) / (24 * T01**2) + E * area * alpha * (temp_calc - t1) - T01
                C_temp = (E * area * peso_curva**2 * A**2) / 24
                
                roots_temp = np.roots([1, B_temp, 0, -C_temp])
                T_temp = roots_temp[np.isreal(roots_temp) & (roots_temp > 0)].real
                T_temp_val = T_temp[0] if len(T_temp) > 0 else T01
                
                flecha_temp = (peso_curva * A**2) / (8 * T_temp_val) if T_temp_val > 0 else 0
                flechas_evol.append(flecha_temp)
                tracoes_evol.append(T_temp_val)
            
            # Criar subplots com Plotly
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=("Flecha", "Tração"),
                shared_yaxes=False,
                horizontal_spacing=0.15
            )
            
            # Gráfico da Flecha
            fig.add_trace(
                go.Scatter(
                    x=temperaturas_orig,
                    y=flechas_evol,
                    mode='lines',
                    name='Evolução (com correções)',
                    line=dict(color='#1f77b4', width=2),
                    hovertemplate='<b>Temperatura: %{x:.0f}°C</b><br>Flecha: %{y:.3f} m<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Ponto da condição inicial (t1) - valores reais sem correções
            fig.add_trace(
                go.Scatter(
                    x=[t1],
                    y=[f1],
                    mode='markers',
                    name=f'Condição 1 ({t1:.0f}°C)',
                    marker=dict(size=14, color='red', symbol='circle'),
                    hovertemplate=f'<b>Condição 1 (real)</b><br>Temperatura: {t1:.0f}°C<br>Flecha: {f1:.3f} m<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Ponto da condição final (t2)
            fig.add_trace(
                go.Scatter(
                    x=[t2],
                    y=[f2],
                    mode='markers',
                    name=f'Condição 2 ({t2:.0f}°C)',
                    marker=dict(size=14, color='green', symbol='circle'),
                    hovertemplate=f'<b>Condição 2 (com correções)</b><br>Temperatura: {t2:.0f}°C<br>Flecha: {f2:.3f} m<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Gráfico da Tração
            fig.add_trace(
                go.Scatter(
                    x=temperaturas_orig,
                    y=tracoes_evol,
                    mode='lines',
                    name='Evolução (com correções)',
                    line=dict(color='#ff7f0e', width=2),
                    hovertemplate='<b>Temperatura: %{x:.0f}°C</b><br>Tração: %{y:.0f} kgf<extra></extra>'
                ),
                row=1, col=2
            )
            
            # Ponto da condição inicial (t1)
            fig.add_trace(
                go.Scatter(
                    x=[t1],
                    y=[T01],
                    mode='markers',
                    name=f'Condição 1 ({t1:.0f}°C)',
                    marker=dict(size=14, color='red', symbol='circle'),
                    hovertemplate=f'<b>Condição 1 (real)</b><br>Temperatura: {t1:.0f}°C<br>Tração: {T01:.0f} kgf<extra></extra>',
                    showlegend=False
                ),
                row=1, col=2
            )
            
            # Ponto da condição final (t2)
            fig.add_trace(
                go.Scatter(
                    x=[t2],
                    y=[T02],
                    mode='markers',
                    name=f'Condição 2 ({t2:.0f}°C)',
                    marker=dict(size=14, color='green', symbol='circle'),
                    hovertemplate=f'<b>Condição 2 (com correções)</b><br>Temperatura: {t2:.0f}°C<br>Tração: {T02:.0f} kgf<extra></extra>',
                    showlegend=False
                ),
                row=1, col=2
            )
            
            # Layout moderno
            fig.update_layout(
                title=dict(
                    text="<b>Evolução com a Temperatura</b>",
                    font=dict(size=16, color="#1f1f1f"),
                    x=0.5
                ),
                template="plotly_white",
                height=450,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='closest'
            )
            
            fig.update_xaxes(title_text="Temperatura (°C)", row=1, col=1)
            fig.update_yaxes(title_text="Flecha (m)", row=1, col=1)
            fig.update_xaxes(title_text="Temperatura (°C)", row=1, col=2)
            fig.update_yaxes(title_text="Tração (kgf)", row=1, col=2)
            
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Erro no cálculo: {e}")
