from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Server operational status")
    app: str = Field(default="VSM Conductor Simulator", description="Application name")
