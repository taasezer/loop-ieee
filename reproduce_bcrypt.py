from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    hash = pwd_context.hash("password123")
    print(f"Hash success: {hash}")
    verify = pwd_context.verify("password123", hash)
    print(f"Verify success: {verify}")
except Exception as e:
    print(f"Error: {e}")
