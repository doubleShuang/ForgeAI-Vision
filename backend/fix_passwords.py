import bcrypt
from app.db.session import SessionLocal
from app.models.system import SysUser

def get_password_hash(password: str) -> str:
    # Use bcrypt directly to avoid passlib version check issues
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

db = SessionLocal()
users = db.query(SysUser).all()
for u in users:
    if not u.password.startswith("$2b$"):
        print(f"Hashing password for user: {u.username}")
        u.password = get_password_hash(u.password)
db.commit()
db.close()
print("All passwords checked and hashed using direct bcrypt.")
