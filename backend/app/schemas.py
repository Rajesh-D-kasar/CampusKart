from pydantic import BaseModel, Field


class Product(BaseModel):
    id: int
    name: str
    price: int = Field(ge=0)
    category: str
    unit: str
    icon: str
    in_stock: bool = True
