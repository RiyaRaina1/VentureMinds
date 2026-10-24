from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SimulationRequest(BaseModel):
    price: float = Field(..., description="Subscription or average contract price per customer per month ($)", example=100.0)
    customers: int = Field(..., description="Active paying customers count", example=100)
    monthly_growth: float = Field(..., description="Projected monthly customer growth rate (%)", example=10.0)
    churn: float = Field(..., description="Monthly customer churn rate (%)", example=3.0)
    marketing_spend: float = Field(..., description="Monthly sales & marketing expense ($)", example=2000.0)
    salaries: float = Field(..., description="Monthly payroll & contractor expenses ($)", example=2500.0)
    infrastructure_cost: float = Field(..., description="Monthly cloud, GPU, and IT infrastructure costs ($)", example=500.0)
    other_expenses: float = Field(default=0.0, description="Other monthly operational expenses ($)", example=0.0)
    cash_balance: Optional[float] = Field(default=50000.0, description="Current cash reserve / capital balance ($) used for runway calculation", example=50000.0)

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than zero.")
        return v

    @field_validator("customers")
    @classmethod
    def validate_customers(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Customers count must be greater than zero.")
        return v

    @field_validator("churn")
    @classmethod
    def validate_churn(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Churn rate cannot be negative.")
        if v > 100:
            raise ValueError("Churn rate cannot exceed 100%.")
        return v

    @field_validator("monthly_growth", "marketing_spend", "salaries", "infrastructure_cost", "other_expenses")
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Expense and growth values cannot be negative.")
        return v

    @field_validator("cash_balance")
    @classmethod
    def validate_cash_balance(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Cash balance cannot be negative.")
        return v


class SimulationResponse(BaseModel):
    mrr: float = Field(..., description="Monthly Recurring Revenue ($)", example=10000.0)
    arr: float = Field(..., description="Annual Recurring Revenue ($)", example=120000.0)
    monthly_burn: float = Field(..., description="Total gross monthly expenses ($)", example=5000.0)
    runway_months: float = Field(..., description="Estimated runway horizon in months based on cash balance", example=10.0)
    net_burn: Optional[float] = Field(None, description="Net monthly burn (expenses minus MRR)", example=0.0)
    status: Optional[str] = Field(None, description="Financial status indicator (PROFITABLE, BALANCED, HIGH RISK)")
