from __future__ import annotations
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from .db import Base

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    state = Column(String(2), nullable=True)  # Optional: 2-letter state code
    country = Column(String(2), nullable=True)  # Optional: ISO country code

    neighborhoods = relationship("Neighborhood", back_populates="city", cascade="all, delete-orphan")
    police_stations = relationship("PoliceStation", back_populates="city", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("name", "state", "country", name="uq_city_name_state_country"),
        Index("ix_city_name", "name"),
    )

class Neighborhood(Base):
    __tablename__ = "neighborhoods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)

    city = relationship("City", back_populates="neighborhoods")
    streets = relationship("Street", back_populates="neighborhood", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("name", "city_id", name="uq_neighborhood_name_city"),
        Index("ix_neighborhood_name", "name"),
    )

class Street(Base):
    __tablename__ = "streets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id", ondelete="CASCADE"), nullable=False)

    neighborhood = relationship("Neighborhood", back_populates="streets")

    __table_args__ = (
        UniqueConstraint("name", "neighborhood_id", name="uq_street_name_neighborhood"),
        Index("ix_street_name", "name"),
    )

class PoliceStation(Base):
    __tablename__ = "police_stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="SET NULL"), nullable=True)
    address = Column(String(255), nullable=True)

    city = relationship("City", back_populates="police_stations")

    __table_args__ = (
        UniqueConstraint("name", "city_id", name="uq_police_station_name_city"),
        Index("ix_police_station_name", "name"),
    )
