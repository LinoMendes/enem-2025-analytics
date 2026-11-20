import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

RAIZ = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ / "src"))

from database import get_engine

st.set_page_config(
    page_title="Painel Analítico — ENEM 2025",
    page_icon="📊",
    layout="wide",
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA (CARDS, CABEÇALHO E ABAS) ---
st.markdown("""
<style>
    .header-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.15);
    }
    .header-banner h1 {
        color: #FFFFFF !important;
        font-size: 1.85rem;
        margin: 0;
        font-weight: 700;
    }
    .header-banner p {
        color: #DBEAFE;
        margin: 0.35rem 0 0 0;
        font-size: 0.95rem;
    }

    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #2563EB;
        padding: 1rem 1.25rem;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }

    [data-testid="stPlotlyChart"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 0.75rem;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #EFF6FF !important;
        border-color: #2563EB !important;
        color: #1E40AF !important;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-banner">
    <h1>📊 Observatório Analítico — Microdados ENEM 2025</h1>
    <p>Indicadores socioeconômicos e desempenho acadêmico por Unidade Federativa (UF) • PostgreSQL + Python</p>
</div>
""", unsafe_allow_html=True)

COORDENADAS_UF = {
    "AC": (-9.0238, -70.8120), "AL": (-9.5713, -36.7820), "AM": (-3.4168, -65.8561),
    "AP": (1.4144, -51.7700),  "BA": (-12.5797, -41.7007), "CE": (-5.4984, -39.3206),
    "DF": (-15.7998, -47.8645), "ES": (-19.1834, -40.3089), "GO": (-15.8270, -49.8362),
    "MA": (-4.9609, -45.2744), "MG": (-18.5122, -44.5550), "MS": (-20.7722, -54.7852),
    "MT": (-12.6819, -56.9211), "PA": (-3.4168, -52.1679), "PB": (-7.2400, -36.7820),
    "PE": (-8.8137, -36.9541), "PI": (-7.7183, -42.7289), "PR": (-24.8932, -51.5500),
    "RJ": (-22.9068, -43.1729), "RN": (-5.4026, -36.9541), "RO": (-10.8300, -63.3400),
    "RR": (2.7376, -62.0751),  "RS": (-30.0346, -51.2177), "SC": (-27.2423, -50.2189),
    "SE": (-10.5741, -37.3857), "SP": (-23.5505, -46.6333), "TO": (-10.1753, -48.2982),
}


@st.cache_data(ttl=86400)
def carregar_metadados_questionario() -> dict[str, tuple[str, dict[str, str]]]:
    """
    Lê os enunciados e alternativas de Q006, Q007 e Q023 diretamente do Dicionário do INEP em dados/.
    Mantém descrições padrão de segurança caso o arquivo não seja encontrado.
    """
    padroes = {
        "Q006": (
            "Q006 — Você exerce ou já exerceu atividade remunerada (trabalho)?",
            {
                "A": "A — Sim",
                "B": "B — Não",
            },
        ),
        "Q007": (
            "Q007 — Qual é a renda mensal de sua família? (Somando a sua renda com a dos seus familiares)",
            {
                "A": "A — Nenhuma renda",
                "B": "B — Até 1 salário mínimo",
                "C": "C — De 1 a 1,5 salário mínimo",
                "D_G": "D a G — De 1,5 a 4 salários mínimos",
                "H_MAIS": "H ou mais — Acima de 4 salários mínimos",
            },
        ),
        "Q023": (
            "Q023 — Em que tipo de escola você frequentou o Ensino Médio?",
            {
                "A": "A — Somente em escola pública",
                "B": "B — Parte em escola pública e parte em escola privada (sem bolsa)",
                "C": "C — Parte em escola pública e parte em escola privada (com bolsa)",
                "D": "D — Somente em escola privada (sem bolsa)",
                "E": "E — Somente em escola privada (com bolsa)",
                "F": "F — Não frequentou escola / Outra situação",
            },
        ),
    }

    pasta_dados = RAIZ / "dados"
    arquivos_dic = list(pasta_dados.rglob("*DICIONARIO*.xlsx"))
    if not arquivos_dic:
        return padroes

    try:
        df_dic = pd.read_excel(arquivos_dic[0], sheet_name="PARTICIPANTES_2025")
        df_dic.columns = [str(c).strip() for c in df_dic.columns]
        col_var = df_dic.columns[0]
        letras_validas = {chr(c) for c in range(ord("A"), ord("Z") + 1)}

        for var in ["Q006", "Q007", "Q023"]:
            idx_inicio = df_dic[df_dic[col_var].astype(str).str.strip() == var].index
            if len(idx_inicio) == 0:
                continue

            inicio = idx_inicio[0]
            proximas = df_dic.loc[inicio + 1 :, col_var].dropna().index
            fim = proximas[0] if len(proximas) > 0 else len(df_dic)

            bloco = df_dic.loc[inicio : fim - 1]
            enunciado_raw = str(bloco.iloc[0, 1]).strip() if pd.notna(bloco.iloc[0, 1]) else ""
            enunciado = f"{var} — {enunciado_raw}" if enunciado_raw else padroes[var][0]

            mapa_extraido = {}
            for _, row in bloco.iterrows():
                cod = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                desc = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                if cod in letras_validas and desc:
                    mapa_extraido[cod] = f"{cod} — {desc}"

            if mapa_extraido:
                if var == "Q007":
                    mapa_extraido["D_G"] = "D a G — Faixas intermediárias (de D até G)"
                    mapa_extraido["H_MAIS"] = "H ou mais — Faixas superiores (a partir de H)"
                padroes[var] = (enunciado, mapa_extraido)
    except Exception:
        pass

    return padroes


@st.cache_data(ttl=3600)
def carregar_dados_uf() -> pd.DataFrame:
    """Consulta consolidada por UF unindo indicadores socioeconômicos (Q006, Q007, Q023) e notas."""
    engine = get_engine()
    sql = """
    WITH socio_uf AS (
        SELECT
            m.co_uf,
            m.sg_uf,
            COUNT(*) AS total_inscritos,
            -- Q006 (Trabalho)
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q006 = 'A') / COUNT(*), 2) AS pct_q006_a,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q006 = 'B') / COUNT(*), 2) AS pct_q006_b,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q006 = 'C') / COUNT(*), 2) AS pct_q006_c,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q006 = 'D') / COUNT(*), 2) AS pct_q006_d,
            -- Q007 (Renda)
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q007 = 'A') / COUNT(*), 2) AS pct_q007_a,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q007 = 'B') / COUNT(*), 2) AS pct_q007_b,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q007 = 'C') / COUNT(*), 2) AS pct_q007_c,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q007 IN ('D', 'E', 'F', 'G')) / COUNT(*), 2) AS pct_q007_d_a_g,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q007 >= 'H') / COUNT(*), 2) AS pct_q007_h_ou_mais,
            -- Q023 (Tipo de Escola no Ensino Médio)
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q023 = 'A') / COUNT(*), 2) AS pct_q023_a,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q023 = 'B') / COUNT(*), 2) AS pct_q023_b,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q023 = 'C') / COUNT(*), 2) AS pct_q023_c,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q023 = 'D') / COUNT(*), 2) AS pct_q023_d,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q023 = 'E') / COUNT(*), 2) AS pct_q023_e,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.q023 = 'F') / COUNT(*), 2) AS pct_q023_f
        FROM participantes p
        JOIN municipios m ON p.co_municipio_prova = m.co_municipio
        GROUP BY m.co_uf, m.sg_uf
    ),
    notas_uf AS (
        SELECT
            m.co_uf,
            m.sg_uf,
            COUNT(*) AS total_presentes,
            ROUND(AVG(r.nu_nota_cn), 2) AS media_cn,
            ROUND(AVG(r.nu_nota_ch), 2) AS media_ch,
            ROUND(AVG(r.nu_nota_lc), 2) AS media_lc,
            ROUND(AVG(r.nu_nota_mt), 2) AS media_mt,
            ROUND(AVG((r.nu_nota_cn + r.nu_nota_ch + r.nu_nota_lc + r.nu_nota_mt) / 4.0), 2) AS media_objetivas,
            ROUND(AVG(r.nu_nota_redacao), 2) AS media_redacao,
            ROUND(AVG((r.nu_nota_cn + r.nu_nota_ch + r.nu_nota_lc + r.nu_nota_mt + r.nu_nota_redacao) / 5.0), 2) AS media_geral
        FROM resultados r
        JOIN municipios m ON r.co_municipio_prova = m.co_municipio
        WHERE r.tp_presenca_cn = 1
          AND r.tp_presenca_ch = 1
          AND r.tp_presenca_lc = 1
          AND r.tp_presenca_mt = 1
          AND r.nu_nota_redacao IS NOT NULL
        GROUP BY m.co_uf, m.sg_uf
    )
    SELECT
        s.*,
        n.total_presentes,
        n.media_cn,
        n.media_ch,
        n.media_lc,
        n.media_mt,
        n.media_objetivas,
        n.media_redacao,
        n.media_geral
    FROM socio_uf s
    JOIN notas_uf n ON s.co_uf = n.co_uf
    ORDER BY n.media_geral DESC;
    """
    df = pd.read_sql(text(sql), engine)
    df["lat"] = df["sg_uf"].map(lambda uf: COORDENADAS_UF.get(uf, (None, None))[0])
    df["lon"] = df["sg_uf"].map(lambda uf: COORDENADAS_UF.get(uf, (None, None))[1])
    return df


def renderizar_mapa_e_dispersao(
    df: pd.DataFrame,
    col_indicador: str,
    label_indicador: str,
    col_nota: str,
    label_nota: str,
    escala_mapa: str = "Teal",
):
    """Renderiza lado a lado o Mapa de Bolhas por UF e o Gráfico de Dispersão."""
    col_mapa, col_disp = st.columns([1.15, 1])

    with col_mapa:
        func_mapa = px.scatter_map if hasattr(px, "scatter_map") else px.scatter_mapbox
        kwargs_estilo = (
            {"map_style": "carto-positron"}
            if hasattr(px, "scatter_map")
            else {"mapbox_style": "carto-positron"}
        )

        fig_mapa = func_mapa(
            df,
            lat="lat",
            lon="lon",
            size=col_indicador,
            color=col_nota,
            hover_name="sg_uf",
            hover_data={
                "lat": False,
                "lon": False,
                col_indicador: ":.2f",
                col_nota: ":.2f",
                "total_presentes": ":,",
            },
            color_continuous_scale=escala_mapa,
            size_max=34,
            zoom=3.1,
            center={"lat": -14.5, "lon": -52.0},
            labels={
                col_indicador: "Proporção (%)",
                col_nota: label_nota,
                "total_presentes": "Presentes",
            },
            title=f"Mapa por UF: Tamanho = % Categoria | Cor = {label_nota}",
            **kwargs_estilo,
        )
        fig_mapa.update_layout(margin={"r": 0, "t": 45, "l": 0, "b": 0}, height=500)
        st.plotly_chart(fig_mapa, use_container_width=True)

    with col_disp:
        fig_disp = px.scatter(
            df,
            x=col_indicador,
            y=col_nota,
            text="sg_uf",
            size="total_presentes",
            color=col_nota,
            color_continuous_scale="Blues",
            template="plotly_white",
            labels={col_indicador: label_indicador, col_nota: label_nota},
            title=f"Dispersão: {label_indicador} vs. {label_nota}",
        )
        fig_disp.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="#1E3A8A")))
        fig_disp.update_layout(height=500, coloraxis_showscale=False)
        st.plotly_chart(fig_disp, use_container_width=True)


df_uf = carregar_dados_uf()
metadados = carregar_metadados_questionario()

# --- BARRA LATERAL ---
st.sidebar.markdown("### 🎛️ Parâmetros de Análise")

ufs_disponiveis = sorted(df_uf["sg_uf"].unique())
ufs_selecionadas = st.sidebar.multiselect(
    "Unidades Federativas (UF):",
    options=ufs_disponiveis,
    default=ufs_disponiveis,
)

metricas_nota = {
    "Média Geral": "media_geral",
    "Média Provas Objetivas": "media_objetivas",
    "Redação": "media_redacao",
    "Matemática (MT)": "media_mt",
    "Ciências da Natureza (CN)": "media_cn",
    "Ciências Humanas (CH)": "media_ch",
    "Linguagens e Códigos (LC)": "media_lc",
}
label_metrica = st.sidebar.selectbox("Métrica de Desempenho:", list(metricas_nota.keys()))
col_metrica = metricas_nota[label_metrica]

st.sidebar.divider()
st.sidebar.caption("Fonte: Microdados ENEM 2025 (INEP)\nBase: PostgreSQL (`enem2025`)")

df_filtrado = df_uf[df_uf["sg_uf"].isin(ufs_selecionadas)].copy()

if df_filtrado.empty:
    st.warning("Selecione pelo menos um estado na barra lateral.")
    st.stop()

# --- CARDS DE RESUMO ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Estados Selecionados", len(df_filtrado))
col2.metric("Total de Inscritos", f"{df_filtrado['total_inscritos'].sum():,}".replace(",", "."))
col3.metric("Presentes (4 Provas)", f"{df_filtrado['total_presentes'].sum():,}".replace(",", "."))
col4.metric(f"Média ({label_metrica})", f"{df_filtrado[col_metrica].mean():.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# --- ABAS MODULARES ---
aba_geral, aba_trabalho, aba_renda_escola, aba_dados = st.tabs([
    "1. Desempenho por UF",
    "2. Trabalho (Q006)",
    "3. Renda (Q007) & Escola (Q023)",
    "4. Tabela Consolidada",
])

with aba_geral:
    st.subheader(f"Ranking por Estado — {label_metrica}")
    fig_uf = px.bar(
        df_filtrado.sort_values(col_metrica, ascending=False),
        x="sg_uf",
        y=col_metrica,
        text=col_metrica,
        color=col_metrica,
        color_continuous_scale="Blues",
        template="plotly_white",
        labels={"sg_uf": "UF", col_metrica: label_metrica},
    )
    fig_uf.update_traces(textposition="outside", marker_line_color="#1E3A8A", marker_line_width=0.8)
    fig_uf.update_layout(
        yaxis_range=[350, 700],
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(t=30, b=20, l=20, r=20),
    )
    st.plotly_chart(fig_uf, use_container_width=True)

with aba_trabalho:
    enunciado_q006, mapa_q006 = metadados["Q006"]
    st.subheader("Trabalho (Q006) e Desempenho por Estado")
    st.info(f"**Pergunta do Questionário Socioeconômico:** {enunciado_q006}")

    opcoes_q006 = {}
    for letra, col_nome in [("A", "pct_q006_a"), ("B", "pct_q006_b"), ("C", "pct_q006_c"), ("D", "pct_q006_d")]:
        if col_nome in df_filtrado.columns and df_filtrado[col_nome].sum() > 0:
            rotulo_traduzido = f"{mapa_q006.get(letra, f'Alternativa {letra}')} (%)"
            opcoes_q006[rotulo_traduzido] = col_nome

    var_q006_label = st.selectbox("Selecione a categoria de Trabalho (Q006):", list(opcoes_q006.keys()))
    col_q006 = opcoes_q006[var_q006_label]

    renderizar_mapa_e_dispersao(df_filtrado, col_q006, var_q006_label, col_metrica, label_metrica, escala_mapa="Teal")

    with st.expander("📐 Ver Matriz de Correlação de Pearson (Q006 x Desempenho)"):
        cols_corr = [c for c in opcoes_q006.values() if df_filtrado[c].std() > 0]
        corr_trab = df_filtrado[cols_corr + ["media_objetivas", "media_redacao", "media_geral"]].corr().loc[
            cols_corr, ["media_objetivas", "media_redacao", "media_geral"]
        ]
        corr_trab.index = [k for k, v in opcoes_q006.items() if v in cols_corr]
        st.dataframe(corr_trab.round(4), use_container_width=True)

with aba_renda_escola:
    st.subheader("Renda Familiar (Q007) e Escola do Ensino Médio (Q023)")

    dimensao_escolhida = st.radio(
        "Escolha o quesito socioeconômico para visualizar:",
        options=["Renda Familiar (Q007)", "Tipo de Escola no Ensino Médio (Q023)"],
        horizontal=True,
    )

    if dimensao_escolhida == "Renda Familiar (Q007)":
        enunciado_var, mapa_var = metadados["Q007"]
        pares_colunas = [
            ("A", "pct_q007_a"),
            ("B", "pct_q007_b"),
            ("C", "pct_q007_c"),
            ("D_G", "pct_q007_d_a_g"),
            ("H_MAIS", "pct_q007_h_ou_mais"),
        ]
        escala_cor = "Blues"
    else:
        enunciado_var, mapa_var = metadados["Q023"]
        pares_colunas = [
            ("A", "pct_q023_a"),
            ("B", "pct_q023_b"),
            ("C", "pct_q023_c"),
            ("D", "pct_q023_d"),
            ("E", "pct_q023_e"),
            ("F", "pct_q023_f"),
        ]
        escala_cor = "Purples"

    st.info(f"**Pergunta do Questionário Socioeconômico:** {enunciado_var}")

    opcoes_socio = {}
    for chave, col_nome in pares_colunas:
        if col_nome in df_filtrado.columns and df_filtrado[col_nome].sum() > 0:
            rotulo = f"{mapa_var.get(chave, f'Categoria {chave}')} (%)"
            opcoes_socio[rotulo] = col_nome

    var_socio_label = st.selectbox("Selecione a faixa/categoria:", list(opcoes_socio.keys()))
    col_socio = opcoes_socio[var_socio_label]

    renderizar_mapa_e_dispersao(df_filtrado, col_socio, var_socio_label, col_metrica, label_metrica, escala_mapa=escala_cor)

    with st.expander(f"📐 Ver Matriz de Correlação de Pearson ({dimensao_escolhida} x Desempenho)"):
        cols_corr_socio = [c for c in opcoes_socio.values() if df_filtrado[c].std() > 0]
        corr_socio = df_filtrado[cols_corr_socio + ["media_objetivas", "media_redacao", "media_geral"]].corr().loc[
            cols_corr_socio, ["media_objetivas", "media_redacao", "media_geral"]
        ]
        corr_socio.index = [k for k, v in opcoes_socio.items() if v in cols_corr_socio]
        st.dataframe(corr_socio.round(4), use_container_width=True)

with aba_dados:
    st.subheader("Base Consolidada por Estado")
    st.dataframe(df_filtrado.drop(columns=["lat", "lon"]), use_container_width=True, hide_index=True)
