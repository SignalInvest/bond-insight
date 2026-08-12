from pydantic import BaseModel, Field


class BondCompareRequest(BaseModel):
    isins: list[str] = Field(min_length=2, max_length=5)
