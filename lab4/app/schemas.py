from typing import Literal

from pydantic import BaseModel, Field


class AudienceSegment(BaseModel):
    name: str = Field(min_length=3)
    description: str = Field(min_length=10)
    requests: list[str] = Field(min_length=1)
    pains: list[str] = Field(min_length=1)
    needs: list[str] = Field(min_length=1)
    fears: list[str] = Field(min_length=1)
    objections: list[str] = Field(min_length=1)


class AudienceAnalysis(BaseModel):
    segments: list[AudienceSegment] = Field(min_length=3, max_length=3)


class HookItem(BaseModel):
    text: str = Field(min_length=5)
    approach: str = Field(min_length=3)
    basis: str = Field(min_length=5)


class HooksResult(BaseModel):
    hooks: list[HookItem] = Field(min_length=10, max_length=10)


class CreativeDraft(BaseModel):
    body_style: Literal["bullets", "text"]
    body: list[str] = Field(min_length=1, max_length=3)
    cta: str = Field(min_length=3, max_length=60)
    price: str = ""
