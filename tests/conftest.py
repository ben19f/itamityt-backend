import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)  # <- используем ASGITransport
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        yield client
