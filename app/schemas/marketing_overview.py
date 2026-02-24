from pydantic import BaseModel


class CountOut(BaseModel):
    count: int


class ConversionRateOut(BaseModel):
    conversion_rate: float