from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, SessionLocal

# Crea las tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Boutique Minimalista API")

# --- CONFIGURACIÓN CORS ---
# Esto permite que una página web externa se conecte a tu catálogo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # El asterisco significa que permitimos conexión desde cualquier origen (Frontend)
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, DELETE, etc.
    allow_headers=["*"],
)

# Función esencial: Abre y cierra la sesión de la base de datos por cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"mensaje": "Bienvenido a tu Boutique Minimalista, sistema inicializado."}

# NUEVO ENDPOINT: Crear una Colección
@app.post("/colecciones/", response_model=schemas.ColeccionResponse)
def crear_coleccion(coleccion: schemas.ColeccionCreate, db: Session = Depends(get_db)):
    # 1. Preparamos los datos para la Base de Datos
    nueva_coleccion = models.Coleccion(
        nombre=coleccion.nombre, 
        descripcion=coleccion.descripcion
    )
    
    # 2. Guardamos en la Base de Datos
    db.add(nueva_coleccion)
    db.commit()                   # Confirmamos la transacción
    db.refresh(nueva_coleccion)   # Actualizamos para obtener el ID generado
    
    # 3. Devolvemos la respuesta
    return nueva_coleccion

# NUEVO ENDPOINT: Obtener TODAS las Colecciones
@app.get("/colecciones/", response_model=list[schemas.ColeccionResponse])
def obtener_colecciones(db: Session = Depends(get_db)):
    # Le pedimos a SQLAlchemy que consulte la tabla Coleccion y traiga TODO (.all())
    colecciones = db.query(models.Coleccion).all()
    return colecciones

# NUEVO ENDPOINT: Crear un Producto
@app.post("/productos/", response_model=schemas.ProductoResponse)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    nuevo_producto = models.Producto(
        nombre=producto.nombre,
        precio_base=producto.precio_base,
        coleccion_id=producto.coleccion_id
    )
    
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    
    return nuevo_producto

# NUEVO ENDPOINT: Crear una Variante (Stock físico)
@app.post("/variantes/", response_model=schemas.VarianteResponse)
def crear_variante(variante: schemas.VarianteCreate, db: Session = Depends(get_db)):
    nueva_variante = models.Variante(
        producto_id=variante.producto_id,
        talla=variante.talla,
        color=variante.color,
        stock_fisico=variante.stock_fisico,
        sku=variante.sku
    )
    
    db.add(nueva_variante)
    db.commit()
    db.refresh(nueva_variante)
    
    return nueva_variante

# NUEVO ENDPOINT: Obtener el Catálogo Completo (Árbol)
@app.get("/catalogo/", response_model=list[schemas.ColeccionCompleta])
def obtener_catalogo_completo(db: Session = Depends(get_db)):
    # Solo necesitamos pedir las colecciones, SQLAlchemy y Pydantic 
    # se encargarán de anidar los productos y variantes automáticamente.
    catalogo = db.query(models.Coleccion).all()
    return catalogo

# NUEVO ENDPOINT: Procesar Venta (Checkout)
@app.post("/ordenes/", response_model=schemas.OrdenResponse)
def crear_orden(orden_data: schemas.OrdenCreate, db: Session = Depends(get_db)):
    
    # 1. Crear la cabecera de la orden vacía
    nueva_orden = models.Orden(total=0.0)
    db.add(nueva_orden)
    db.commit() 
    db.refresh(nueva_orden)
    
    total_calculado = 0.0
    
    # 2. Procesar cada renglón del carrito de compras
    for item in orden_data.detalles:
        # A. Buscar la variante física en la DB
        variante = db.query(models.Variante).filter(models.Variante.id == item.variante_id).first()
        
        # B. Validar que la variante realmente exista
        if not variante:
            raise HTTPException(status_code=404, detail=f"La variante con ID {item.variante_id} no existe.")
            
        # C. Validar que haya stock suficiente para la compra
        if variante.stock_fisico < item.cantidad:
            raise HTTPException(
                status_code=400, 
                detail=f"Stock insuficiente para el SKU {variante.sku}. Solo hay {variante.stock_fisico} disponibles."
            )
        
        # D. Obtener el precio real desde el Producto "Maestro"
        precio_actual = variante.producto.precio_base
        
        # E. Restar el stock del almacén físico
        variante.stock_fisico -= item.cantidad
        
        # F. Crear el renglón del ticket (DetalleOrden)
        nuevo_detalle = models.DetalleOrden(
            orden_id=nueva_orden.id,
            variante_id=variante.id,
            cantidad=item.cantidad,
            precio_unitario_historico=precio_actual
        )
        db.add(nuevo_detalle)
        
        # G. Acumular el costo al total
        total_calculado += (precio_actual * item.cantidad)
        
    # 3. Actualizar el gran total y guardar todo el proceso final
    nueva_orden.total = total_calculado
    db.commit()
    db.refresh(nueva_orden)
    
    return nueva_orden

# NUEVO ENDPOINT: Actualizar estado de la orden (Confirmar pago o cancelar)
@app.post("/ordenes/{orden_id}/estado", response_model=schemas.OrdenResponse)
def actualizar_estado_orden(orden_id: int, update_data: schemas.OrdenUpdate, db: Session = Depends(get_db)):
    # 1. Buscar la orden
    orden = db.query(models.Orden).filter(models.Orden.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # 2. Lógica de negocio si se CANCELA
    if orden.estado == "Pendiente" and update_data.nuevo_estado == "Cancelado":
        for detalle in orden.detalles:
            variante = db.query(models.Variante).filter(models.Variante.id == detalle.variante_id).first()
            if variante:
                variante.stock_fisico += detalle.cantidad 
    
    # 3. Actualizar el estado y guardar
    orden.estado = update_data.nuevo_estado
    db.commit()
    db.refresh(orden)
    
    return orden

# NUEVO ENDPOINT: Eliminar una Colección
@app.delete("/colecciones/{coleccion_id}")
def eliminar_coleccion(coleccion_id: int, db: Session = Depends(get_db)):
    # 1. Buscar la colección que se desea eliminar
    coleccion = db.query(models.Coleccion).filter(models.Coleccion.id == coleccion_id).first()
    
    # 2. Validar que la colección realmente exista
    if not coleccion:
        raise HTTPException(status_code=404, detail=f"La colección con ID {coleccion_id} no fue encontrada.")
        
    # 3. Eliminar el registro de la base de datos
    db.delete(coleccion)
    db.commit() # Confirmar la transacción
    
    return {"mensaje": f"La colección con ID {coleccion_id} ha sido eliminada exitosamente."}

# NUEVO ENDPOINT: Obtener el historial de Órdenes (Backoffice)
@app.get("/ordenes/", response_model=list[schemas.OrdenResponse])
def obtener_ordenes(db: Session = Depends(get_db)):
    # Traemos todas las órdenes; SQLAlchemy anidará los detalles automáticamente
    ordenes = db.query(models.Orden).all()
    return ordenes