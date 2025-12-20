from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Importar conexión PostgreSQL
from ..database import get_db

router = APIRouter()
load_dotenv()

# =========================
# MODELOS PYDANTIC
# =========================

class LoginRequest(BaseModel):
    email: str  # Puede ser email O username
    password: str

class RegisterRequest(BaseModel):
    nombre_completo: str
    email: str
    telefono: str = None
    username: str
    password: str
    rol: str = "repartidor"  # Default: repartidor

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    nombre_completo: str
    email: str
    rol: str
    username: str

class UserResponse(BaseModel):
    id: int
    nombre_completo: str
    email: str
    username: str
    telefono: str = None
    rol: str
    activo: bool
    fecha_registro: datetime

# =========================
# CONFIGURACIÓN JWT
# =========================

SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura_aqui_123")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def create_access_token(data: dict):
    """Crea token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# =========================
# ENDPOINTS DE AUTENTICACIÓN
# =========================

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login de usuario (admin o repartidor)
    - Acepta email O username
    - Verifica credenciales
    - Genera token JWT
    - Actualiza último login
    """
    try:
        # MODIFICADO: Buscar por email O username
        query = text("""
            SELECT id, nombre_completo, email, username, telefono, 
                   password_hash, rol, activo
            FROM usuarios 
            WHERE (email = :identifier OR username = :identifier) 
            AND activo = TRUE
        """)
        
        result = db.execute(query, {"identifier": request.email})
        user = result.fetchone()
        
        if not user:
            print(f"❌ Usuario no encontrado: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas o usuario inactivo"
            )
        
        # Verificar contraseña
        if user.password_hash != request.password:
            print(f"❌ Contraseña incorrecta para: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )
        
        print(f"✅ Login exitoso: {user.email} - Rol: {user.rol}")
        
        # Actualizar último login
        update_query = text("""
            UPDATE usuarios 
            SET ultimo_login = CURRENT_TIMESTAMP 
            WHERE id = :id
        """)
        db.execute(update_query, {"id": user.id})
        db.commit()
        
        # Crear token JWT
        token_data = {
            "sub": user.email,
            "user_id": user.id,
            "rol": user.rol,
            "username": user.username
        }
        
        access_token = create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            nombre_completo=user.nombre_completo,
            email=user.email,
            rol=user.rol,
            username=user.username
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(e)}"
        )

@router.post("/register", response_model=UserResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registro de nuevo usuario
    - Valida que el email y username sean únicos
    - Crea usuario con rol especificado
    """
    try:
        print(f"📝 Intento de registro: {request.email} - Usuario: {request.username}")
        
        # Verificar si email ya existe
        check_email = text("SELECT id FROM usuarios WHERE email = :email")
        email_exists = db.execute(check_email, {"email": request.email}).fetchone()
        
        if email_exists:
            print(f"⚠️  Email ya existe: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Verificar si username ya existe
        check_username = text("SELECT id FROM usuarios WHERE username = :username")
        username_exists = db.execute(check_username, {"username": request.username}).fetchone()
        
        if username_exists:
            print(f"⚠️  Username ya existe: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso"
            )
        
        # Validar rol
        if request.rol not in ["admin", "repartidor"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rol no válido. Use 'admin' o 'repartidor'"
            )
        
        # Insertar nuevo usuario
        insert_query = text("""
            INSERT INTO usuarios 
            (nombre_completo, email, telefono, username, password_hash, rol)
            VALUES (:nombre, :email, :telefono, :username, :password, :rol)
            RETURNING id, nombre_completo, email, username, telefono, rol, 
                     activo, fecha_registro
        """)
        
        result = db.execute(insert_query, {
            "nombre": request.nombre_completo,
            "email": request.email,
            "telefono": request.telefono,
            "username": request.username,
            "password": request.password,  # ⚠️ En producción: hash esta contraseña
            "rol": request.rol
        })
        
        new_user = result.fetchone()
        db.commit()
        
        print(f"✅ Usuario registrado exitosamente: {new_user.email}")
        
        return UserResponse(
            id=new_user.id,
            nombre_completo=new_user.nombre_completo,
            email=new_user.email,
            username=new_user.username,
            telefono=new_user.telefono,
            rol=new_user.rol,
            activo=new_user.activo,
            fecha_registro=new_user.fecha_registro
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error en registro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
def get_current_user(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene información del usuario actual mediante token
    """
    try:
        # Decodificar token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        # Buscar usuario
        query = text("""
            SELECT id, nombre_completo, email, username, telefono, 
                   rol, activo, fecha_registro, ultimo_login
            FROM usuarios 
            WHERE email = :email AND activo = TRUE
        """)
        
        result = db.execute(query, {"email": email})
        user = result.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return UserResponse(
            id=user.id,
            nombre_completo=user.nombre_completo,
            email=user.email,
            username=user.username,
            telefono=user.telefono,
            rol=user.rol,
            activo=user.activo,
            fecha_registro=user.fecha_registro
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado o inválido"
        )

@router.get("/repartidores")
def get_repartidores(db: Session = Depends(get_db)):
    """
    Obtiene lista de repartidores activos
    (Para que admin pueda asignar en formulario 2)
    """
    try:
        query = text("""
            SELECT id, nombre_completo, email, username, telefono
            FROM usuarios 
            WHERE rol = 'repartidor' AND activo = TRUE
            ORDER BY nombre_completo
        """)
        
        result = db.execute(query)
        repartidores = result.fetchall()
        
        return {
            "total": len(repartidores),
            "repartidores": [
                {
                    "id": r.id,
                    "nombre_completo": r.nombre_completo,
                    "email": r.email,
                    "username": r.username,
                    "telefono": r.telefono
                } for r in repartidores
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener repartidores: {str(e)}"
        )

@router.post("/logout")
def logout(token: str = None):
    """
    Logout simbólico (en JWT stateless, el cliente debe eliminar el token)
    """
    return {
        "message": "Logout exitoso. Elimine el token del cliente.",
        "timestamp": datetime.now().isoformat()
    }