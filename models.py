from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    telefone = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    versao_biblia = Column(String, default="ARC")
    plano_leitura = Column(String, default="cronologico")
    tipo_ordem = Column(String, default="normal")  # normal ou cronológica
    horario_envio = Column(String, default="08:00")
    data_cadastro = Column(DateTime, default=datetime.datetime.utcnow)

    leituras = relationship("Leitura", back_populates="usuario")

class Leitura(Base):
    __tablename__ = "leituras"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    data = Column(DateTime, default=datetime.datetime.utcnow)
    trecho = Column(String)
    concluido = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="leituras")
