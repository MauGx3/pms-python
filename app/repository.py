
import logging
from contextlib import contextmanager
from typing import Iterator, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import SessionLocal
from . import models as m
from sqlalchemy.orm import load_only

logger = logging.getLogger("pms.repository")

@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    logger.debug("Session opened")
    try:
        yield session
        session.commit()
        logger.debug("Session committed")
    except Exception as e:
        session.rollback()
        logger.debug(f"Session rolled back due to: {e}")
        raise
    finally:
        session.close()
        logger.debug("Session closed")

# Cities

def list_cities(session: Session) -> List[m.City]:
    logger.debug("Listing cities")
    cities = session.query(m.City).options(load_only(m.City.id, m.City.name, m.City.state, m.City.country)).order_by(m.City.name).all()
    for c in cities:
        session.expunge(c)
    logger.debug(f"Found {len(cities)} cities")
    return cities

def create_city(session: Session, name: str, state: Optional[str] = None, country: Optional[str] = None) -> m.City:
    logger.debug(f"Creating city: name={name}, state={state}, country={country}")
    city = m.City(name=name.strip(), state=(state or '').strip() or None, country=(country or '').strip() or None)
    session.add(city)
    session.flush()
    logger.debug(f"Created city with id={city.id}")
    return city

def update_city(session: Session, city_id: int, name: str, state: Optional[str], country: Optional[str]) -> m.City:
    logger.debug(f"Updating city id={city_id}")
    city = session.get(m.City, city_id)
    if not city:
        logger.error(f"City id={city_id} not found")
        raise ValueError("City not found")
    city.name = name.strip()
    city.state = (state or '').strip() or None
    city.country = (country or '').strip() or None
    session.flush()
    logger.debug(f"Updated city id={city_id}")
    return city

def delete_city(session: Session, city_id: int) -> None:
    logger.debug(f"Deleting city id={city_id}")
    city = session.get(m.City, city_id)
    if not city:
        logger.error(f"City id={city_id} not found")
        raise ValueError("City not found")
    session.delete(city)
    logger.debug(f"Deleted city id={city_id}")

# Neighborhoods

def list_neighborhoods(session: Session, city_id: Optional[int] = None) -> List[m.Neighborhood]:
    logger.debug(f"Listing neighborhoods for city_id={city_id}")
    q = session.query(m.Neighborhood).options(load_only(m.Neighborhood.id, m.Neighborhood.name, m.Neighborhood.city_id))
    if city_id:
        q = q.filter(m.Neighborhood.city_id == city_id)
    nbs = q.order_by(m.Neighborhood.name).all()
    for nb in nbs:
        session.expunge(nb)
    logger.debug(f"Found {len(nbs)} neighborhoods")
    return nbs

def create_neighborhood(session: Session, name: str, city_id: int) -> m.Neighborhood:
    logger.debug(f"Creating neighborhood: name={name}, city_id={city_id}")
    nb = m.Neighborhood(name=name.strip(), city_id=city_id)
    session.add(nb)
    session.flush()
    logger.debug(f"Created neighborhood id={nb.id}")
    return nb

def update_neighborhood(session: Session, nb_id: int, name: str, city_id: int) -> m.Neighborhood:
    logger.debug(f"Updating neighborhood id={nb_id}")
    nb = session.get(m.Neighborhood, nb_id)
    if not nb:
        logger.error(f"Neighborhood id={nb_id} not found")
        raise ValueError("Neighborhood not found")
    nb.name = name.strip()
    nb.city_id = city_id
    session.flush()
    logger.debug(f"Updated neighborhood id={nb_id}")
    return nb

def delete_neighborhood(session: Session, nb_id: int) -> None:
    logger.debug(f"Deleting neighborhood id={nb_id}")
    nb = session.get(m.Neighborhood, nb_id)
    if not nb:
        logger.error(f"Neighborhood id={nb_id} not found")
        raise ValueError("Neighborhood not found")
    session.delete(nb)
    logger.debug(f"Deleted neighborhood id={nb_id}")

# Streets

def list_streets(session: Session, neighborhood_id: Optional[int] = None) -> List[m.Street]:
    logger.debug(f"Listing streets for neighborhood_id={neighborhood_id}")
    q = session.query(m.Street).options(load_only(m.Street.id, m.Street.name, m.Street.neighborhood_id))
    if neighborhood_id:
        q = q.filter(m.Street.neighborhood_id == neighborhood_id)
    sts = q.order_by(m.Street.name).all()
    for st in sts:
        session.expunge(st)
    logger.debug(f"Found {len(sts)} streets")
    return sts

def create_street(session: Session, name: str, neighborhood_id: int) -> m.Street:
    logger.debug(f"Creating street: name={name}, neighborhood_id={neighborhood_id}")
    st = m.Street(name=name.strip(), neighborhood_id=neighborhood_id)
    session.add(st)
    session.flush()
    logger.debug(f"Created street id={st.id}")
    return st

def update_street(session: Session, st_id: int, name: str, neighborhood_id: int) -> m.Street:
    logger.debug(f"Updating street id={st_id}")
    st = session.get(m.Street, st_id)
    if not st:
        logger.error(f"Street id={st_id} not found")
        raise ValueError("Street not found")
    st.name = name.strip()
    st.neighborhood_id = neighborhood_id
    session.flush()
    logger.debug(f"Updated street id={st_id}")
    return st

def delete_street(session: Session, st_id: int) -> None:
    logger.debug(f"Deleting street id={st_id}")
    st = session.get(m.Street, st_id)
    if not st:
        logger.error(f"Street id={st_id} not found")
        raise ValueError("Street not found")
    session.delete(st)
    logger.debug(f"Deleted street id={st_id}")

# Police Stations

def list_police_stations(session: Session, city_id: Optional[int] = None) -> List[m.PoliceStation]:
    logger.debug(f"Listing police stations for city_id={city_id}")
    q = session.query(m.PoliceStation).options(load_only(m.PoliceStation.id, m.PoliceStation.name, m.PoliceStation.city_id, m.PoliceStation.address))
    if city_id:
        q = q.filter(m.PoliceStation.city_id == city_id)
    pss = q.order_by(m.PoliceStation.name).all()
    for ps in pss:
        session.expunge(ps)
    logger.debug(f"Found {len(pss)} police stations")
    return pss

def create_police_station(session: Session, name: str, city_id: Optional[int], address: Optional[str]) -> m.PoliceStation:
    logger.debug(f"Creating police station: name={name}, city_id={city_id}, address={address}")
    ps = m.PoliceStation(name=name.strip(), city_id=city_id, address=(address or '').strip() or None)
    session.add(ps)
    session.flush()
    logger.debug(f"Created police station id={ps.id}")
    return ps

def update_police_station(session: Session, ps_id: int, name: str, city_id: Optional[int], address: Optional[str]) -> m.PoliceStation:
    logger.debug(f"Updating police station id={ps_id}")
    ps = session.get(m.PoliceStation, ps_id)
    if not ps:
        logger.error(f"Police station id={ps_id} not found")
        raise ValueError("Police station not found")
    ps.name = name.strip()
    ps.city_id = city_id
    ps.address = (address or '').strip() or None
    session.flush()
    logger.debug(f"Updated police station id={ps_id}")
    return ps

def delete_police_station(session: Session, ps_id: int) -> None:
    logger.debug(f"Deleting police station id={ps_id}")
    ps = session.get(m.PoliceStation, ps_id)
    if not ps:
        logger.error(f"Police station id={ps_id} not found")
        raise ValueError("Police station not found")
    session.delete(ps)
    logger.debug(f"Deleted police station id={ps_id}")

class DuplicateError(Exception):
    """Raised when a unique constraint is violated."""
    pass

# Helper to wrap IntegrityError as DuplicateError for GUI-friendly messaging

def commit_with_integrity_handling(session: Session):
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        raise DuplicateError(str(e))
