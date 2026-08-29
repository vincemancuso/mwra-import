from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.brewfather import (
    beerxml_filename,
    brewfather_filename,
    build_beerxml,
    build_brewfather_recipe,
)
from app.config import APP_NAME, CONFIG_PATH, STATIC_DIR, TEMPLATES_DIR
from app.errors import ReportNotFoundError, WaterProfileError
from app.service import WaterProfileService
from app.settings import load_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings(CONFIG_PATH)
    app.state.settings = settings
    app.state.profile_service = WaterProfileService(settings)
    yield


app = FastAPI(title=APP_NAME, version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-src 'self'; "
        "frame-ancestors 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}


def service(request: Request) -> WaterProfileService:
    return request.app.state.profile_service


def csv_download(content: str, filename: str) -> Response:
    return Response(
        content=content,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        media_type="text/csv",
    )


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    return response


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
                "message": "Local PDF upload is planned but is not implemented yet.",
            },
        },
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "mwra_reports_page_url": str(request.app.state.settings.mwra_reports_page_url),
        },
    )


@app.get("/api/latest")
async def latest(request: Request):
    profile, _ = await service(request).latest()
    return profile


@app.get("/api/reports")
async def reports(request: Request):
    return await service(request).reports()


@app.get("/api/history")
async def history(request: Request):
    return await service(request).history()


@app.get("/api/exports/brewing-values.csv")
async def brewing_values_csv(request: Request):
    return csv_download(
        await service(request).brewing_values_csv(),
        "mwra-brewing-values-ppm.csv",
    )


@app.get("/api/exports/raw-values.csv")
async def raw_values_csv(request: Request):
    return csv_download(
        await service(request).raw_values_csv(),
        "mwra-raw-water-values.csv",
    )


@app.get("/api/reports/{year}/{month}")
async def report_profile(
    request: Request,
    year: int = Path(ge=2000, le=2100),
    month: int = Path(ge=1, le=12),
):
    profile, _ = await service(request).profile(year, month)
    return profile


@app.get("/api/reports/{year}/{month}/pdf", response_class=FileResponse)
async def report_pdf(
    request: Request,
    year: int = Path(ge=2000, le=2100),
    month: int = Path(ge=1, le=12),
):
    _, pdf_path = await service(request).profile(year, month)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="The cached report PDF is missing.")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
        content_disposition_type="inline",
    )


@app.get("/api/reports/{year}/{month}/brewfather.json")
async def brewfather_recipe(
    request: Request,
    year: int = Path(ge=2000, le=2100),
    month: int = Path(ge=1, le=12),
):
    profile, _ = await service(request).profile(year, month)
    return JSONResponse(
        content=build_brewfather_recipe(profile),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{brewfather_filename(profile)}"'
            )
        },
        media_type="application/json",
    )


@app.get("/api/reports/{year}/{month}/beerxml.xml")
async def beerxml_recipe(
    request: Request,
    year: int = Path(ge=2000, le=2100),
    month: int = Path(ge=1, le=12),
):
    profile, _ = await service(request).profile(year, month)
    recipe = build_brewfather_recipe(profile)
    return Response(
        content=build_beerxml(recipe),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{beerxml_filename(profile)}"'
            )
        },
        media_type="application/xml",
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
