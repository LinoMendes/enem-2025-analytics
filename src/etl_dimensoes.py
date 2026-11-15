from pathlib import Path
import pandas as pd
from sqlalchemy import text
from database import get_engine

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados"

def localizar_arquivo(nome_arquivo: str) -> Path:
    arquivos = list(PASTA_DADOS.rglob(nome_arquivo))
    if not arquivos:
        raise FileNotFoundError(f"Arquivo {nome_arquivo} não encontrado em {PASTA_DADOS}")
    return arquivos[0]

def extrair_dimensoes():
    caminho_part = localizar_arquivo("PARTICIPANTES_2025.csv")
    caminho_res = localizar_arquivo("RESULTADOS_2025.csv")

    municipios_dict = {}
    escolas_dict = {}

    print("1/3 - Lendo municípios de prova em PARTICIPANTES_2025.csv...")
    cols_part = ["CO_MUNICIPIO_PROVA", "NO_MUNICIPIO_PROVA", "CO_UF_PROVA", "SG_UF_PROVA"]
    for chunk in pd.read_csv(caminho_part, sep=";", encoding="latin1", usecols=cols_part, chunksize=200_000):
        unicos = chunk.dropna(subset=["CO_MUNICIPIO_PROVA"]).drop_duplicates(subset=["CO_MUNICIPIO_PROVA"])
        for row in unicos.itertuples(index=False):
            co_mun = int(row.CO_MUNICIPIO_PROVA)
            if co_mun not in municipios_dict:
                municipios_dict[co_mun] = (
                    co_mun,
                    str(row.NO_MUNICIPIO_PROVA).strip(),
                    int(row.CO_UF_PROVA),
                    str(row.SG_UF_PROVA).strip(),
                )

    print("2/3 - Lendo municípios e escolas em RESULTADOS_2025.csv...")
    cols_res = [
        "CO_MUNICIPIO_PROVA", "NO_MUNICIPIO_PROVA", "CO_UF_PROVA", "SG_UF_PROVA",
        "CO_ESCOLA", "CO_MUNICIPIO_ESC", "NO_MUNICIPIO_ESC", "CO_UF_ESC", "SG_UF_ESC",
        "TP_DEPENDENCIA_ADM_ESC", "TP_LOCALIZACAO_ESC", "TP_SIT_FUNC_ESC"
    ]
    for chunk in pd.read_csv(caminho_res, sep=";", encoding="latin1", usecols=cols_res, chunksize=200_000):
        # Municípios de prova
        mun_prova = chunk.dropna(subset=["CO_MUNICIPIO_PROVA"]).drop_duplicates(subset=["CO_MUNICIPIO_PROVA"])
        for row in mun_prova.itertuples(index=False):
            co_mun = int(row.CO_MUNICIPIO_PROVA)
            if co_mun not in municipios_dict:
                municipios_dict[co_mun] = (
                    co_mun,
                    str(row.NO_MUNICIPIO_PROVA).strip(),
                    int(row.CO_UF_PROVA),
                    str(row.SG_UF_PROVA).strip(),
                )

        # Municípios das escolas
        mun_esc = chunk.dropna(subset=["CO_MUNICIPIO_ESC"]).drop_duplicates(subset=["CO_MUNICIPIO_ESC"])
        for row in mun_esc.itertuples(index=False):
            co_mun = int(row.CO_MUNICIPIO_ESC)
            if co_mun not in municipios_dict:
                municipios_dict[co_mun] = (
                    co_mun,
                    str(row.NO_MUNICIPIO_ESC).strip(),
                    int(row.CO_UF_ESC),
                    str(row.SG_UF_ESC).strip(),
                )

        # Escolas únicas
        esc = chunk.dropna(subset=["CO_ESCOLA"]).drop_duplicates(subset=["CO_ESCOLA"])
        for row in esc.itertuples(index=False):
            co_esc = int(row.CO_ESCOLA)
            if co_esc not in escolas_dict:
                escolas_dict[co_esc] = (
                    co_esc,
                    int(row.CO_MUNICIPIO_ESC) if pd.notna(row.CO_MUNICIPIO_ESC) else None,
                    int(row.TP_DEPENDENCIA_ADM_ESC) if pd.notna(row.TP_DEPENDENCIA_ADM_ESC) else None,
                    int(row.TP_LOCALIZACAO_ESC) if pd.notna(row.TP_LOCALIZACAO_ESC) else None,
                    int(row.TP_SIT_FUNC_ESC) if pd.notna(row.TP_SIT_FUNC_ESC) else None,
                )

    df_municipios = pd.DataFrame(
        list(municipios_dict.values()),
        columns=["co_municipio", "no_municipio", "co_uf", "sg_uf"]
    )
    df_escolas = pd.DataFrame(
        list(escolas_dict.values()),
        columns=["co_escola", "co_municipio_esc", "tp_dependencia_adm_esc", "tp_localizacao_esc", "tp_sit_func_esc"]
    )

    print(f"Total de municípios únicos extraídos: {len(df_municipios)}")
    print(f"Total de escolas únicas extraídas: {len(df_escolas)}")

    return df_municipios, df_escolas

def carregar_dimensoes():
    df_municipios, df_escolas = extrair_dimensoes()
    engine = get_engine()

    print("3/3 - Inserindo dimensões no PostgreSQL...")
    with engine.begin() as conn:
        # Inserir municípios com ON CONFLICT DO NOTHING
        sql_mun = text("""
            INSERT INTO municipios (co_municipio, no_municipio, co_uf, sg_uf)
            VALUES (:co_municipio, :no_municipio, :co_uf, :sg_uf)
            ON CONFLICT (co_municipio) DO NOTHING;
        """)
        conn.execute(sql_mun, df_municipios.to_dict(orient="records"))

        # Inserir escolas com ON CONFLICT DO NOTHING
        sql_esc = text("""
            INSERT INTO escolas (co_escola, co_municipio_esc, tp_dependencia_adm_esc, tp_localizacao_esc, tp_sit_func_esc)
            VALUES (:co_escola, :co_municipio_esc, :tp_dependencia_adm_esc, :tp_localizacao_esc, :tp_sit_func_esc)
            ON CONFLICT (co_escola) DO NOTHING;
        """)
        conn.execute(sql_esc, df_escolas.to_dict(orient="records"))

    print("Carga das tabelas dimensionais concluída com sucesso!")

if __name__ == "__main__":
    carregar_dimensoes()