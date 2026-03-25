import os
import shutil
import requests
import json
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.model import Base, Model  # 导入基础模型
from app.models.system import SysUser, SysRole, SysDept, SysDict, SysMenu, SysConfig, SysLog  # 导入系统管理模型

def init_db(db: Session):
    # 创建所有数据库表
    Base.metadata.create_all(bind=engine)

    # ===================== 1. 官方 YOLOv8 模型（通用目标检测） =====================
    coco_subset = {
        "0": "Person (人)",
        "1": "Bicycle (自行车)",
        "2": "Car (汽车)",
        "3": "Motorcycle (摩托车)",
        "5": "Bus (公交车)",
        "7": "Truck (卡车)"
    }
    coco_subset_json = json.dumps(coco_subset)

    official_models = [
        {"name": "yolo26n", "type": "detector", "accuracy": 0.37, "file_path": "yolov8n.pt", "desc": "Fastest, lightweight", "classes": coco_subset_json},
    ]

    for m_data in official_models:
        existing = db.query(Model).filter(Model.name == m_data["name"]).first()
        if not existing:
            print(f"Registering official model: {m_data['name']}")
            model = Model(
                name=m_data["name"],
                type=m_data["type"],
                accuracy=m_data["accuracy"],
                file_path=m_data["file_path"],
                description=m_data["desc"],
                classes=m_data["classes"]
            )
            db.add(model)
        else:
            existing.classes = m_data["classes"]
            
        if not os.path.exists(m_data["file_path"]):
            print(f"Note: {m_data['file_path']} will be downloaded by Ultralytics on first use.")

    # ===================== 2. 安全帽检测模型 =====================
    helmet_classes = {
        "0": "hat (安全帽)",
        "1": "person (人)"
    }
    helmet_classes_json = json.dumps(helmet_classes)
    
    base_path = os.path.join("models", "safety_helmet")
    
    helmet_models = [
    ]

    for m_data in helmet_models:
        existing = db.query(Model).filter(Model.name == m_data["name"]).first()
        if not existing:
            print(f"Registering helmet model: {m_data['name']}")
            model = Model(
                name=m_data["name"],
                type=m_data["type"],
                accuracy=m_data["accuracy"],
                file_path=m_data["file_path"],
                description=m_data["desc"],
                classes=m_data["classes"]
            )
            db.add(model)
        else:
            existing.classes = m_data["classes"]

    db.commit()

    # ===================== 3. 系统管理初始数据 =====================
    _init_system_data(db)


def _init_system_data(db: Session):
    """初始化系统管理模块的默认数据"""

    # ----- 角色 -----
    if db.query(SysRole).count() == 0:
        print("初始化默认角色...")
        roles = [
            SysRole(role_name="超级管理员", role_key="admin", sort=1, status=1, remark="拥有所有权限"),
            SysRole(role_name="普通用户", role_key="common", sort=2, status=1, remark="普通操作权限"),
            SysRole(role_name="访客", role_key="guest", sort=3, status=1, remark="仅查看权限"),
        ]
        db.add_all(roles)
        db.commit()

    # ----- 部门 -----
    if db.query(SysDept).count() == 0:
        print("初始化默认部门...")
        # 顶级部门
        root_dept = SysDept(dept_name="ForgeAI 集团总部", parent_id=0, leader="Admin", phone="13800138000", sort=1, status=1)
        db.add(root_dept)
        db.commit()
        db.refresh(root_dept)
        # 子部门
        sub_depts = [
            SysDept(dept_name="研发中心", parent_id=root_dept.id, leader="张三", phone="13800138001", sort=1, status=1),
            SysDept(dept_name="运营部门", parent_id=root_dept.id, leader="李四", phone="13800138002", sort=2, status=1),
            SysDept(dept_name="测试部门", parent_id=root_dept.id, leader="王五", phone="13800138003", sort=3, status=1),
        ]
        db.add_all(sub_depts)
        db.commit()

    # ----- 用户 -----
    if db.query(SysUser).count() == 0:
        print("初始化默认用户...")
        from app.core.security import get_password_hash
        # 获取角色和部门ID
        admin_role = db.query(SysRole).filter(SysRole.role_key == "admin").first()
        common_role = db.query(SysRole).filter(SysRole.role_key == "common").first()
        guest_role = db.query(SysRole).filter(SysRole.role_key == "guest").first()
        dev_dept = db.query(SysDept).filter(SysDept.dept_name == "研发中心").first()
        ops_dept = db.query(SysDept).filter(SysDept.dept_name == "运营部门").first()
        test_dept = db.query(SysDept).filter(SysDept.dept_name == "测试部门").first()

        users = [
            SysUser(username="admin", nickname="超级管理员", email="admin@forgeai.com", phone="13800138000",
                    dept_id=dev_dept.id if dev_dept else 0, role_id=admin_role.id if admin_role else 0,
                    password=get_password_hash("admin123"), status=1),
            SysUser(username="editor", nickname="内容编辑", email="editor@forgeai.com", phone="13800138010",
                    dept_id=ops_dept.id if ops_dept else 0, role_id=common_role.id if common_role else 0,
                    password=get_password_hash("123456"), status=1),
            SysUser(username="test", nickname="测试账户", email="test@forgeai.com", phone="13800138020",
                    dept_id=test_dept.id if test_dept else 0, role_id=guest_role.id if guest_role else 0,
                    password=get_password_hash("123456"), status=0),
        ]
        db.add_all(users)
        db.commit()

    # ----- 字典 -----
    if db.query(SysDict).count() == 0:
        print("初始化默认字典...")
        dicts = [
            SysDict(dict_name="用户性别", dict_type="sys_user_sex", status=1, remark="用户性别列表"),
            SysDict(dict_name="系统状态", dict_type="sys_normal_disable", status=1, remark="系统开关状态"),
            SysDict(dict_name="任务状态", dict_type="sys_job_status", status=1, remark="异步任务运行状态"),
        ]
        db.add_all(dicts)
        db.commit()

    # ----- 菜单 -----
    if db.query(SysMenu).count() == 0:
        print("初始化默认菜单 (包含系统与业务菜单)...")
        # 0. 业务菜单 (分配给所有用户，非系统组件)
        biz_menus = [
            SysMenu(menu_name="模型库管理", parent_id=0, icon="Menu", order_num=1, perms="model:list", component="models", status=1),
            SysMenu(menu_name="标注工程", parent_id=0, icon="Folder", order_num=2, perms="project:list", component="projects", status=1),
            SysMenu(menu_name="训练管理", parent_id=0, icon="DataLine", order_num=3, perms="train:list", component="training", status=1),
            SysMenu(menu_name="媒体识别", parent_id=0, icon="VideoCamera", order_num=4, perms="inference:list", component="inference", status=1),
            SysMenu(menu_name="识别记录", parent_id=0, icon="Clock", order_num=5, perms="history:list", component="history", status=1),
        ]
        db.add_all(biz_menus)
        db.commit()

        # 1. 系统管理一级菜单
        sys_menu = SysMenu(menu_name="系统管理", parent_id=0, icon="Setting", order_num=6, perms="", component="Layout", status=1)
        db.add(sys_menu)
        db.commit()
        db.refresh(sys_menu)
        
        # 2. 系统管理子菜单
        sub_menus = [
            SysMenu(menu_name="用户管理", parent_id=sys_menu.id, icon="User", order_num=1, perms="system:user:list", component="system/user/index", status=1),
            SysMenu(menu_name="角色管理", parent_id=sys_menu.id, icon="Avatar", order_num=2, perms="system:role:list", component="system/role/index", status=1),
            SysMenu(menu_name="部门管理", parent_id=sys_menu.id, icon="OfficeBuilding", order_num=3, perms="system:dept:list", component="system/dept/index", status=1),
            SysMenu(menu_name="字典管理", parent_id=sys_menu.id, icon="Collection", order_num=4, perms="system:dict:list", component="system/dict/index", status=1),
            SysMenu(menu_name="菜单管理", parent_id=sys_menu.id, icon="Menu", order_num=5, perms="system:menu:list", component="system/menu/index", status=1),
            SysMenu(menu_name="参数配置", parent_id=sys_menu.id, icon="Tools", order_num=6, perms="system:config:list", component="system/config/index", status=1),
            SysMenu(menu_name="日志管理", parent_id=sys_menu.id, icon="Notebook", order_num=7, perms="system:log:list", component="system/log/index", status=1),
        ]
        db.add_all(sub_menus)
        db.commit()

    # ----- 参数配置 -----
    if db.query(SysConfig).count() == 0:
        print("初始化默认参数配置...")
        configs = [
            SysConfig(config_name="主框架页-默认皮肤样式", config_key="sys.index.skinName", config_value="skin-blue", config_type="Y", remark="内置蓝色皮肤"),
            SysConfig(config_name="系统名称", config_key="sys.name", config_value="ForgeAI Vision Base", config_type="N", remark="全局系统名称"),
        ]
        db.add_all(configs)
        db.commit()

    print("系统管理初始数据初始化完成。")


if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
    print("Database initialization completed.")
