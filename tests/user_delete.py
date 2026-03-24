import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# tests/test_user_delete.py
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    await client.__aenter__()
    yield client
    await client.__aexit__(None, None, None)


@pytest.mark.anyio
async def test_delete_user_with_items(async_client):

    uid = uuid.uuid4().hex

    username = f"deleteuser_{uid}"
    email = f"{uid}@example.com"

    # создаем пользователя
    response = await async_client.post(
        "/users/register",
        json={
            "username": username,
            "email": email,
            "password": "testpass"
        }
    )

    assert response.status_code == 201

    user_id = response.json()["id"]

    # удаляем пользователя
    response = await async_client.delete(f"/users/delete/{user_id}")

    assert response.status_code == 204

    # повторное удаление должно дать 404
    response = await async_client.delete(f"/users/delete/{user_id}")

    assert response.status_code == 404
