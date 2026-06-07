from datetime import date

from sqlalchemy import Column, Date, Integer

from app.domain.models.base import Base


class OrderDailySequence(Base):
    __tablename__ = "secuencia_pedidos"

    business_date = Column(Date, primary_key=True)
    last_value = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<OrderDailySequence(business_date={self.business_date}, last_value={self.last_value})>"
