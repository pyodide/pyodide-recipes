from fastapi_test_app import handle_request
from js import Request
import pytest

@pytest.mark.asyncio
async def test_a():
    r = await handle_request(Request.new("https://localhost:8000/hello"))
    assert r.status == 200
    json = await r.json()
    assert json.to_py() == {"message": "Hello World"}

    r = await handle_request(Request.new("https://localhost:8000/items/7"))
    assert r.status == 200
    json = await r.json()
    assert json.to_py() == {"item_id": 7}
