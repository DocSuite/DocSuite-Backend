from app.schemas.base_schema import TimestampIdSchema


class AuditRead(TimestampIdSchema):
    event: str
    module: str
    status: str
    detail: str | None = None
    resource_id: str | None = None
    user_email: str
