from fastapi import FastAPI

app = FastAPI()

@app.post("/chat")
async def chat():
    return {"message": "Hello World"}