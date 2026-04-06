from pydantic import BaseModel
from typing import Optional

# 1. El molde base: Lo que comparten todas las peticiones
class ColeccionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None # Optional significa que no es obligatorio

# 2. El molde para CREAR (Lo que envía el cliente)
class ColeccionCreate(ColeccionBase):
    pass # Hereda todo de ColeccionBase sin cambios

# 3. El molde de RESPUESTA (Lo que la API devuelve, incluyendo el ID que genera la Base de Datos)
class ColeccionResponse(ColeccionBase):
    id: int

    class Config:
        from_attributes = True # Esto le permite a Pydantic leer los datos de SQLAlchemy

# --- ESQUEMAS PARA PRODUCTOS ---

class ProductoBase(BaseModel):
    nombre: str
    precio_base: float
    coleccion_id: int # ¡Esta es la clave que lo conecta con la colección!

class ProductoCreate(ProductoBase):
    pass

class ProductoResponse(ProductoBase):
    id: int

    class Config:
        from_attributes = True

# --- ESQUEMAS PARA VARIANTES (TALLA/COLOR) ---

class VarianteBase(BaseModel):
    talla: str
    color: str
    stock_fisico: int
    sku: str
    producto_id: int # La llave que lo une a la Camisa, Pantalón, etc.

class VarianteCreate(VarianteBase):
    pass

class VarianteResponse(VarianteBase):
    id: int

    class Config:
        from_attributes = True

# --- ESQUEMAS PARA EL ÁRBOL DEL CATÁLOGO (DATOS ANIDADOS) ---

# 1. Un Producto que incluye su lista de Variantes
class ProductoCompleto(ProductoResponse):
    variaciones: list[VarianteResponse] = []

# 2. Una Colección que incluye su lista de Productos Completos
class ColeccionCompleta(ColeccionResponse):
    productos: list[ProductoCompleto] = []

from datetime import datetime

# --- ESQUEMAS PARA VENTAS (ORDENES) ---

# 1. El renglón del carrito (Lo que el cliente envía)
class DetalleOrdenCreate(BaseModel):
    variante_id: int
    cantidad: int

# 2. La cabecera de la orden (La lista de artículos)
class OrdenCreate(BaseModel):
    detalles: list[DetalleOrdenCreate]

# 3. Respuesta del detalle (Lo que mostramos en el ticket)
class DetalleOrdenResponse(BaseModel):
    id: int
    variante_id: int
    cantidad: int
    precio_unitario_historico: float

    class Config:
        from_attributes = True

# 4. Respuesta de la Orden completa
class OrdenResponse(BaseModel):
    id: int
    estado: str
    fecha_creacion: datetime
    total: float
    detalles: list[DetalleOrdenResponse]

    class Config:
        from_attributes = True

# Esquema para actualizar solo el estado
class OrdenUpdate(BaseModel):
    nuevo_estado: str # "Pagado" o "Cancelado"