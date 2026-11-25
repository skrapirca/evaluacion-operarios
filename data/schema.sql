-- Esquema de la base de datos del prototipo de evaluación de operarios.
-- Clave del empleado: CI (código de legajo).

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS ausencias;
DROP TABLE IF EXISTS radar;
DROP TABLE IF EXISTS evaluaciones;
DROP TABLE IF EXISTS empleados;

CREATE TABLE empleados (
    ci              INTEGER PRIMARY KEY,
    nombre          TEXT    NOT NULL,              -- "Flavio Garrido"
    nombre_original TEXT    NOT NULL,              -- "GARRIDO, FLAVIO" (como viene en el Excel)
    turno           TEXT    NOT NULL CHECK (turno IN ('Mañana', 'Tarde', 'Noche')),
    genero          TEXT             CHECK (genero IN ('M', 'F'))
);

CREATE TABLE evaluaciones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ci          INTEGER NOT NULL REFERENCES empleados(ci),
    fecha       TEXT    NOT NULL CHECK (date(fecha) IS NOT NULL),
    evaluador   TEXT    NOT NULL,
    aptitud     INTEGER NOT NULL CHECK (aptitud BETWEEN 1 AND 5),
    puntaje     INTEGER NOT NULL CHECK (puntaje BETWEEN 1 AND 5),
    observacion TEXT    NOT NULL
);

CREATE TABLE radar (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ci                  INTEGER NOT NULL REFERENCES empleados(ci),
    fecha               TEXT    NOT NULL CHECK (date(fecha) IS NOT NULL),
    tipo_incidencia     TEXT    NOT NULL,
    gravedad            TEXT    NOT NULL CHECK (gravedad IN ('Leve', 'Moderado', 'Grave')),
    descripcion         TEXT    NOT NULL,
    area                TEXT,
    titulo              TEXT,
    accion_realizada    TEXT,
    reaccion_trabajador TEXT,
    observaciones       TEXT
);

CREATE TABLE ausencias (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ci            INTEGER NOT NULL REFERENCES empleados(ci),
    fecha         TEXT    NOT NULL CHECK (date(fecha) IS NOT NULL),   -- fecha de inicio
    fecha_fin     TEXT             CHECK (fecha_fin IS NULL OR date(fecha_fin) IS NOT NULL),
    motivo        TEXT    NOT NULL,
    hora_inicio   TEXT,
    hora_fin      TEXT,
    unidades      REAL    NOT NULL CHECK (unidades > 0),
    unidad_tiempo TEXT    NOT NULL CHECK (unidad_tiempo IN ('Día', 'Hora')),
    dias          REAL    NOT NULL CHECK (dias > 0)                    -- Hora: unidades / 8 · Día: unidades
);

CREATE INDEX idx_evaluaciones_ci_fecha ON evaluaciones (ci, fecha);
CREATE INDEX idx_radar_ci_fecha        ON radar (ci, fecha);
CREATE INDEX idx_ausencias_ci_fecha    ON ausencias (ci, fecha);
