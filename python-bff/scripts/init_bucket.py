"""Run once to initialize MinIO bucket."""
from app.services.oss import ensure_bucket

if __name__ == "__main__":
    ensure_bucket()
    print("Bucket initialized successfully.")
