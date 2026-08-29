from fastapi import FastAPI

app = FastAPI(
    title="Met Museum API",
    description="an ETL pipeline feeding a real API over CC0 Met data",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
