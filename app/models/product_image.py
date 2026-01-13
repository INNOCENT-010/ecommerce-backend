from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class ProductImage(Base):
    __tablename__ = "product-images"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    filepath = Column(String, nullable=False)

