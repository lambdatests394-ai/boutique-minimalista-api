from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Coleccion(Base):
    __tablename__ = "colecciones"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    descripcion = Column(String)
    
    productos = relationship("Producto", back_populates="coleccion")

class Producto(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    precio_base = Column(Float)
    coleccion_id = Column(Integer, ForeignKey("colecciones.id"))
    
    coleccion = relationship("Coleccion", back_populates="productos")
    variaciones = relationship("Variante", back_populates="producto")

# NUEVA TABLA: Variantes (SKU)
class Variante(Base):
    __tablename__ = "variantes"
    
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id")) # Conexión al producto maestro
    talla = Column(String, index=True)
    color = Column(String, index=True)
    stock_fisico = Column(Integer, default=0)
    sku = Column(String, unique=True, index=True) # Identificador único global
    
    # Relación inversa para que la variante sepa a qué producto pertenece
    producto = relationship("Producto", back_populates="variaciones")

# NUEVA TABLA: Órdenes (El Ticket o Cabecera)
class Orden(Base):
    __tablename__ = "ordenes"
    
    id = Column(Integer, primary_key=True, index=True)
    estado = Column(String, default="Pendiente") # Estados: Pendiente, Pagado, Cancelado
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    total = Column(Float, default=0.0)
    
    # Relación: Una orden tiene muchos detalles
    detalles = relationship("DetalleOrden", back_populates="orden")

# NUEVA TABLA: Detalle de la Orden (Los renglones del ticket)
class DetalleOrden(Base):
    __tablename__ = "detalles_orden"
    
    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"))
    variante_id = Column(Integer, ForeignKey("variantes.id")) # Conexión a la variante exacta
    cantidad = Column(Integer)
    precio_unitario_historico = Column(Float) 
    
    # Relaciones
    orden = relationship("Orden", back_populates="detalles")
    variante = relationship("Variante")