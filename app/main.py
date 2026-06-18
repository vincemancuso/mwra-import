from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import APP_NAME, STATIC_DIR, TEMPLATES_DIR
from app.errors import ReportNotFoundError, WaterProfileError
from app.service import WaterProfileService


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.profile_service = WaterProfileService()
    yield


app = FastAPI(title=APP_NAME, version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def service(request: Request) -> WaterProfileService:
    return request.app.state.profile_service


@app.exception_handler(WaterProfileError)
async def water_profile_error_handler(
    request: Request, exc: WaterProfileError
) -> JSONResponse:
    return JSONResponse(
        status_code=404 if isinstance(exc, ReportNotFoundError) else 502,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "manual_fallback": {
                "available": False,
                "message": "Local PDF upload is planned but is not implemented in this MVP.",
            },
        },
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": APP_NAME},
    )


@app.get("/api/latest")
async def latest(request: Request):
    profile, _ = await service(request).latest()
    return profile


@app.get("/api/reports")
async def reports(request: Request):
    return await service(request).reports()


@app.get("/api/reports/{year}/{month}")
async def report_profile(request: Request, year: int, month: int):
    profile, _ = await service(request).profile(year, month)
    return profile


@app.get("/api/reports/{year}/{month}/pdf", response_class=FileResponse)
async def report_pdf(request: Request, year: int, month: int):
    _, pdf_path = await service(request).profile(year, month)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="The cached report PDF is missing.")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
        content_disposition_type="inline",
    )


@app.get("/api/latest/pdf", response_class=FileResponse)
async def latest_pdf(request: Request):
    _, pdf_path = await service(request).latest()
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="The cached report PDF is missing.")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
        content_disposition_type="inline",
    )
