from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.services.auth_dependency import usuario_logado, apenas_admin

from backend.routes.auth_routes import router as auth_router
from backend.routes.user_routes import router as user_router
from backend.routes.person_routes import router as person_router
from backend.routes.scenario_routes import router as scenario_router
from backend.routes.event_routes import router as event_router
from backend.routes.location_routes import router as location_router
from backend.routes.dashboard_routes import router as dashboard_router
from backend.routes.config_routes import router as config_router
from backend.routes.camera_routes import router as camera_router
from backend.routes.tracking_routes import router as tracking_router
from backend.routes.person_event_routes import router as person_event_router
from backend.routes.media_routes import router as media_router
from backend.routes.upload_mapa_route import router as upload_mapa_router
from backend.routes.biodoc_routes import router as biodoc_router

app = FastAPI(title="Health Track API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.20.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rotas publicas (sem token) ────────────────────────────────────────────────
app.include_router(auth_router)

# ── Rotas protegidas (exigem token valido) ────────────────────────────────────
# user_router e config_router aplicam apenas_admin no proprio APIRouter,
# entao user_router nao precisa do dependencies generico aqui.
protegido = [Depends(usuario_logado)]

app.include_router(user_router)
app.include_router(person_router,       dependencies=protegido)
app.include_router(scenario_router,     dependencies=protegido)
app.include_router(event_router,        dependencies=protegido)
app.include_router(location_router,     dependencies=protegido)
app.include_router(dashboard_router,    dependencies=protegido)
app.include_router(config_router,       dependencies=protegido)
app.include_router(camera_router,       dependencies=protegido)
app.include_router(tracking_router,     dependencies=protegido)
app.include_router(person_event_router, dependencies=protegido)
app.include_router(upload_mapa_router,  dependencies=protegido)
app.include_router(biodoc_router,       dependencies=protegido)

# media_router fica sem protecao: imagens via <img> nao enviam Authorization.
app.include_router(media_router)


@app.get("/")
def root():
    return {"status": "API rodando"}
