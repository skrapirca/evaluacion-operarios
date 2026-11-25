# Incidencias encontradas al crear la base de datos

Origen: `Valoraciones_Operarios_Temporales_2026_Consolidado_APP_2.xlsx`

## Resumen de carga

| Tabla | Filas en el Excel | Cargadas | Descartadas |
|---|---|---|---|
| empleados | — | 4 | — |
| evaluaciones | 12 evaluaciones (× 5 aptitudes) | 60 filas (12 evaluaciones) | 0 |
| radar | 112 | 112 | 0 |
| ausencias | 56 | 53 | 3 |

## Filas descartadas

| Pestaña | Fila | Motivo |
|---|---|---|
| AUSENCIAS | 12 | Fila vacía: solo tiene CI y nombre (GONZALEZ, SONIA) |
| AUSENCIAS | 22 | Fila vacía: solo tiene CI y nombre (GARRIDO, FLAVIO) |
| AUSENCIAS | 51 | Fila vacía: solo tiene CI y nombre (ROBLES, FRANCISCO) |

## Avisos y transformaciones aplicadas

- Las puntuaciones vienen como texto ("4 - Muy bueno"); se guarda solo el número.
- El nombre del evaluador se toma de la celda B2 de cada pestaña, sin espacios sobrantes ("Juan Carlos " → "Juan Carlos").
- El turno de la pestaña RADAR es siempre "T2" y no coincide con el de las evaluaciones; se usa el turno de las evaluaciones.
- Los nombres vienen como "APELLIDO, NOMBRE"; se muestran como "Nombre Apellido" y el original se guarda en `nombre_original`.
- El género (para el avatar) se deduce del nombre de pila.
- Ausencias en horas: `dias = unidades / 8`. Ausencias en días: `dias = unidades`.
- Las ausencias se asignan al periodo consultado según su fecha de inicio.
- No se usan las pestañas PANEL EMPLEADOS ni las de Criterios, ni las columnas "Puntuación media" y "Estado / nivel" (la aplicación calcula sus propios promedios).
- El motivo "EXCESO JORNADA, COMPENSACIÓN FESTIVOS, ACUM., ETC" se carga y se muestra, pero no cuenta para el % de ausentismo (configurable en `backend/config.py`).
