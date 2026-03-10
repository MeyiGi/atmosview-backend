from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.wrf_api import router as wrf_router


from app.core.config import settings
from app.core.database import engine
from app.models import request_log
from app.routes.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on boot. If this ever becomes "real prod", revisit this.
    request_log.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="REST API for meteorological data visualization (GRIB → PNG)",
    lifespan=lifespan,
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# route registration
app.include_router(router)
app.include_router(wrf_router)