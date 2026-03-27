from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.person_routes import router as person_router
from backend.routes.scenario_routes import router as scenario_router
from backend.routes.event_routes import router as event_router
from backend.routes.location_routes import router as location_router
from backend.routes.dashboard_routes import router as dashboard_router
from backend.routes.config_routes import router as config_router
from backend.routes.camera_routes import router as camera_router
from backend.routes.tracking_routes import router as tracking_router

app = FastAPI(title="Health Track API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(person_router)
app.include_router(scenario_router)
app.include_router(event_router)
app.include_router(location_router)
app.include_router(dashboard_router)
app.include_router(config_router)
app.include_router(camera_router)
app.include_router(tracking_router)


@app.get("/")
def root():
    return {"status": "API rodando"}
