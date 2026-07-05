from fastapi import FastAPI

app = FastAPI(title="HelpDesk API")


@app.post("/chat")
async def chat():
    return {"message": "Hello World"}