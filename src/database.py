import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Localiza e carrega o arquivo .env da raiz do projeto
raiz_projeto = Path(__file__).resolve().parent.parent
load_dotenv(raiz_projeto / ".env")

def get_engine():
    """Cria e retorna uma engine do SQLAlchemy conectada ao PostgreSQL."""
    url_conexao = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url_conexao)

def testar_conexao():
    """Testa a conexão e lista as tabelas existentes no schema public."""
    engine = get_engine()
    with engine.connect() as conn:
        versao = conn.execute(text("SELECT version();")).scalar()
        tabelas = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)).scalars().all()
        
    print("Conexão bem-sucedida!")
    print(f"Servidor: {versao.split(',')[0]}")
    print(f"Tabelas encontradas no banco '{os.getenv('DB_NAME')}': {tabelas}")

if __name__ == "__main__":
    testar_conexao()
