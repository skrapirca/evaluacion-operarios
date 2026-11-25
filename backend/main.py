"""API del prototipo de evaluación de operarios. Documentación en /docs."""
import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import config
from backend.db import get_db
from backend.errors import registrar_manejadores
from backend.routers import analisis, empleados

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Evaluación de operarios - API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[config.FRONTEND_ORIGIN], allow_methods=["GET"], allow_headers=["*"])
registrar_manejadores(app)
app.include_router(empleados.router)
app.include_router(analisis.router)


@app.get("/api/health", tags=["Estado"])
def health(con=Depends(get_db)):
    n = con.execute("SELECT COUNT(*) FROM empleados").fetchone()[0]
    return {"status": "ok", "empleados": n}
