from app.db.session import SessionLocal
from app.models.system import SysMenu

db = SessionLocal()

# 定义映射关系: 菜单名称 -> 实际组件名
updates = {
    "模型库管理": "ModelList",
    "标注工程": "ProjectList",
    "训练管理": "Training",
    "媒体识别": "Inference",
    "识别记录": "History"
}

for name, component in updates.items():
    menu = db.query(SysMenu).filter(SysMenu.menu_name == name).first()
    if menu:
        print(f"Updating menu {name}: {menu.component} -> {component}")
        menu.component = component

db.commit()
db.close()
print("Menu component mapping updated.")
