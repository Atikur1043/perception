from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.database import init_db
from app.routes import auth_routes, evaluation_routes, teacher_routes, student_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await init_db()
    yield
    print("Shutting down...")

app = FastAPI(
    title="Perception API",
    description="API for the AI-Powered Online Evaluation Portal.",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://perception-ui.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])

app.include_router(teacher_routes.router, prefix="/api/teacher", tags=["Teacher"])

app.include_router(student_routes.router, prefix="/api/student", tags=["Student"])

app.include_router(evaluation_routes.router, prefix="/api", tags=["Evaluation"])


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Perception API!"}

