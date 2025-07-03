from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    telefone = Column(String, unique=True)
    versao_biblia = Column(String)
    plano_leitura = Column(String)
    tipo_ordem = Column(String)  # normal ou cronológica
    horario_envio = Column(String)

    leituras = relationship("Leitura", back_populates="usuario")

class Leitura(Base):
    __tablename__ = "leituras"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    data = Column(DateTime, default=datetime.datetime.utcnow)
    trecho = Column(String)
    concluido = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="leituras")
