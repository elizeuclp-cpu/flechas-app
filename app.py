import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
import base64

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

def format_variacao(valor_inicial, valor_final):
    variacao = valor_final - valor_inicial
    percentual = (variacao / valor_inicial) * 100 if valor_inicial != 0 else 0
    
    if variacao > 0:
        seta = "▲"
        cor = "green"
    elif variacao < 0:
        seta = "▼"
        cor = "red"
    else:
        seta = "●"
        cor = "gray"
    
    return f'{seta} {variacao:+.3f} ({percentual:+.1f}%)', cor

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

calcular = st.button("🔍 Calcular", type="primary", use_container_width=True)

if calcular:
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
            
            # Flechas
            f1 = (P1 * A**2) / (8 * T01)
            f2 = (P2 * A**2) / (8 * T02)
            
            # Salvar resultados no session_state
            st.session_state['P1'] = P1
            st.session_state['P2'] = P2
            st.session_state['T01'] = T01
            st.session_state['T02'] = T02
            st.session_state['f1'] = f1
            st.session_state['f2'] = f2
            st.session_state['cr'] = cr
            st.session_state['E'] = E
            st.session_state['area'] = area
            st.session_state['alpha'] = alpha
            st.session_state['A'] = A
            st.session_state['dt_creep'] = dt_creep
            st.session_state['cabo_selecionado'] = cabo_selecionado
            st.session_state['t1_eq'] = t1_eq
            st.session_state['t2_eq'] = t2_eq
            st.session_state['mensagem_creep'] = mensagem_creep
            st.session_state['analise_flechas'] = analise_flechas
            st.session_state['resultado_pronto'] = True
            
            # ===================================================
            # EXIBIR RESULTADOS
            # ===================================================
            st.markdown("---")
            st.subheader("📊 RESULTADOS")
            
            # TABELA COMPARATIVA (Opção 4 com cores)
            variacao_tracao, cor_tracao = format_variacao(T01, T02)
            variacao_flecha, cor_flecha = format_variacao(f1, f2)
            
            # Criar HTML para tabela com cores
            tabela_html = f"""
            <style>
                .tabela-resultado {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 16px;
                    text-align: center;
                }}
                .tabela-resultado th {{
                    background-color: #1f1f1f;
                    color: white;
                    padding: 12px;
                    border: 1px solid #ddd;
                }}
                .tabela-resultado td {{
                    padding: 10px;
                    border: 1px solid #ddd;
                }}
                .verde {{ color: #2ca02c; font-weight: bold; }}
                .vermelho {{ color: #d62728; font-weight: bold; }}
                .cinza {{ color: #7f7f7f; font-weight: bold; }}
            </style>
            <table class="tabela-resultado">
                <tr>
                    <th>Parâmetro</th>
                    <th>Inicial</th>
                    <th>Final</th>
                    <th>Variação</th>
                </tr>
                <tr>
                    <td><b>Tração (kgf)</b></td>
                    <td>{T01:.1f} ({100*T01/cr:.1f}% CR)</td>
                    <td>{T02:.1f} ({100*T02/cr:.1f}% CR)</td>
                    <td class="{cor_tracao}">{variacao_tracao}</td>
                </tr>
            """
            
            if analise_flechas:
                tabela_html += f"""
                <tr>
                    <td><b>Flecha (m)</b></td>
                    <td>{f1:.3f}</td>
                    <td>{f2:.3f}</td>
                    <td class="{cor_flecha}">{variacao_flecha}</td>
                </tr>
                """
            
            tabela_html += "</table>"
            st.markdown(tabela_html, unsafe_allow_html=True)
            
            # Detalhes adicionais
            st.markdown("---")
            st.subheader("📋 DETALHES")
            
            col_det1, col_det2 = st.columns(2)
            with col_det1:
                st.metric("Cabo", cabo_selecionado)
                st.metric("CR", f"{cr:.1f} kgf")
                st.metric("Vão", f"{A} m")
            with col_det2:
                st.metric("Temperatura 1", f"{t1_eq:.1f} °C")
                st.metric("Temperatura 2", f"{t2_eq:.1f} °C")
                if mensagem_creep:
                    st.metric("Creep", f"{dt_creep:.1f} °C")
            
            # ===================================================
            # GRÁFICOS MODERNOS COM PLOTLY (Opção 3)
            # ===================================================
            if analise_flechas:
                st.markdown("---")
                st.subheader("📈 EVOLUÇÃO COM A TEMPERATURA")
                
                # Gerar pontos de t1 até 90°C (passo 1°C)
                temp_max = max(90, t2_eq)
                temperaturas = np.arange(t1_eq, temp_max + 1, 1)
                
                flechas_evol = []
                tracoes_evol = []
                
                for temp in temperaturas:
                    # Ajustar temperatura com creep se aplicável
                    if "creep" in cond.lower():
                        temp_eq = temp - dt_creep
                    else:
                        temp_eq = temp
                    
                    B_temp = (E * area * P1**2 * A**2) / (24 * T01**2) + E * area * alpha * (temp_eq - t1_eq) - T01
                    C_temp = (E * area * P2**2 * A**2) / 24
                    
                    roots_temp = np.roots([1, B_temp, 0, -C_temp])
                    T_temp = roots_temp[np.isreal(roots_temp) & (roots_temp > 0)].real
                    T_temp_val = T_temp[0] if len(T_temp) > 0 else T01
                    
                    flecha_temp = (P2 * A**2) / (8 * T_temp_val) if T_temp_val > 0 else 0
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
                        x=temperaturas,
                        y=flechas_evol,
                        mode='lines+markers',
                        name='Flecha',
                        line=dict(color='#1f77b4', width=2),
                        marker=dict(size=4, color='#1f77b4'),
                        hovertemplate='<b>Temperatura: %{x:.0f}°C</b><br>Flecha: %{y:.3f} m<extra></extra>'
                    ),
                    row=1, col=1
                )
                
                # Ponto da condição inicial (t1)
                idx_t1 = np.where(temperaturas >= t1_eq)[0]
                if len(idx_t1) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=[t1_eq],
                            y=[f1],
                            mode='markers',
                            name=f'Inicial ({t1_eq:.0f}°C)',
                            marker=dict(size=12, color='red', symbol='circle'),
                            hovertemplate=f'<b>Condição Inicial</b><br>Temperatura: {t1_eq:.0f}°C<br>Flecha: {f1:.3f} m<extra></extra>'
                        ),
                        row=1, col=1
                    )
                
                # Ponto da condição final (t2_eq)
                idx_t2 = np.where(temperaturas >= t2_eq)[0]
                if len(idx_t2) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=[t2_eq],
                            y=[f2],
                            mode='markers',
                            name=f'Final ({t2_eq:.0f}°C)',
                            marker=dict(size=12, color='green', symbol='circle'),
                            hovertemplate=f'<b>Condição Final</b><br>Temperatura: {t2_eq:.0f}°C<br>Flecha: {f2:.3f} m<extra></extra>'
                        ),
                        row=1, col=1
                    )
                
                # Gráfico da Tração
                fig.add_trace(
                    go.Scatter(
                        x=temperaturas,
                        y=tracoes_evol,
                        mode='lines+markers',
                        name='Tração',
                        line=dict(color='#ff7f0e', width=2),
                        marker=dict(size=4, color='#ff7f0e'),
                        hovertemplate='<b>Temperatura: %{x:.0f}°C</b><br>Tração: %{y:.0f} kgf<extra></extra>'
                    ),
                    row=1, col=2
                )
                
                # Ponto da condição inicial (t1)
                if len(idx_t1) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=[t1_eq],
                            y=[T01],
                            mode='markers',
                            name=f'Inicial ({t1_eq:.0f}°C)',
                            marker=dict(size=12, color='red', symbol='circle'),
                            hovertemplate=f'<b>Condição Inicial</b><br>Temperatura: {t1_eq:.0f}°C<br>Tração: {T01:.0f} kgf<extra></extra>',
                            showlegend=False
                        ),
                        row=1, col=2
                    )
                
                # Ponto da condição final (t2_eq)
                if len(idx_t2) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=[t2_eq],
                            y=[T02],
                            mode='markers',
                            name=f'Final ({t2_eq:.0f}°C)',
                            marker=dict(size=12, color='green', symbol='circle'),
                            hovertemplate=f'<b>Condição Final</b><br>Temperatura: {t2_eq:.0f}°C<br>Tração: {T02:.0f} kgf<extra></extra>',
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
                
                # Configurar eixos
                fig.update_xaxes(title_text="Temperatura (°C)", row=1, col=1)
                fig.update_yaxes(title_text="Flecha (m)", row=1, col=1)
                fig.update_xaxes(title_text="Temperatura (°C)", row=1, col=2)
                fig.update_yaxes(title_text="Tração (kgf)", row=1, col=2)
                
                st.plotly_chart(fig, use_container_width=True)
            
            # ===================================================
            # TABELA DE ESTICAMENTO
            # ===================================================
            st.markdown("---")
            st.subheader("📊 TABELA DE ESTICAMENTO")
            
            col_tab1, col_tab2 = st.columns(2)
            with col_tab1:
                temp_eds = st.number_input("Temp EDS (°C)", value=20.0, step=0.5, key="temp_eds_tab")
            with col_tab2:
                eds_percent = st.number_input("EDS (%CR)", value=20.0, step=0.5, min_value=1.0, max_value=100.0, key="eds_percent_tab")
            
            if st.button("📊 Gerar tabela de esticamento", key="btn_gerar_tabela"):
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
                output_excel = BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Tabela Esticamento', index=False)
                
                output_excel.seek(0)
                b64 = base64.b64encode(output_excel.read()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="tabela_esticamento.xlsx">📎 Download Excel</a>'
                st.markdown(href, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"❌ Erro no cálculo: {e}")
