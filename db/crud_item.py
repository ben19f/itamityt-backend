
import string
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.item import Item

def generate_link_id(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# async def create_item(db: AsyncSession, name: str, description: str, owner_user_id: int = None):
#     # Генерация уникального link_id
#     while True:
#         link_id = generate_link_id()
#         existing = await db.execute(select(Item).filter_by(link_id=link_id))
#         if not existing.scalar():
#             break
#
#     db_item = Item(
#         name=name,
#         description=description,
#         link_id=link_id,
#         owner_user_id=owner_user_id
#     )
#     db.add(db_item)
#     await db.commit()
#     await db.refresh(db_item)
#     return db_item
async def create_item(db: AsyncSession, name: str, description: str, owner_user_id: int):
    """Создаёт Item и привязывает к пользователю"""
    if owner_user_id is None:
        raise ValueError("owner_user_id must be provided")

    # Генерация уникального link_id
    while True:
        link_id = generate_link_id()
        existing = await db.execute(select(Item).filter_by(link_id=link_id))
        if not existing.scalar():
            break

    db_item = Item(
        name=name,
        description=description,
        link_id=link_id,
        owner_user_id=owner_user_id
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def get_all_items(db: AsyncSession):
    result = await db.execute(select(Item))
    return result.scalars().all()

async def get_items_by_user(db: AsyncSession, owner_user_id: int):
    result = await db.execute(select(Item).filter_by(owner_user_id=owner_user_id))
    return result.scalars().all()

async def get_item_by_link_id(db: AsyncSession, link_id: str):
    result = await db.execute(select(Item).filter_by(link_id=link_id))
    return result.scalar()

# async def delete_item(db: AsyncSession, item_id: int):
#     result = await db.execute(select(Item).filter_by(id=item_id))
#     item = result.scalar()
#     if item:
#         await db.delete(item)
#         await db.commit()
#     return item


async def delete_item(db: AsyncSession, item_id: int):
    item = await get_item_by_id(db, item_id)

    # удалить связанные клики
    await db.execute(
        delete(Click).where(Click.link_id == item.link_id)
    )

    # удалить сам item
    await db.delete(item)
    await db.commit()



# db/crud_item.py
async def get_item_by_id(db: AsyncSession, item_id: int):
    result = await db.execute(select(Item).filter_by(id=item_id))
    return result.scalar()

