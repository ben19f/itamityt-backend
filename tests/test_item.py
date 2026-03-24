import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# tests/test_item.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app  # твой FastAPI app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    await client.__aenter__()  # открываем контекст
    yield client
    await client.__aexit__(None, None, None)  # закрываем контекст

@pytest.mark.anyio
async def test_user_register(async_client):
    # Обязательно указываем email, чтобы соответствовать модели UserCreate
    response = await async_client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "testuser@test.com",
            "password": "testpass"
        }
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@test.com"
    assert "id" in data
