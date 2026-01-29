import streamlit as st
import pandas as pd
import qrcode
import uuid
import os
from datetime import datetime
from urllib.parse import quote, unquote
import json

ARQUIVO_ESTOQUE = "estoque.xlsx"
IP_SERVIDOR = os.getenv("IP_LOCAL")

if not IP_SERVIDOR:
    IP_SERVIDOR = "localhost"

IP_SERVIDOR = f"http://{IP_SERVIDOR}:8501"

#IP_SERVIDOR = "http://10.166.88.100:8501"  # ⚠️ TROQUE se mudar
#IP_SERVIDOR = "http://192.168.3.5:8501"  # ⚠️ TROQUE se mudar
#IP_SERVIDOR = "http://192.168.88.121:8501"  # ⚠️ TROQUE se mudar 
# =====================
# Funções
# =====================
def carregar_estoque():
    if os.path.exists(ARQUIVO_ESTOQUE):
        return pd.read_excel(ARQUIVO_ESTOQUE)
    return pd.DataFrame(columns=[
    "id", "cliente", "fabrica", "medidas", "tipo", "data_entrada", "data_saida"
])

if "qr" in st.query_params:
    st.session_state["pagina"] = "📸 Ler QR Code"


def salvar_estoque(df):
    df.to_excel(ARQUIVO_ESTOQUE, index=False)

# =====================
# Interface
# =====================
st.set_page_config(page_title="Estoque", layout="centered")
def carregar_css():
    if os.path.exists("styles/style.css"):
        with open("styles/style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

carregar_css()
st.title("🪵 Controle de Estoque")

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "📦 Gerar Etiquetas"


menu = st.sidebar.radio(
    "📋 Menu",
    ["📦 Gerar Etiquetas", "📸 Ler QR Code", "📊 Estoque"]
)


st.session_state["pagina"] = menu

estoque = carregar_estoque()

import io

if st.button("Gerar"):
    for _ in range(quantidade):
        dados = {
            "id": str(uuid.uuid4()),
            "cliente": cliente,
            "fabrica": fabrica,
            "medidas": medidas,
            "tipo": tipo
        }

        json_texto = json.dumps(dados, ensure_ascii=False)
        json_url = quote(json_texto)

        link = f"{IP_SERVIDOR}/?qr={json_url}"

        qr = qrcode.make(link)

        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)

        st.image(buffer, caption="📦 QR Code da Etiqueta")

        st.download_button(
            label="⬇️ Baixar etiqueta",
            data=buffer,
            file_name=f"etiqueta_{dados['id']}.png",
            mime="image/png"
        )

    st.success("✅ Etiquetas geradas com sucesso!")


# =====================
# LEITURA AUTOMÁTICA
# =====================
elif menu == "📸 Ler QR Code":
    st.header("Leitura Automática")

    qr_param = st.query_params.get("qr")

    # guarda o QR na sessão
    if qr_param:
        st.session_state["qr"] = qr_param

    if "qr" not in st.session_state:
        st.info("📱 Leia o QR Code com o celular")
        st.stop()

    try:
        texto = unquote(st.session_state["qr"])

        if not texto.startswith("{"):
            st.error("❌ QR Code inválido")
            st.stop()

        dados = json.loads(texto)

        estoque = carregar_estoque()
        existe = estoque[estoque["id"] == dados["id"]]

        # =====================
        # ENTRADA
        # =====================
        if existe.empty:
            novo = {
                "id": dados["id"],
                "cliente": dados["cliente"],
                "fabrica": dados["fabrica"],
                "medidas": dados["medidas"],
                "tipo": dados["tipo"],
                "data_entrada": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "data_saida": ""
            }

            estoque = pd.concat([estoque, pd.DataFrame([novo])])
            salvar_estoque(estoque)

            st.success("✅ Entrada registrada no estoque")
            st.json(novo)

    # =====================
    # SAÍDA
    # =====================
        else:
            st.warning("⚠️ Item já está no estoque")

            if st.button("Confirmar SAÍDA"):
                estoque.loc[
                    estoque["id"] == dados["id"], "data_saida"
                ] = datetime.now().strftime("%d/%m/%Y %H:%M")

                salvar_estoque(estoque)

                # limpa tudo SÓ AGORA
                del st.session_state["qr"]
                st.query_params.clear()

                st.success("❌ Saída registrada")
                st.info("📱 Pronto para ler o próximo QR Code")
                st.stop()
                   
    except Exception as e:
        st.error("❌ Erro ao ler o QR Code")
        st.write(e)

   # =====================
    # BOTÃO SAIR DA LEITURA
    # =====================
    st.divider()

    if st.button("🚪 Sair da leitura"):
        st.session_state.pop("qr", None)
        st.query_params.clear()
        st.session_state["pagina"] = "📦 Gerar Etiquetas"
        st.rerun()

        
