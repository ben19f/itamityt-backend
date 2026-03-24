# tests/cascad_test.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
import uuid
from httpx import AsyncClient
from main import app  # твое FastAPI приложение

@pytest.mark.anyio
async def test_user_delete_with_items():
    uid = uuid.uuid4().hex
    username = f"user_{uid}"
    email = f"{uid}@example.com"
    password = "testpass"

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        # -------------------------------
        # 1️⃣ регистрация
        # -------------------------------
        response = await client.post(
            "/users/register",
            json={"username": username, "email": email, "password": password}
        )
        assert response.status_code == 201
        user_id = response.json()["id"]

        # -------------------------------
        # 2️⃣ логин
        # -------------------------------
        response = await client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # -------------------------------
        # 3️⃣ создаём item 1
        # -------------------------------
        response = await client.post(
            "/items/",
            headers=headers,
            json={"name": "Item 1", "description": "desc1"}
        )
        assert response.status_code == 201
        item1_id = response.json()["id"]

        # -------------------------------
        # 4️⃣ создаём item 2
        # -------------------------------
        response = await client.post(
            "/items/",
            headers=headers,
            json={"name": "Item 2", "description": "desc2"}
        )
        assert response.status_code == 201
        item2_id = response.json()["id"]

        # -------------------------------
        # 5️⃣ удаляем item 1
        # -------------------------------
        response = await client.delete(f"/items/{item1_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["detail"] == "Item deleted"

        # -------------------------------
        # 6️⃣ проверяем, что остался только item 2
        # -------------------------------
        response = await client.get(f"/items/", headers=headers)
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["id"] == item2_id

        # -------------------------------
        # 7️⃣ удаляем пользователя
        # -------------------------------
        response = await client.delete(f"/users/delete/{user_id}", headers=headers)
        assert response.status_code == 204

        # # -------------------------------
        # # 8️⃣ проверяем, что пользователя больше нет
        # # -------------------------------
        # response = await client.get("/users/me", headers=headers)
        # assert response.status_code == 401  # токен больше не действителен
        #
        # #9 проверяем, что item 2 тоже удалён (каскад)
        # response = await client.get(f"/items/profile/{user_id}", headers=headers)
        # assert response.status_code == 200
        # items = response.json()
        # assert len(items) == 0