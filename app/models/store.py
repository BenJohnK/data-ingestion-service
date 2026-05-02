from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)

    store_id = Column(String(255), unique=True, nullable=False)
    store_external_id = Column(String(255), default="")

    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)

    # Foreign Keys (Lookup Tables)
    store_brand_id = Column(Integer, ForeignKey("store_brands.id", ondelete="SET NULL"))
    store_type_id = Column(Integer, ForeignKey("store_types.id", ondelete="SET NULL"))
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="SET NULL"))
    state_id = Column(Integer, ForeignKey("states.id", ondelete="SET NULL"))
    country_id = Column(Integer, ForeignKey("countries.id", ondelete="SET NULL"))
    region_id = Column(Integer, ForeignKey("regions.id", ondelete="SET NULL"))

    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)

    is_active = Column(Boolean, default=True)

    created_on = Column(TIMESTAMP, server_default=func.now())
    modified_on = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    store_brand = relationship("StoreBrand")
    store_type = relationship("StoreType")
    city = relationship("City")
    state = relationship("State")
    country = relationship("Country")
    region = relationship("Region")