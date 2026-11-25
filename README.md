# Evaluación de operarios · Prototipo

Aplicación web para evaluar el desempeño de los operarios de un centro: **performance individual**, **comparación** entre empleados y **ranking**.

- **Backend:** Python + FastAPI + SQLite (documentación automática de la API en `/docs`)
- **Frontend:** Streamlit
- **Tests:** pytest + FastAPI TestClient + Streamlit AppTest

No necesitas crear cuentas en ningún servicio: todo funciona en tu ordenador.

---

## 1. Cómo probarlo (paso a paso)

### Requisitos
- **Python 3.11 o superior.** Descárgalo de https://www.python.org/downloads/
  En Windows, marca la casilla **"Add Python to PATH"** durante la instalación.

### Instalación (solo la primera vez)
Abre una terminal (en Windows: *Símbolo del sistema* o *PowerShell*; en Mac: *Terminal*) dentro de la carpeta del proyecto y ejecuta:

```bash
# 1. Crear un entorno virtual (recomendado)
python -m venv .venv

# 2. Activarlo
#    Windows:
.venv\Scripts\activate
#    Mac / Linux:
source .venv/bin/activate

# 3. Instalar las librerías
pip install -r requirements.txt
```

> En Mac, si `python` no funciona, usa `python3`.

### Arrancar la aplicación
```bash
python run.py
```

Se levantan el backend y el frontend a la vez. Abre en el navegador:

| Qué | Dirección |
|---|---|
| **Aplicación** | http://localhost:8501 |
| Documentación de la API | http://localhost:8000/docs |

Para detenerla, pulsa `Ctrl + C` en la terminal.

### Ejecutar los tests
```bash
pytest
```

### Publicarla online (Streamlit Community Cloud, gratis)
1. Entra en https://share.streamlit.io e inicia sesión con tu cuenta de GitHub.
2. Pulsa **Create app** → **Deploy a public app from GitHub**.
3. Rellena: **Repository** `skrapirca/evaluacion-operarios` · **Branch** `main` · **Main file path** `frontend/app.py`.
   En **App URL** puedes elegir el nombre del enlace (por ejemplo `evaluacion-operarios`).
4. En **Advanced settings**, elige Python 3.12 y pulsa **Deploy**.

En la nube no hay un backend aparte: si no existe la variable `API_URL`, el frontend ejecuta la misma API FastAPI dentro de su propio proceso (modo embebido). En local, `python run.py` arranca los dos por separado.

---

## 2. Qué hace la aplicación

| Pantalla | Contenido |
|---|---|
| **Inicio** | Tres tarjetas de acceso a cada apartado. |
| **Performance** | Buscador por nombre o CI (desde la primera letra) y periodo. Avatar y datos del empleado, ranking 1–10, promedio general con estrellas y color (rojo < 3 · amarillo < 4 · verde ≥ 4), promedio y resumen de comentarios por aptitud, conflictos del Radar por tipo y gravedad, ausencias por motivo y % de ausentismo, y el detalle de evaluaciones, conflictos y ausencias. |
| **Comparación** | De 2 a 5 empleados. Fichas con "Ver ficha", tabla de aptitudes (verde el más alto y rojo el más bajo de cada fila), Radar (verde el mejor y rojo el peor) y ausencias por motivo (sin colores). |
| **Ranking** | Filtro por turno y periodo. Orden por ranking o por turno, ascendente o descendente (por defecto, de mejor a peor). Tarjetas con avatar, datos, ranking y "Ver ficha". |

La URL de la ficha se puede compartir: `http://localhost:8501/performance?ci=576010&desde=2026-01-01&hasta=2026-11-30`

---

## 3. Reglas de cálculo

Todos los parámetros se pueden cambiar en `backend/config.py`.

- **Promedio por aptitud:** media de los puntajes de esa aptitud en el periodo.
- **Promedio general:** media de los promedios por aptitud.
- **Días de ausencia:** si la unidad es *Hora*, `días = horas / 8`; si es *Día*, sin transformar.
- **% de ausentismo:** `días que computan / 225 × 100`.
  *"EXCESO JORNADA, COMPENSACIÓN FESTIVOS, ACUM., ETC"* se muestra pero **no computa** (son días recuperados, no ausencias).
- **Ranking 1–10:**

  ```
  aptitudes  = (promedio_general − 1) / 4                                  peso 70 %
  conflictos = max(0, 1 − penalización / 100)   leve 1 · moderado 3 · grave 5   peso 20 %
  ausencias  = max(0, 1 − días_falta_sin_justificar / 10)                  peso 10 %

  ranking = 1 + 9 × (0,7·aptitudes + 0,2·conflictos + 0,1·ausencias)
  ```

  Solo penaliza el motivo **"FALTA SIN JUSTIFICAR"**. Un empleado sin evaluaciones en el periodo aparece como **"Sin datos"** y al final del ranking.

  > El tope de penalización por conflictos es **100** y no 10: con los datos reales (56–78 puntos por empleado), con 10 todos quedaban en 0 y el componente no diferenciaba a nadie.

---

## 4. API

Todos los endpoints con periodo aceptan `desde` y `hasta` (`AAAA-MM-DD`, ambos inclusive).

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/empleados` | Lista completa de empleados |
| GET | `/api/empleados?q=texto` | Búsqueda por nombre o CI (desde 1 carácter, máx. 10 resultados) |
| GET | `/api/empleados/{ci}` | Datos del empleado |
| GET | `/api/empleados/{ci}/performance` | Ficha completa |
| GET | `/api/comparacion?cis=1,2,3` | Comparación de 2 a 5 empleados |
| GET | `/api/ranking?turno=todos&orden=ranking_desc` | Ranking. `turno`: todos, Mañana, Tarde, Noche · `orden`: ranking_desc, ranking_asc, turno_asc, turno_desc |
| GET | `/api/health` | Estado del servicio |

**Errores** con formato uniforme: `{"error": {"code": "...", "message": "...", "details": {...}}}`

| HTTP | code | Cuándo |
|---|---|---|
| 400 | `INVALID_DATE_RANGE` | Fecha mal formada o `desde` > `hasta` |
| 400 | `INVALID_COMPARISON_SIZE` | Menos de 2 o más de 5 CI, o CI duplicados |
| 400 | `INVALID_PARAMETER` | Turno, orden o parámetro no válido; `q` vacío |
| 404 | `EMPLOYEE_NOT_FOUND` | CI inexistente |
| 404 | `NOT_FOUND` | Ruta inexistente |
| 500 | `INTERNAL_ERROR` | Error inesperado (sin exponer detalles internos) |

Un periodo sin datos **no es un error**: devuelve 200 con listas vacías.

---

## 5. Datos

En `data/`:

| Archivo | Contenido |
|---|---|
| `schema.sql` | Creación de las tablas (con restricciones CHECK, NOT NULL y FOREIGN KEY) |
| `data.sql` | Inserción de los datos |
| `evaluaciones.db` | Base de datos SQLite lista para usar |
| `incidencias-datos.md` | Filas descartadas y transformaciones aplicadas al pasar el Excel a la BBDD |

Tablas: `empleados` (clave: CI), `evaluaciones` (con columna `evaluador`), `radar` y `ausencias` (con columna calculada `dias`).

La aplicación **no importa Excel**: la base de datos ya viene creada.

---

## 6. Estructura del proyecto

```
backend/
  main.py            Aplicación FastAPI
  config.py          Parámetros de negocio (pesos, topes, motivos…)
  db.py              Conexión a SQLite (solo lectura)
  errors.py          Formato uniforme de errores
  routers/           Endpoints y validación de parámetros
  services/          calculos.py (lógica pura) · consultas.py (BBDD → respuestas)
frontend/
  app.py             Navegación y red de seguridad de errores
  views/             Inicio, Performance, Comparación, Ranking
  components/ui.py   Avatar, estrellas, tablas, filtros, mensajes de error
  api_client.py      Único acceso a la API (timeout, caché y errores controlados)
  utils.py           Lógica de presentación (colores, estrellas…)
  assets/            Avatares SVG y estilos
data/                Base de datos y scripts SQL
tests/               Unitarios, BBDD, API y pantallas
.streamlit/          Tema visual
run.py               Arranque de backend + frontend
```

---

## 7. Tests

`pytest` ejecuta 86 tests:

| Archivo | Qué prueba |
|---|---|
| `test_unitarios.py` | Conversión horas → días, promedios, colores, estrellas, ranking, % de ausentismo, avatares y colores de comparación |
| `test_bd.py` | Integridad de la BBDD de demo (claves, rangos, conversiones, restricciones, número de filas) |
| `test_api.py` | Todos los endpoints y errores (fechas, tamaños, turnos, 404, 500, inyección SQL) |
| `test_frontend.py` | Pantallas con AppTest: buscador, validaciones, tooltips, errores 500, backend caído, "Empleado no encontrado", colores, flujos completos y modo embebido |

Los tests usan una BBDD propia con datos fijos (`tests/conftest.py`), independiente de la de demo. GitHub Actions los ejecuta en cada push (`.github/workflows/tests.yml`).

---

## 8. Variables de entorno (opcionales)

| Variable | Por defecto | Uso |
|---|---|---|
| `API_URL` | (vacía) | URL del backend. `run.py` la define; si no existe, la API se ejecuta dentro del frontend (modo embebido, usado en Streamlit Cloud) |
| `API_PORT` | `8000` | Puerto del backend |
| `FRONTEND_PORT` | `8501` | Puerto del frontend |
| `DB_PATH` | `data/evaluaciones.db` | Ruta de la base de datos |
