#!/usr/bin/env python3
"""
Script para probar la conexión a Neon PostgreSQL
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 60)
print("🧪 TEST DE CONEXIÓN A NEON POSTGRESQL")
print("=" * 60)

if not DATABASE_URL:
    print("❌ ERROR: No se encontró DATABASE_URL en .env")
    exit(1)

# Ocultar password en el log
safe_url = DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL
print(f"📡 Conectando a: ...@{safe_url}")
print()

try:
    print("🔄 Intentando conectar...")
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ ¡Conexión exitosa!")
    print()
    
    cursor = conn.cursor()
    
    # Version de PostgreSQL
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"📊 PostgreSQL Version:")
    print(f"   {version[:80]}...")
    print()
    
    # Contar usuarios
    try:
        cursor.execute("SELECT COUNT(*) FROM usuarios;")
        count = cursor.fetchone()[0]
        print(f"👥 Total usuarios en BD: {count}")
        
        # Listar usuarios
        cursor.execute("""
            SELECT id, nombre_completo, email, rol 
            FROM usuarios 
            ORDER BY id 
            LIMIT 5
        """)
        users = cursor.fetchall()
        print("\n📋 Usuarios registrados:")
        for user in users:
            print(f"   ID: {user[0]} | {user[1]} | {user[2]} | Rol: {user[3]}")
    except Exception as e:
        print(f"⚠️  No se pudo consultar tabla usuarios: {e}")
    
    print()
    
    # Listar todas las tablas
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    tables = cursor.fetchall()
    print(f"🗂️  Tablas disponibles ({len(tables)}):")
    for table in tables:
        print(f"   - {table[0]}")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 60)
    print("✅ TODO FUNCIONA CORRECTAMENTE")
    print("=" * 60)
    print()
    print("💡 Ahora intenta iniciar tu API:")
    print("   python scripts/start_backend.py")
    
except psycopg2.OperationalError as e:
    print("❌ ERROR DE CONEXIÓN")
    print(f"   {str(e)[:200]}")
    print()
    print("=" * 60)
    print("🔧 SOLUCIONES POSIBLES:")
    print("=" * 60)
    print()
    print("1. Verifica que tu proyecto Neon esté ACTIVO")
    print("   https://console.neon.tech")
    print()
    print("2. Cambia sslmode en tu .env:")
    print("   De: sslmode=require")
    print("   A:  sslmode=prefer")
    print()
    print("3. Copia la Connection String directamente desde Neon:")
    print("   Dashboard > Connection Details > Copy")
    print()
    print("4. Instala/actualiza psycopg2:")
    print("   pip install psycopg2-binary --upgrade")
    
except Exception as e:
    print(f"❌ ERROR INESPERADO: {e}")
    print()
    print("💡 Verifica tu archivo .env y la URL de conexión")

print()