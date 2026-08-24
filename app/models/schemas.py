from pydantic import BaseModel, Field
from typing import Any, Optional


class DedupRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., description="待去重的记录列表")
    match_fields: list[str] = Field(..., description="参与匹配的字段名")
    match_mode: str = Field("exact", description="匹配模式: exact | fuzzy")
    similarity_threshold: float = Field(0.85, ge=0, le=1, description="模糊模式相似度阈值")
    standardize_before_match: bool = Field(True, description="匹配前先做标准化")


class DuplicateGroup(BaseModel):
    group_id: int
    master_id: Any
    duplicate_ids: list[Any]
    similarity_score: Optional[float] = None
    match_reason: str


class DedupResponse(BaseModel):
    status: str
    total_records: int
    unique_count: int
    duplicate_count: int
    duplicate_groups: list[DuplicateGroup]
    deduplicated_records: list[dict[str, Any]]
    removed_ids: list[Any]
    credits_used: int
    processing_time_ms: int


class StandardizeRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., description="待标准化的记录列表")
    fields: list[str] = Field(..., description="需要标准化的字段名")
    rules: Optional[dict] = Field(None, description="自定义规则")


class StandardizeChange(BaseModel):
    field: str
    original: str
    standardized: str


class StandardizeDetail(BaseModel):
    record: dict[str, Any]
    original: dict[str, Any]
    changed: bool
    changes: list[StandardizeChange]


class StandardizeResponse(BaseModel):
    status: str
    total_records: int
    changed_count: int
    standardized_records: list[dict[str, Any]]
    credits_used: int
    processing_time_ms: int


class CleanRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., description="待清洗的记录列表")
    pipeline: list[str] = Field(
        ["standardize", "validate", "dedup"],
        description="清洗流程: standardize | validate | dedup",
    )
    config: dict = Field(
        default_factory=dict,
        description="各模块配置",
    )


class CleanSummary(BaseModel):
    input_count: int
    after_standardize: Optional[int] = None
    after_validate: Optional[int] = None
    after_dedup: Optional[int] = None
    final_count: int
    removed_duplicates: Optional[int] = None
    invalid_records: Optional[int] = None


class QualityReport(BaseModel):
    completeness: float
    uniqueness: float
    validity: float
    overall_score: int


class CleanResponse(BaseModel):
    status: str
    summary: CleanSummary
    cleaned_records: list[dict[str, Any]]
    quality_report: QualityReport
    credits_used: int
    processing_time_ms: int


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
