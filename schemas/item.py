
from pydantic import BaseModel
from typing import Optional

class ItemBase(BaseModel):
    name: str
    description: str

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    link_id: str
    owner_user_id: Optional[int]

    class Config:
        orm_mode = True
