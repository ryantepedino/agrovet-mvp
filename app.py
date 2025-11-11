import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import io
from fpdf import FPDF

st.set_page_config(page_title="AgroVet Metrics", layout="wide")

# ===============================
# CABEÇALHO
# ===============================
st.title("🐄 AgroVet Metrics — Painel de Desempenho Reprodutivo")
st.markdown("#### Sistema de acompanhamento e métricas veterinárias baseadas em IA")

# ===============================
# FORMULÁRIO DE DADOS
# ===============================
with st.form("dados_reprodutivos"):
    st.subheader("📋 Inserir Dados de Medição")
    fazenda = st.text_input("Nome da Fazenda", "")
    data_medicao = st.date_input("Data da Medição", date.today())
    matrizes = st.number_input("Total de Matrizes", 0)
    aptas = st.number_input("Matrizes Aptas à Reprodução", 0)
    inseminadas = st.number_input("Matrizes Inseminadas", 0)
    gestantes = st.number_input("Matrizes Gestantes (Prenhes)", 0)
    diagnosticos_positivos = st.number_input("Diagnósticos Positivos", 0)
    partos_previstos = st.number_input("Partos Previstos", 0)
    partos_reais = st.number_input("Partos Realizados", 0)
    perdas = st.number_input("Perdas Gestacionais", 0)
    servicos_repetidos = st.number_input("Serviços Repetidos", 0)
    observacoes = st.text_area("Observações", "")
    enviar = st.form_submit_button("Gerar Métricas e Dashboards")

# ===============================
# CÁLCULOS DE MÉTRICAS
# ===============================
if enviar:
    try:
        taxa_servico = (inseminadas / aptas * 100) if aptas > 0 else 0
        taxa_prenhez = (gestantes / inseminadas * 100) if inseminadas > 0 else 0
        taxa_concepcao = (diagnosticos_positivos / inseminadas * 100) if inseminadas > 0 else 0
        taxa_diagnostico = (diagnosticos_positivos / aptas * 100) if aptas > 0 else 0
        taxa_partos = (partos_reais / partos_previstos * 100) if partos_previstos > 0 else 0
        eficiencia_reprodutiva = (gestantes / matrizes * 100) if matrizes > 0 else 0
        perdas_gestacionais = (perdas / gestantes * 100) if gestantes > 0 else 0

        st.success("✅ Métricas calculadas com sucesso!")

        # ===============================
        # EXIBIR MÉTRICAS PRINCIPAIS
        # ===============================
        col1, col2, col3 = st.columns(3)
        col1.metric("Taxa de Serviço", f"{taxa_servico:.1f}%")
        col2.metric("Taxa de Prenhez", f"{taxa_prenhez:.1f}%")
        col3.metric("Taxa de Concepção", f"{taxa_concepcao:.1f}%")

        col4, col5, col6 = st.columns(3)
        col4.metric("Taxa de Diagnóstico", f"{taxa_diagnostico:.1f}%")
        col5.metric("Taxa de Partos", f"{taxa_partos:.1f}%")
        col6.metric("Eficiência Reprodutiva", f"{eficiencia_reprodutiva:.1f}%")

        col7, _ = st.columns([1, 2])
        col7.metric("Perdas Gestacionais", f"{perdas_gestacionais:.1f}%")

        # ===============================
        # GRÁFICOS INTERATIVOS
        # ===============================
        st.subheader("📊 Dashboards Interativos")

        df = pd.DataFrame({
            "Indicador": [
                "Taxa de Serviço", "Taxa de Prenhez", "Taxa de Concepção",
                "Taxa de Diagnóstico", "Taxa de Partos", "Eficiência Reprodutiva", "Perdas Gestacionais"
            ],
            "Valor (%)": [
                taxa_servico, taxa_prenhez, taxa_concepcao,
                taxa_diagnostico, taxa_partos, eficiencia_reprodutiva, perdas_gestacionais
            ]
        })

        # Barra
        fig_bar = px.bar(df, x="Indicador", y="Valor (%)", color="Indicador",
                         title="Comparativo de Indicadores Reprodutivos",
                         text_auto=".1f")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Gauge principal
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=eficiencia_reprodutiva,
            title={'text': "Eficiência Global"},
            delta={'reference': 80},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "green"},
                   'steps': [
                       {'range': [0, 60], 'color': "lightcoral"},
                       {'range': [60, 80], 'color': "gold"},
                       {'range': [80, 100], 'color': "lightgreen"}]}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Observações
        if observacoes.strip():
            st.info(f"📝 **Observações:** {observacoes}")

        # Dados resumidos
        resumo = pd.DataFrame([{
            "Fazenda": fazenda,
            "Data": data_medicao,
            "Taxa Serviço (%)": taxa_servico,
            "Taxa Prenhez (%)": taxa_prenhez,
            "Taxa Concepção (%)": taxa_concepcao,
            "Eficiência (%)": eficiencia_reprodutiva,
            "Perdas Gestacionais (%)": perdas_gestacionais
        }])

        st.dataframe(resumo, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erro ao calcular métricas: {e}")

# ===============================
# EXPORTAR RELATÓRIO (fora do try)
# ===============================
if "resumo" in locals():
    st.markdown("---")
    st.subheader("📤 Exportar Relatório")

    # Exportar para Excel
    excel_buffer = io.BytesIO()
    resumo.to_excel(excel_buffer, index=False)
    st.download_button(
        label="⬇️ Baixar Relatório em Excel (.xlsx)",
        data=excel_buffer.getvalue(),
        file_name=f"Relatorio_{fazenda}_{data_medicao}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Exportar para PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Relatório AgroVet Metrics", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Fazenda: {fazenda}", ln=True)
    pdf.cell(200, 10, txt=f"Data: {data_medicao}", ln=True)
    pdf.ln(5)

    for coluna, valor in resumo.iloc[0].items():
        pdf.cell(200, 8, txt=f"{coluna}: {valor}", ln=True)

    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    st.download_button(
        label="📄 Baixar Relatório em PDF (.pdf)",
        data=pdf_buffer.getvalue(),
        file_name=f"Relatorio_{fazenda}_{data_medicao}.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Gere as métricas primeiro para exportar o relatório.")
