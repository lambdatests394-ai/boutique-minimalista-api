import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Leemos la URL secreta de Render. Si no existe (en tu computadora local), usamos SQLite.
URL_BASE_DATOS = os.getenv("DATABASE_URL", "sqlite:///./boutique.db")

# SQLite necesita un permiso especial, PostgreSQL no.
if URL_BASE_DATOS.startswith("sqlite"):
    engine = create_engine(URL_BASE_DATOS, connect_args={"check_same_thread": False})
else:
    # Corrección de seguridad para algunas nubes
    if URL_BASE_DATOS.startswith("postgres://"):
        URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)
    engine = create_engine(URL_BASE_DATOS)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()