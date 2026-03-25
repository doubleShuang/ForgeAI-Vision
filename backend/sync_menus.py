from app.db.session import SessionLocal
from app.models.system import SysMenu

db = SessionLocal()

# 定义所有需要的菜单
# 模型管理可能已经存在，我们先清理一下或者确保它正确
existing_menus = {m.menu_name for m in db.query(SysMenu).all()}

biz_menus = [
    {"name": "模型库管理", "icon": "Menu", "component": "ModelList", "perms": "model:list"},
    {"name": "标注工程", "icon": "Folder", "component": "ProjectList", "perms": "project:list"},
    {"name": "训练管理", "icon": "DataLine", "component": "Training", "perms": "train:list"},
    {"name": "媒体识别", "icon": "VideoCamera", "component": "Inference", "perms": "inference:list"},
    {"name": "识别记录", "icon": "Clock", "component": "History", "perms": "history:list"},
]

for i, m in enumerate(biz_menus):
    # 如果已经有同名菜单，则更新 component 和图标，防止路径不匹配
    target = db.query(SysMenu).filter(SysMenu.menu_name == m["name"]).first()
    if target:
        print(f"Updating menu: {m['name']}")
        target.component = m["component"]
        target.icon = m["icon"]
        target.perms = m["perms"]
    else:
        # 如果不存在，则新增
        print(f"Adding menu: {m['name']}")
        new_menu = SysMenu(
            menu_name=m["name"],
            parent_id=0,
            icon=m["icon"],
            order_num=i+1,
            perms=m["perms"],
            component=m["component"],
            status=1
        )
        db.add(new_menu)

# 确保系统管理也是 parent_id=0 的顶层菜单，且 order_num 在后面
sys_mgmt = db.query(SysMenu).filter(SysMenu.menu_name == "系统管理").first()
if sys_mgmt:
    sys_mgmt.order_num = 100
    sys_mgmt.component = "Layout"

db.commit()
db.close()
print("Menu synchronization completed.")
