import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Initialize SQLAlchemy
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///mock_db.sqlite')
# Railway postgres urls start with postgres://, but sqlalchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class CosteoModel(Base):
    __tablename__ = "costeos"

    id = Column(String, primary_key=True, index=True)
    nombre_costeo = Column(String, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    configuracion = Column(JSON)
    categoria = Column(String)
    mpd = Column(JSON)
    empaque = Column(JSON)
    cmod = Column(JSON)
    cif = Column(JSON)
    parametros_financieros = Column(JSON)
    resultados = Column(JSON)
    proformas = Column(JSON, default=list)

# Create tables
Base.metadata.create_all(bind=engine)

class CosteosDB:
    @staticmethod
    def save_costeo(costeo_data: dict, doc_id: str = None) -> str:
        """
        Guarda o actualiza un documento de costeo en PostgreSQL.
        """
        db = SessionLocal()
        try:
            if not doc_id:
                # generate a simple ID if none provided
                doc_id = f"doc_{int(datetime.now().timestamp() * 1000)}"

            # Check if it exists
            existing = db.query(CosteoModel).filter(CosteoModel.id == doc_id).first()

            if existing:
                existing.nombre_costeo = costeo_data.get('nombre_costeo', existing.nombre_costeo)
                existing.fecha_actualizacion = datetime.utcnow()
                existing.configuracion = costeo_data.get('configuracion', existing.configuracion)
                existing.categoria = costeo_data.get('categoria', existing.categoria)
                existing.mpd = costeo_data.get('mpd', existing.mpd)
                existing.empaque = costeo_data.get('empaque', existing.empaque)
                existing.cmod = costeo_data.get('cmod', existing.cmod)
                existing.cif = costeo_data.get('cif', existing.cif)
                existing.parametros_financieros = costeo_data.get('parametros_financieros', existing.parametros_financieros)
                existing.resultados = costeo_data.get('resultados', existing.resultados)
                if 'proformas' in costeo_data:
                    existing.proformas = costeo_data['proformas']
            else:
                new_costeo = CosteoModel(
                    id=doc_id,
                    nombre_costeo=costeo_data.get('nombre_costeo', ''),
                    configuracion=costeo_data.get('configuracion', {}),
                    categoria=costeo_data.get('categoria', ''),
                    mpd=costeo_data.get('mpd', []),
                    empaque=costeo_data.get('empaque', []),
                    cmod=costeo_data.get('cmod', []),
                    cif=costeo_data.get('cif', []),
                    parametros_financieros=costeo_data.get('parametros_financieros', {}),
                    resultados=costeo_data.get('resultados', {}),
                    proformas=costeo_data.get('proformas', [])
                )
                db.add(new_costeo)

            db.commit()
            return doc_id
        finally:
            db.close()

    @staticmethod
    def get_all_costeos() -> list:
        """
        Recupera todos los documentos de costeo guardados.
        """
        db = SessionLocal()
        try:
            costeos_records = db.query(CosteoModel).all()
            costeos_list = []
            for record in costeos_records:
                costeo_dict = {
                    "id": record.id,
                    "nombre_costeo": record.nombre_costeo,
                    "fecha_creacion": record.fecha_creacion.isoformat() if record.fecha_creacion else None,
                    "fecha_actualizacion": record.fecha_actualizacion.isoformat() if record.fecha_actualizacion else None,
                    "configuracion": record.configuracion,
                    "categoria": record.categoria,
                    "mpd": record.mpd,
                    "empaque": record.empaque,
                    "cmod": record.cmod,
                    "cif": record.cif,
                    "parametros_financieros": record.parametros_financieros,
                    "resultados": record.resultados,
                    "proformas": record.proformas
                }
                costeos_list.append(costeo_dict)
            return costeos_list
        finally:
            db.close()
