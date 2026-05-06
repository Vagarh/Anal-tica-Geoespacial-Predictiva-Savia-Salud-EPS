"""Test de conectividad BD y volumen de datos para extracción v5."""
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path("d:/Users/jcardonr/Documents/Savia/.env"))
import mysql.connector

try:
    conn = mysql.connector.connect(
        host=os.environ["SAVIA_DB_HOST"],
        database=os.environ["SAVIA_DB_NAME"],
        user=os.environ["SAVIA_DB_USER"],
        password=os.environ["SAVIA_DB_PASSWORD"],
        connect_timeout=10,
    )
    print("Conexion OK:", os.environ["SAVIA_DB_HOST"])

    cur = conn.cursor()

    # Volumen 6 meses maduros
    cur.execute("""
        SELECT COUNT(*)
        FROM cm_facturas
        WHERE fecha_radicacion >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
          AND fecha_radicacion <= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    print("Facturas 6m maduros:", cur.fetchone()[0])

    # Verificar codigo_dx en cm_detalles
    cur.execute("""
        SELECT COUNT(*), SUM(CASE WHEN codigo_dx IS NOT NULL AND codigo_dx != '' THEN 1 ELSE 0 END)
        FROM cm_detalles
        LIMIT 1
    """)
    row = cur.fetchone()
    print("Total detalles:", row[0], " | Con codigo_dx:", row[1])

    # Sample de codigo_dx
    cur.execute("""
        SELECT codigo_dx, COUNT(*) AS n
        FROM cm_detalles
        WHERE codigo_dx IS NOT NULL AND codigo_dx != ''
        GROUP BY codigo_dx
        ORDER BY n DESC
        LIMIT 5
    """)
    print("Top 5 codigo_dx:")
    for r in cur.fetchall():
        print(" ", r)

    conn.close()
    print("Test completo OK")

except Exception as e:
    print("ERROR:", e)
