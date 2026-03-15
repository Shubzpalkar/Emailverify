from passlib.context import CryptContext
import sys

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    h = pwd_context.hash("admin")
    print(f"Hash success: {h}")
    verify = pwd_context.verify("admin", h)
    print(f"Verify success: {verify}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
