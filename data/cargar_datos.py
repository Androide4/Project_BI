"""
bulk_insert_1000.py

Script para generar e insertar 1000 registros en cada tabla del esquema `mydb`.
Genera datos con las siguientes características:
 1. Valores NULL (~10%) en columnas seleccionadas (si tiene privilegios ALTER).
 2. Valores repetidos (alta repetición en campos seleccionados).
 3. Campos con poca varianza (por ejemplo, la mayoría comparten un mismo valor).
 4. Campos no categorizados (texto aleatorio libre).

Genera exactamente 1000 filas en cada tabla: sede, docente, clase, matricula, alumno,
clase_has_sede (intentos hasta llenar o hasta que ya no haya combinaciones nuevas),
pago (1000 registros) y asistencia (1000 registros).

Notas importantes:
 - El script intenta ejecutar ALTER TABLE para permitir NULLs y ajustar DECIMAL. Requiere
   privilegios ALTER. Si no tienes permisos, el script continuará sin alterar y
   generará datos sin NULLs en esas columnas.
 - Se respeta la integridad referencial: se insertan sedes/docentes/clases/matriculas/alumnos
   primero, y luego pagos/asistencias.
 - Para mejorar rendimiento se hace commit cada bloque de inserciones.

Requisitos:
    pip install mysql-connector-python

Ejecución:
    python bulk_insert_1000.py

"""

import random
import string
from datetime import datetime, timedelta
import getpass
import mysql.connector # type: ignore
from mysql.connector import Error # type: ignore
from decimal import Decimal

# ---------- Config (se piden al ejecutar) ----------
user = input("Usuario MySQL (ej. root): ").strip() or "root"
password = getpass.getpass("Contraseña MySQL: ")
host = input("Host (por defecto 'localhost'): ").strip() or "localhost"
port_input = input("Puerto (por defecto 3306): ").strip() or "3306"
port = int(port_input)
database = input("Base de datos (por defecto 'mydb'): ").strip() or "mydb"

# ---------- Parámetros de generación ----------
N = 1000  # registros objetivo por tabla
NULL_RATIO = 0.10  # ~10% valores nulos donde se permite
LOW_VARIANCE_RATIO = 0.70  # 70% usan el mismo valor en columnas de baja varianza
BATCH = 200  # commits cada BATCH inserciones para no saturar

# ---------- Helpers ----------

def rand_text(min_len=5, max_len=25):
    l = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_letters + ' ', k=l)).strip()


def maybe_null(value):
    return None if random.random() < NULL_RATIO else value


def random_date(start_days_ago=365*2, end_days_ago=0):
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    return start + (end - start) * random.random()

# ---------- Conexión ----------
config = {
    'user': user,
    'password': password,
    'host': host,
    'port': port,
    'database': database,
    'raise_on_warnings': True
}

conn = None
cursor = None

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    print("Conectado a MySQL correctamente."
          f"\nInsertando {N} registros por tabla. Esto puede tardar unos minutos...")

    # Intentar cambiar esquema para aceptar NULLs y decimal
    alters = [
        "ALTER TABLE sede MODIFY nombre_sede VARCHAR(100) NULL",
        "ALTER TABLE sede MODIFY ubicacion VARCHAR(45) NULL",
        "ALTER TABLE docente MODIFY nombre_docente VARCHAR(45) NULL",
        "ALTER TABLE clase MODIFY nombre_clase VARCHAR(45) NULL",
        "ALTER TABLE alumno MODIFY nombre_alumno VARCHAR(45) NULL",
        "ALTER TABLE matricula MODIFY costo DECIMAL(10,2) NULL",
        "ALTER TABLE pago MODIFY periodo VARCHAR(7) NULL",
        "ALTER TABLE pago MODIFY valor_pago DECIMAL(10,2) NULL",
        "ALTER TABLE pago MODIFY fecha DATETIME NULL",
        "ALTER TABLE asistencia MODIFY fecha DATETIME NULL"
    ]
    applied_alters = 0
    for s in alters:
        try:
            cursor.execute(s)
            applied_alters += 1
        except Exception:
            # Puede fallar por falta de privilegios o porque ya está en ese estado
            pass
    if applied_alters:
        conn.commit()
        print(f"ALTERs aplicados: {applied_alters}")
    else:
        print("No se aplicaron ALTERs (posible falta de privilegios o ya estaban).")

    # ---------- Sedes ----------
    sede_ids = []
    common_sede_name = "Sede Principal"
    for i in range(N):
        if random.random() < LOW_VARIANCE_RATIO:
            nombre = common_sede_name
        else:
            nombre = f"Sede {rand_text(4, 10)}"
        ubicacion = maybe_null(f"Ciudad {random.choice(['A','B','C','D','E'])}")
        cursor.execute("INSERT INTO sede (nombre_sede, ubicacion) VALUES (%s, %s)", (nombre, ubicacion))
        sede_ids.append(cursor.lastrowid)
        # commit por lotes
        if (i + 1) % BATCH == 0:
            conn.commit()
    conn.commit()
    print(f"Sedes insertadas: {len(sede_ids)}")

    # ---------- Docentes ----------
    docente_ids = []
    common_docente = "Profesor Común"
    nombres_base = ['Ana','Juan','Luis','Marta','Carolina','Pedro']
    for i in range(N):
        if random.random() < LOW_VARIANCE_RATIO:
            nombre = common_docente
        else:
            nombre = f"{random.choice(nombres_base)} {random.choice(['Gómez','Pérez','López','Torres','Ruiz'])}"
        nombre = maybe_null(nombre)
        cursor.execute("INSERT INTO docente (nombre_docente) VALUES (%s)", (nombre,))
        docente_ids.append(cursor.lastrowid)
        if (i + 1) % BATCH == 0:
            conn.commit()
    conn.commit()
    print(f"Docentes insertados: {len(docente_ids)}")

    # ---------- Clases (Escuela Deportiva) ----------
    clase_ids = []
    deportes = ["Voleibol", "Fútbol", "Baloncesto"]
    for i in range(N):
        if random.random() < LOW_VARIANCE_RATIO:
            nombre_clase = random.choice(deportes)
        else:
            nombre_clase = rand_text(6, 18)  # Texto aleatorio, sin categorizar
        nombre_clase = maybe_null(nombre_clase)
        docente_id = random.choice(docente_ids)
        cursor.execute("INSERT INTO clase (nombre_clase, docente_id) VALUES (%s, %s)", (nombre_clase, docente_id))
        clase_ids.append(cursor.lastrowid)
        if (i + 1) % BATCH == 0:
            conn.commit()
    conn.commit()
    print(f"Clases insertadas: {len(clase_ids)}")

    # ---------- Matrículas ----------
    matricula_ids = []
    for i in range(N):
        if random.random() < LOW_VARIANCE_RATIO:
            costo = Decimal('100000.00')
        else:
            costo = Decimal(str(round(random.uniform(50000, 300000), 2)))
        costo = maybe_null(costo)
        fecha_pago = random_date(365*2, 0).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO matricula (costo, fecha_pago) VALUES (%s, %s)", (costo, fecha_pago))
        matricula_ids.append(cursor.lastrowid)
        if (i + 1) % BATCH == 0:
            conn.commit()
    conn.commit()
    print(f"Matrículas insertadas: {len(matricula_ids)}")

    # ---------- Alumnos ----------
    alumno_ids = []
    for i in range(N):
        if random.random() < LOW_VARIANCE_RATIO:
            nombre_alumno = "Estudiante Test"
        else:
            nombre_alumno = f"{random.choice(['Andrés','Lucía','Diego','Sofía','Camila','Miguel'])} {random.choice(['Gómez','Pérez','López','Torres'])}"
        nombre_alumno = maybe_null(nombre_alumno)
        matricula_id = random.choice(matricula_ids)
        sede_id = random.choice(sede_ids)
        cursor.execute("INSERT INTO alumno (nombre_alumno, matricula_id, sede_id) VALUES (%s, %s, %s)",
                       (nombre_alumno, matricula_id, sede_id))
        alumno_ids.append(cursor.lastrowid)
        if (i + 1) % BATCH == 0:
            conn.commit()
    conn.commit()
    print(f"Alumnos insertados: {len(alumno_ids)}")

    # ---------- clase_has_sede ----------
    relaciones_insertadas = 0
    intentos = 0
    while relaciones_insertadas < N and intentos < N * 4:  # limit para evitar loop infinito
        intentos += 1
        clase_id = random.choice(clase_ids)
        sede_id = random.choice(sede_ids)
        try:
            cursor.execute("INSERT INTO clase_has_sede (clase_id, sede_id) VALUES (%s, %s)", (clase_id, sede_id))
            relaciones_insertadas += 1
            if relaciones_insertadas % BATCH == 0:
                conn.commit()
        except Exception:
            pass
    conn.commit()
    print(f"Relaciones clase_has_sede insertadas: {relaciones_insertadas} (intentados: {intentos})")

    # ---------- Pagos ----------
    pago_count = 0
    periods = ['2025-01','2025-02','2025-03','2025-04', '2025-05']
    common_val = Decimal('50000.00')
    pagos_batch = []
    for i in range(N):
        fecha = random_date(365, 0).strftime('%Y-%m-%d %H:%M:%S')
        valor = common_val if random.random() < LOW_VARIANCE_RATIO else Decimal(str(round(random.uniform(20000, 150000), 2)))
        periodo = random.choice(periods) if random.random() > 0.15 else rand_text(4,7)
        valor = maybe_null(valor)
        periodo = maybe_null(periodo)
        alumno_id = random.choice(alumno_ids)
        pagos_batch.append((fecha, valor, periodo, alumno_id))
        if len(pagos_batch) >= BATCH:
            cursor.executemany("INSERT INTO pago (fecha, valor_pago, periodo, alumno_id) VALUES (%s, %s, %s, %s)", pagos_batch)
            pago_count += len(pagos_batch)
            pagos_batch = []
            conn.commit()
    if pagos_batch:
        cursor.executemany("INSERT INTO pago (fecha, valor_pago, periodo, alumno_id) VALUES (%s, %s, %s, %s)", pagos_batch)
        pago_count += len(pagos_batch)
        conn.commit()
    print(f"Pagos insertados: {pago_count}")

    # ---------- Asistencias ----------
    asistencia_count = 0
    asistencia_batch = []
    for i in range(N):
        fecha = random_date(90, 0).strftime('%Y-%m-%d %H:%M:%S')
        alumno_id = random.choice(alumno_ids)
        clase_id = random.choice(clase_ids)
        sede_id = random.choice(sede_ids)
        asistencia_batch.append((fecha, alumno_id, clase_id, sede_id))
        if len(asistencia_batch) >= BATCH:
            cursor.executemany("INSERT INTO asistencia (fecha, alumno_id, clase_id, sede_id) VALUES (%s, %s, %s, %s)", asistencia_batch)
            asistencia_count += len(asistencia_batch)
            asistencia_batch = []
            conn.commit()
    if asistencia_batch:
        cursor.executemany("INSERT INTO asistencia (fecha, alumno_id, clase_id, sede_id) VALUES (%s, %s, %s, %s)", asistencia_batch)
        asistencia_count += len(asistencia_batch)
        conn.commit()
    print(f"Asistencias insertadas: {asistencia_count}")

    # ---------- Resumen ----------
    print("\nCarga masiva finalizada. Resumen:")
    print(f" - Sedes: {len(sede_ids)}")
    print(f" - Docentes: {len(docente_ids)}")
    print(f" - Clases: {len(clase_ids)}")
    print(f" - Matrículas: {len(matricula_ids)}")
    print(f" - Alumnos: {len(alumno_ids)}")
    print(f" - Clase_has_sede: {relaciones_insertadas}")
    print(f" - Pagos: {pago_count}")
    print(f" - Asistencias: {asistencia_count}")

except Error as e:
    print("Error durante la carga:", e)
finally:
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()