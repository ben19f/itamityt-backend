from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.deps import get_db
from db.crud_item import create_item, get_items_by_user, delete_item, get_item_by_id
from schemas.item import ItemCreate, Item
from models.user import User
from core.security import get_current_user

router = APIRouter(prefix="/items", tags=["items"])

# -------------------------------
# Получить свои items
# -------------------------------
@router.get("/", response_model=list[Item])
async def read_own_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = await get_items_by_user(db, current_user.id)
    return items


# -------------------------------
# Добавить новый item
# -------------------------------
@router.post("/", response_model=Item, status_code=201)
async def add_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    new_item = await create_item(
        db,
        item.name,
        item.description,
        owner_user_id=current_user.id
    )
    return new_item

# -------------------------------
# Удалить свой item по id
# -------------------------------
@router.delete("/{item_id}")
async def remove_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Сначала получаем item
    item = await get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Проверяем владельца
    if item.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this item")

    await delete_item(db, item_id)
    return {"detail": "Item deleted"}
