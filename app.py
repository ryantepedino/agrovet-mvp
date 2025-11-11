import io
import re
from typing import List, Dict, Tuple

import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd

try:
    from pdf2image import convert_from_bytes
    PDF_OK = True
except Exception:
    PDF_OK = False

st.set_page_config(page_title="AgroVet Metrics - MVP", page_icon="🐄", layout="wide")

st.title("🐄 AgroVet Metrics – MVP (OCR + Métricas Reprodutivas)")
st.write("Faça upload de um **PDF** ou **imagem** (JPG/PNG). O app fará OCR (PT-BR) e tentará extrair métricas reprodutivas.")


# -----------------------------
# Funções de OCR e parsing
# -----------------------------
def ocr_image(img: Image.Image) -> str:
    """Executa OCR em PT-BR usando Tesseract."""
    return pytesseract.image_to_string(img, lang="por")


def pdf_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    if not PDF_OK:
        st.warning("Suporte a PDF indisponível nesta build. Envie imagem (JPG/PNG) ou habilite poppler (apt.txt).")
        return []
    pages = convert_from_bytes(pdf_bytes, dpi=300)
    return pages


def parse_metrics(text: str) -> Dict[str, float]:
    """
    Tenta localizar métricas por padrões simples (regex).
    Ajuste os padrões conforme seus relatórios.
    """
    clean = " ".join(text.lower().split())

    patterns = {
        "taxa_prenhez_%": r"(taxa\s*de\s*prenhez|prenhez)\D+(\d{1,3}[,.]?\d*)\s*%",
        "taxa_concepcao_%": r"(taxa\s*de\s*concep(ç|c)ão|concep(ç|c)ão)\D+(\d{1,3}[,.]?\d*)\s*%",
        "intervalo_partos_dias": r"(intervalo\s*entre\s*partos)\D+(\d{2,4})\s*d",
        "n_inseminacoes_por_prenha": r"(insemin(a|á)ções\s*por\s*prenhez)\D+(\d+[,.]?\d*)",
        "ia_total": r"(quantidade\s*de\s*ia|total\s*de\s*ia)\D+(\d+)",
        "partos_total": r"(total\s*de\s*partos)\D+(\d+)",
        "abortos_%": r"(taxa\s*de\s*aborto|aborto)\D+(\d{1,3}[,.]?\d*)\s*%",
    }

    results = {}
    for key, pat in patterns.items():
        m = re.search(pat, clean, flags=re.IGNORECASE)
        if m:
            # último grupo tem o número
            raw = m.groups()[-1]
            raw = raw.replace(",", ".")
            try:
                results[key] = float(raw)
            except:
                pass

    return results


def compute_kpis(metrics: Dict[str, float]) -> Dict[str, float]:
    """
    KPIs derivados (exemplos simples).
    """
    out = {}

    # Exemplo: Prenhez esperada vs. Concepção (se ambos existirem)
    if "taxa_prenhez_%" in metrics and "taxa_concepcao_%":
        # só um exemplo, ajuste à sua realidade
        out["gap_prenhez_vs_concepcao_%"] = metrics["taxa_concepcao_%"] - metrics.get("taxa_prenhez_%", 0.0)

    # Exemplo: IEP (intervalo entre partos) -> partos/ano
    if "intervalo_partos_dias" in metrics and metrics["intervalo_partos_dias"] > 0:
        out["partos_por_vaca_ano"] = 365.0 / metrics["intervalo_partos_dias"]

    return out


# -----------------------------
# UI – Upload & Processamento
# -----------------------------
up = st.file_uploader("Envie um PDF ou Imagem", type=["pdf", "png", "jpg", "jpeg"])

if up is not None:
    all_text = ""

    if up.name.lower().endswith(".pdf"):
        bytes_data = up.read()
        pages = pdf_to_images(bytes_data)
        if not pages:
            st.stop()

        st.info(f"PDF com {len(pages)} página(s). Processando OCR...")
        for i, pg in enumerate(pages, 1):
            st.caption(f"OCR página {i}…")
            txt = ocr_image(pg)
            all_text += "\n" + txt

    else:
        # imagem única
        img = Image.open(up).convert("RGB")
        st.image(img, caption="Pré-visualização")
        all_text = ocr_image(img)

    with st.expander("📝 Texto OCR (resultado bruto)"):
        st.text_area("OCR", all_text, height=250)

    # parsing
    m = parse_metrics(all_text)
    k = compute_kpis(m)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📌 Métricas extraídas")
        if m:
            st.table(pd.DataFrame([m]))
        else:
            st.warning("Nenhuma métrica padrão foi localizada. Ajuste os padrões (regex) de `parse_metrics` conforme seu layout.")

    with col2:
        st.subheader("📈 KPIs derivados")
        if k:
            st.table(pd.DataFrame([k]))
        else:
            st.info("Sem KPIs derivados calculados para este caso.")

    # Exportações
    df_export = pd.DataFrame([{**m, **k}]) if (m or k) else pd.DataFrame()
    if not df_export.empty:
        st.download_button(
            "⬇️ Exportar CSV",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name="agrovet_metrics.csv",
            mime="text/csv"
        )

st.markdown("---")
st.caption("© 2025 AgroVet Metrics – MVP • Desenvolvido por Data Tech Soluções em I.A.")

