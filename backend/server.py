from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone
from fastapi.responses import Response
import csv
import io

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- LOAD ENV ----------------
load_dotenv()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ---------------- DATABASE ----------------
mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")

client = AsyncIOMotorClient(mongo_url)
db = client.failsafe_ai

# ---------------- FASTAPI APP ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    client.close()

app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")

# ---------------- MODELS ----------------
class MachineHealthInput(BaseModel):
    temperature: float
    vibration: float
    rpm: float

class RiskAssessment(BaseModel):
    risk_score: int
    status: str
    issues: List[str]
    temperature: float
    vibration: float
    rpm: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class MachineHealthCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    temperature: float
    vibration: float
    rpm: float
    risk_score: int
    status: str
    issues: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DashboardStats(BaseModel):
    total_checks: int
    safe_count: int
    medium_risk_count: int
    high_risk_count: int
    avg_risk_score: float

# ---------------- RISK LOGIC ----------------
def calculate_risk(temp, vib, rpm):
    risk = 0
    issues = []
    status = "Safe"

    if temp > 80:
        risk += 30
        issues.append("High Temperature")

    if vib > 1.5:
        risk += 40
        issues.append("High Vibration")

    if rpm > 5000:
        risk += 20
        issues.append("High RPM")

    if risk > 70:
        status = "High Risk"
    elif risk >= 40:
        status = "Medium Risk"

    return risk, issues, status

# ---------------- ROUTES ----------------
@api_router.get("/")
async def root():
    return {"message": "FailSafe AI API Running"}

@api_router.post("/machine-health/check", response_model=RiskAssessment)
async def check_machine_health(input: MachineHealthInput):

    logger.info(f"Input: {input}")

    risk_score, issues, status = calculate_risk(
        input.temperature,
        input.vibration,
        input.rpm
    )

    assessment = RiskAssessment(
        risk_score=risk_score,
        status=status,
        issues=issues,
        temperature=input.temperature,
        vibration=input.vibration,
        rpm=input.rpm
    )

    doc = assessment.model_dump()
    await db.machine_health_checks.insert_one(doc)

    return assessment

@api_router.get("/machine-health/history", response_model=List[MachineHealthCheck])
async def get_history():
    data = await db.machine_health_checks.find({}, {"_id": 0}).sort("timestamp", -1).to_list(50)
    return data

@api_router.get("/machine-health/stats")
async def get_stats():
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_checks": {"$sum": 1},
                "safe_count": {"$sum": {"$cond": [{"$eq": ["$status", "Safe"]}, 1, 0]}},
                "medium_risk_count": {"$sum": {"$cond": [{"$eq": ["$status", "Medium Risk"]}, 1, 0]}},
                "high_risk_count": {"$sum": {"$cond": [{"$eq": ["$status", "High Risk"]}, 1, 0]}},
                "avg_risk_score": {"$avg": "$risk_score"}
            }
        }
    ]

    result = await db.machine_health_checks.aggregate(pipeline).to_list(1)

    if not result:
        return {
            "total_checks": 0,
            "safe_count": 0,
            "medium_risk_count": 0,
            "high_risk_count": 0,
            "avg_risk_score": 0.0
        }

    return result[0]

@api_router.get("/machine-health/export")
async def export_csv():
    data = await db.machine_health_checks.find({}, {"_id": 0}).to_list(1000)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "timestamp", "temperature", "vibration",
        "rpm", "risk_score", "status", "issues"
    ])

    writer.writeheader()

    for row in data:
        if isinstance(row.get("issues"), list):
            row["issues"] = ", ".join(row["issues"])
        writer.writerow(row)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=report.csv"}
    )

# ---------------- INCLUDE ROUTER ----------------
app.include_router(api_router)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)