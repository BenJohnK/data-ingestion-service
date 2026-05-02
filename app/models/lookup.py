from sqlalchemy import Column, Integer, String
from app.models.base import Base


class LookupBase:
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)


class StoreBrand(LookupBase, Base):
    __tablename__ = "store_brands"


class StoreType(LookupBase, Base):
    __tablename__ = "store_types"


class City(LookupBase, Base):
    __tablename__ = "cities"


class State(LookupBase, Base):
    __tablename__ = "states"


class Country(LookupBase, Base):
    __tablename__ = "countries"


class Region(LookupBase, Base):
    __tablename__ = "regions"