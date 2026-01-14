from sqlalchemy import Column, Integer, String
from app.infrastructure.database import Base

class Categoria(Base):
    __tablename__ = "Categorias"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    descripcion = Column(String(255), nullable=True)