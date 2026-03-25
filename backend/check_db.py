from app.db.session import SessionLocal
from app.models.system import SysMenu, SysUser

db = SessionLocal()
print(f"Users: {[u.username for u in db.query(SysUser).all()]}")
print(f"Menus: {[m.menu_name for m in db.query(SysMenu).all()]}")
db.close()
