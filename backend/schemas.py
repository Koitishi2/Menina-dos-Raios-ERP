from typing import Optional

from pydantic import BaseModel


class LoginIn(BaseModel):
    username: str
    password: str


class UserIn(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = "editor"


class AdminMessageIn(BaseModel):
    user_id: str
    title: str
    body: str
    expires_days: Optional[int] = 7


class SaleIn(BaseModel):
    sale_type: str
    sale_date: str
    sale_time: Optional[str] = None
    client: Optional[str] = None
    product: Optional[str] = None
    nf_number: Optional[str] = None
    quantity: float = 0
    unit_price: float = 0
    total: Optional[float] = None
    notes: Optional[str] = None
    delivery_person: Optional[str] = None
    plate: Optional[str] = None
    source: str = "manual"


class PriceUpdate(BaseModel):
    key: str
    price: float
    price_min: Optional[float] = None
    price_max: Optional[float] = None


class ClientIn(BaseModel):
    name: str
    cnpj: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None
