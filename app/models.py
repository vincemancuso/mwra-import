from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ReportLink(BaseModel):
    model_config = ConfigDict(frozen=True)

    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000)
    label: str
    url: str

    @property
    def report_date(self) -> date:
        return date(self.year, self.month, 1)

    @computed_field
    @property
    def month_year(self) -> str:
        return self.report_date.strftime("%B %Y")

    @property
    def cache_filename(self) -> str:
        return f"mwra-water-quality-{self.year:04d}-{self.month:02d}.pdf"


class ReportCatalog(BaseModel):
    reports: list[ReportLink]
    latest: ReportLink


class RawMeasurement(BaseModel):
    parameter: str
    value: float
    unit: str
    source_label: str


class ProfileMeasurement(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    description: str


class Conversion(BaseModel):
    field: str
    source_parameter: str
    source_value: float
    source_unit: str
    formula: str
    result: float
    result_unit: str


class BrewfatherValues(BaseModel):
    calcium: float
    magnesium: float
    sodium: float
    chloride: float
    sulfate: float
    bicarbonate: float
    ph: float = Field(alias="pH")

    model_config = ConfigDict(populate_by_name=True)


class ReportMetadata(BaseModel):
    report_month: str
    report_month_number: int = Field(ge=1, le=12)
    report_year: int
    report_label: str
    source_page_url: str
    source_pdf_url: str
    selected_column: str
    cached_filename: str
    fetched_at: datetime


class WaterProfileResponse(BaseModel):
    name: str
    report: ReportMetadata
    raw_values: dict[str, RawMeasurement]
    profile_values: list[ProfileMeasurement] = Field(default_factory=list)
    other_values: list[ProfileMeasurement] = Field(default_factory=list)
    conversions: list[Conversion]
    brewfather_values: BrewfatherValues


class HistoryPoint(BaseModel):
    report_month: str
    report_month_number: int = Field(ge=1, le=12)
    report_year: int
    month_year: str
    value: float
    normalized: float


class HistorySeries(BaseModel):
    key: str
    label: str
    unit: str
    description: str
    min_value: float
    max_value: float
    points: list[HistoryPoint]


class SkippedHistoryReport(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000)
    month_year: str
    error: str


class WaterProfileHistoryResponse(BaseModel):
    source_page_url: str
    normalized_scale: str
    series: list[HistorySeries]
    skipped_reports: list[SkippedHistoryReport] = Field(default_factory=list)
