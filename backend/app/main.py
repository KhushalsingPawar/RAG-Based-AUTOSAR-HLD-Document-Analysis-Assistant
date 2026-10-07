from fastapi import FastAPI

from app.api.document_routes import router as document_router


app = FastAPI(
    title="AUTOSAR HLD Analysis Assistant",
    description=(
        "AI-assisted AUTOSAR High-Level Design "
        "document analysis system"
    ),
    version="1.0.0"
)


# Register document API
app.include_router(document_router)


@app.get("/")
def root():

    return {
        "message": (
            "AUTOSAR HLD Analysis Assistant "
            "API is running"
        )
    }