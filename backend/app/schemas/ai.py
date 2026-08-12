from pydantic import BaseModel, Field


class BondExplainRequest(BaseModel):
    isin: str = Field(min_length=1, max_length=32)


class BondAICompareRequest(BaseModel):
    isins: list[str] = Field(min_length=2, max_length=5)
