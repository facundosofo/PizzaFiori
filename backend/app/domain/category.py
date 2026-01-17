from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.infrastructure.database import Base

class Category(Base):
    __tablename__ = "Categorias"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    descripcion = Column(String(255), nullable=True)

    productos = relationship(
        "Product",
        back_populates="categoria"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, nombre={self.nombre})>"
