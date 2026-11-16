import io
import time
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

def copiar_dataframe_para_postgres(df: pd.DataFrame, nome_tabela: str, colunas: list[str], raw_conn):
    """Envia um DataFrame diretamente para o PostgreSQL via comando COPY FROM STDIN."""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, sep="\t", na_rep="")
    buffer.seek(0)

    cols_sql = ", ".join(colunas)
    sql_copy = f"COPY {nome_tabela} ({cols_sql}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '');"

    with raw_conn.cursor() as cur:
        cur.copy_expert(sql_copy, buffer)

def carregar_participantes(engine, chunksize: int = 250_000):
    caminho_csv = localizar_arquivo("PARTICIPANTES_2025.csv")

    colunas_csv = [
        "NU_INSCRICAO", "NU_ANO", "TP_FAIXA_ETARIA", "TP_SEXO", "TP_ESTADO_CIVIL",
        "TP_COR_RACA", "TP_NACIONALIDADE", "TP_ST_CONCLUSAO", "TP_ANO_CONCLUIU",
        "TP_ENSINO", "IN_TREINEIRO", "CO_MUNICIPIO_PROVA",
        "Q001", "Q002", "Q003", "Q004", "Q005", "Q006", "Q007", "Q008",
        "Q009", "Q010", "Q011", "Q012", "Q013", "Q014", "Q015", "Q016",
        "Q017", "Q018", "Q019", "Q020", "Q021", "Q022", "Q023"
    ]
    colunas_db = [c.lower() for c in colunas_csv]

    cols_inteiras = [
        "NU_INSCRICAO", "NU_ANO", "TP_FAIXA_ETARIA", "TP_ESTADO_CIVIL",
        "TP_COR_RACA", "TP_NACIONALIDADE", "TP_ST_CONCLUSAO", "TP_ANO_CONCLUIU",
        "TP_ENSINO", "IN_TREINEIRO", "CO_MUNICIPIO_PROVA", "Q005"
    ]

    print("Iniciando carga de PARTICIPANTES_2025.csv...")
    inicio = time.time()
    total_linhas = 0

    raw_conn = engine.raw_connection()
    try:
        for i, chunk in enumerate(
            pd.read_csv(caminho_csv, sep=";", encoding="latin1", usecols=colunas_csv, chunksize=chunksize),
            start=1
        ):
            # Garante a ordem exata das colunas
            chunk = chunk[colunas_csv]

            # Converte colunas inteiras para Int64 (evita ".0" em campos com nulos)
            for col in cols_inteiras:
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce").astype("Int64")

            copiar_dataframe_para_postgres(chunk, "participantes", colunas_db, raw_conn)
            raw_conn.commit()

            total_linhas += len(chunk)
            print(f"  [participantes] Lote {i:02d} concluído — {total_linhas:,} linhas inseridas ({time.time() - inicio:.1f}s)")
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()

    print(f"Carga de 'participantes' finalizada: {total_linhas:,} registros em {time.time() - inicio:.1f}s.\n")

def carregar_resultados(engine, chunksize: int = 250_000):
    caminho_csv = localizar_arquivo("RESULTADOS_2025.csv")

    # Apenas as colunas selecionadas na modelagem enxuta
    colunas_csv = [
        "NU_SEQUENCIAL", "NU_ANO", "CO_ESCOLA", "CO_MUNICIPIO_PROVA",
        "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
        "TP_LINGUA",
        "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT",
        "TP_STATUS_REDACAO", "NU_NOTA_REDACAO"
    ]
    colunas_db = [c.lower() for c in colunas_csv]

    cols_inteiras = [
        "NU_SEQUENCIAL", "NU_ANO", "CO_ESCOLA", "CO_MUNICIPIO_PROVA",
        "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
        "TP_LINGUA", "TP_STATUS_REDACAO"
    ]
    cols_notas = [
        "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"
    ]

    print("Iniciando carga de RESULTADOS_2025.csv...")
    inicio = time.time()
    total_linhas = 0

    raw_conn = engine.raw_connection()
    try:
        for i, chunk in enumerate(
            pd.read_csv(caminho_csv, sep=";", encoding="latin1", usecols=colunas_csv, chunksize=chunksize),
            start=1
        ):
            chunk = chunk[colunas_csv]

            for col in cols_inteiras:
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce").astype("Int64")

            for col in cols_notas:
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

            copiar_dataframe_para_postgres(chunk, "resultados", colunas_db, raw_conn)
            raw_conn.commit()

            total_linhas += len(chunk)
            print(f"  [resultados] Lote {i:02d} concluído — {total_linhas:,} linhas inseridas ({time.time() - inicio:.1f}s)")
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()

    print(f"Carga de 'resultados' finalizada: {total_linhas:,} registros em {time.time() - inicio:.1f}s.\n")

if __name__ == "__main__":
    engine = get_engine()

    # Garante que as dimensões já foram populadas antes de carregar as tabelas fato
    with engine.connect() as conn:
        qtd_mun = conn.execute(text("SELECT COUNT(*) FROM municipios;")).scalar()
        if qtd_mun == 0:
            raise RuntimeError("A tabela 'municipios' está vazia! Execute 'python src/etl_dimensoes.py' primeiro.")

    carregar_participantes(engine)
    carregar_resultados(engine)
    print("Pipeline ETL completo executado com sucesso!")