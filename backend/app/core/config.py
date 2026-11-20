import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

JWT_SECRET_KEY = os.getenv("KAHVECELL_JWT_SECRET")
if JWT_SECRET_KEY is None or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "KAHVECELL_JWT_SECRET must be set to a secret of at least 32 characters "
        "in backend/.env."
    )

QR_SIGNING_SECRET = os.getenv("KAHVECELL_QR_SECRET")
if QR_SIGNING_SECRET is None or len(QR_SIGNING_SECRET) < 32:
    raise RuntimeError(
        "KAHVECELL_QR_SECRET must be set to a secret of at least 32 characters "
        "in backend/.env."
    )

ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 30
OTP_EXPIRE_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
SIMULATED_OTP = "1234"
