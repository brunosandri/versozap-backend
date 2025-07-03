from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cria o banco de dados SQLite local
engine = create_engine("sqlite:///versozap.db", echo=True)

# Cria a sessão para manipular o banco
SessionLocal = sessionmaker(bind=engine)

# Base para os modelos
Base = declarative_base()
