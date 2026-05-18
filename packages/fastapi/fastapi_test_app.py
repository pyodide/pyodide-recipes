async def handle_request(request):
    import asgi

    return await asgi.handle_request(app, request)

# Set up fastapi app

from fastapi import FastAPI

app = FastAPI()

def temp(app):
  @app.get("/hello")
  async def hello():
      return {"message": "Hello World"}

  @app.get("/items/{item_id}")
  async def read_item(item_id: int):
      return {"item_id": item_id}

temp(app)
