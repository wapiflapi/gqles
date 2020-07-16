from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return dict(
        mission="Make it hard to mess up."
    )
