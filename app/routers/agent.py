from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ProjectAnalysisResponse
from app.services.project_analysis import generate_project_analysis

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/project-analysis", response_model=ProjectAnalysisResponse)
def project_analysis(db: Session = Depends(get_db)) -> ProjectAnalysisResponse:
    data = generate_project_analysis(db)
    return ProjectAnalysisResponse(**data)
