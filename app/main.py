"""
FastAPI application entry point.
Main application setup, middleware configuration, and router registration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Create FastAPI application instance
app = FastAPI(
    title="E-commerce API",
    description="API for managing products, orders, and payment webhooks",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Configure CORS middleware
# Allows frontend applications to interact with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint - health check and API information.
    
    Returns:
        dict: API status and basic information
    """
    return {
        "message": "E-commerce API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.app_env
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Service health status
    """
    return {"status": "healthy"}


# Router registration
from app.routers import product_router

app.include_router(product_router.router, prefix="/api", tags=["Products"])
# app.include_router(orders.router, prefix="/api", tags=["Orders"])
# app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])

