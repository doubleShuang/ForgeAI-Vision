"""
系统管理模块 - API路由
包含用户、角色、部门、字典、菜单、参数配置、操作日志的CRUD接口
所有接口仅使用 GET 和 POST，删除使用 POST /xxx/remove，更新使用 POST /xxx/update
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.api.deps import get_current_user
from app.db.session import SessionLocal
from app.models.system import SysUser, SysRole, SysDept, SysDict, SysMenu, SysConfig, SysLog

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===================== 通用响应模型 =====================

class PageResult(BaseModel):
    """分页结果通用模型"""
    list: list  # 数据列表
    total: int  # 总记录数

    class Config:
        from_attributes = True


# ===================== 用户管理 =====================

class UserForm(BaseModel):
    """用户表单数据模型"""
    id: Optional[int] = None
    username: str = ""
    nickname: str = ""
    email: str = ""
    phone: str = ""
    dept_id: int = 0
    role_id: int = 0
    password: str = ""
    status: int = 1
    remark: str = ""


class UserRemoveForm(BaseModel):
    """用户删除表单（支持批量）"""
    ids: List[int]


@router.get("/users/list")
def get_user_list(
    keyword: str = Query("", description="搜索关键词（用户名/昵称）"),
    status: Optional[int] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取用户列表（分页 + 搜索）"""
    query = db.query(SysUser)
    # 关键词搜索：匹配用户名或昵称
    if keyword:
        query = query.filter(
            or_(SysUser.username.like(f"%{keyword}%"), SysUser.nickname.like(f"%{keyword}%"))
        )
    # 状态筛选
    if status is not None:
        query = query.filter(SysUser.status == status)
    total = query.count()
    items = query.order_by(SysUser.id).offset((page - 1) * page_size).limit(page_size).all()

    # 查询关联的部门名称和角色名称
    result = []
    for user in items:
        dept = db.query(SysDept).filter(SysDept.id == user.dept_id).first()
        role = db.query(SysRole).filter(SysRole.id == user.role_id).first()
        result.append({
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "phone": user.phone,
            "dept_id": user.dept_id,
            "department": dept.dept_name if dept else "",
            "role_id": user.role_id,
            "role": role.role_name if role else "",
            "status": user.status,
            "remark": user.remark,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else ""
        })
    return {"list": result, "total": total}


@router.post("/users/add")
def add_user(form: UserForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """新增用户"""
    # 检查用户名是否已存在
    existing = db.query(SysUser).filter(SysUser.username == form.username).first()
    if existing:
        return {"code": 400, "msg": "用户名已存在"}
    user = SysUser(
        username=form.username,
        nickname=form.nickname,
        email=form.email,
        phone=form.phone,
        dept_id=form.dept_id,
        role_id=form.role_id,
        password=form.password or "123456",
        status=form.status,
        remark=form.remark
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # 记录操作日志
    from app.core.security import get_password_hash
    if form.password:
        user.password = get_password_hash(form.password)
        
    _add_log(db, "用户管理", "INSERT", current_user.username, f"新增用户: {form.username}")
    return {"code": 200, "msg": "新增成功"}


@router.post("/users/update")
def update_user(form: UserForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """更新用户信息"""
    user = db.query(SysUser).filter(SysUser.id == form.id).first()
    if not user:
        return {"code": 404, "msg": "用户不存在"}
    user.nickname = form.nickname
    user.email = form.email
    user.phone = form.phone
    user.dept_id = form.dept_id
    user.role_id = form.role_id
    user.status = form.status
    user.remark = form.remark
    if form.password:
        from app.core.security import get_password_hash
        user.password = get_password_hash(form.password)
    db.commit()
    _add_log(db, "用户管理", "UPDATE", current_user.username, f"更新用户: {user.username}")
    return {"code": 200, "msg": "更新成功"}


@router.post("/users/remove")
def remove_users(form: UserRemoveForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """批量删除用户"""
    db.query(SysUser).filter(SysUser.id.in_(form.ids)).delete(synchronize_session=False)
    db.commit()
    _add_log(db, "用户管理", "DELETE", current_user.username, f"删除用户ID: {form.ids}")
    return {"code": 200, "msg": "删除成功"}


# ===================== 角色管理 =====================

class RoleForm(BaseModel):
    """角色表单数据模型"""
    id: Optional[int] = None
    role_name: str = ""
    role_key: str = ""
    sort: int = 0
    status: int = 1
    remark: str = ""


class RoleRemoveForm(BaseModel):
    """角色删除表单"""
    ids: List[int]


@router.get("/roles/list")
def get_role_list(
    keyword: str = Query("", description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取角色列表（分页 + 搜索）"""
    query = db.query(SysRole)
    if keyword:
        query = query.filter(
            or_(SysRole.role_name.like(f"%{keyword}%"), SysRole.role_key.like(f"%{keyword}%"))
        )
    total = query.count()
    items = query.order_by(SysRole.sort).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": r.id, "role_name": r.role_name, "role_key": r.role_key,
        "sort": r.sort, "status": r.status, "remark": r.remark,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
    } for r in items]
    return {"list": result, "total": total}


@router.post("/roles/add")
def add_role(form: RoleForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """新增角色"""
    existing = db.query(SysRole).filter(SysRole.role_key == form.role_key).first()
    if existing:
        return {"code": 400, "msg": "角色标识已存在"}
    role = SysRole(
        role_name=form.role_name, role_key=form.role_key,
        sort=form.sort, status=form.status, remark=form.remark
    )
    db.add(role)
    db.commit()
    _add_log(db, "角色管理", "INSERT", current_user.username, f"新增角色: {form.role_name}")
    return {"code": 200, "msg": "新增成功"}


@router.post("/roles/update")
def update_role(form: RoleForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """更新角色信息"""
    role = db.query(SysRole).filter(SysRole.id == form.id).first()
    if not role:
        return {"code": 404, "msg": "角色不存在"}
    role.role_name = form.role_name
    role.role_key = form.role_key
    role.sort = form.sort
    role.status = form.status
    role.remark = form.remark
    db.commit()
    _add_log(db, "角色管理", "UPDATE", current_user.username, f"更新角色: {form.role_name}")
    return {"code": 200, "msg": "更新成功"}


@router.post("/roles/remove")
def remove_roles(form: RoleRemoveForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """删除角色"""
    db.query(SysRole).filter(SysRole.id.in_(form.ids)).delete(synchronize_session=False)
    db.commit()
    _add_log(db, "角色管理", "DELETE", current_user.username, f"删除角色ID: {form.ids}")
    return {"code": 200, "msg": "删除成功"}


# ===================== 部门管理 =====================

class DeptForm(BaseModel):
    """部门表单数据模型"""
    id: Optional[int] = None
    parent_id: int = 0
    dept_name: str = ""
    leader: str = ""
    phone: str = ""
    sort: int = 0
    status: int = 1


class DeptRemoveForm(BaseModel):
    """部门删除表单"""
    ids: List[int]


def _build_dept_tree(depts, parent_id=0):
    """递归构建部门树形结构"""
    tree = []
    for dept in depts:
        if dept.parent_id == parent_id:
            children = _build_dept_tree(depts, dept.id)
            node = {
                "id": dept.id, "parent_id": dept.parent_id,
                "dept_name": dept.dept_name, "leader": dept.leader,
                "phone": dept.phone, "sort": dept.sort, "status": dept.status,
                "created_at": dept.created_at.strftime("%Y-%m-%d %H:%M:%S") if dept.created_at else ""
            }
            if children:
                node["children"] = children
            tree.append(node)
    # 按排序字段排列
    tree.sort(key=lambda x: x["sort"])
    return tree


@router.get("/depts/list")
def get_dept_list(
    keyword: str = Query("", description="搜索部门名称"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取部门树形列表"""
    query = db.query(SysDept)
    if keyword:
        query = query.filter(SysDept.dept_name.like(f"%{keyword}%"))
    all_depts = query.all()
    tree = _build_dept_tree(all_depts)
    return {"list": tree, "total": len(all_depts)}


@router.post("/depts/add")
def add_dept(form: DeptForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """新增部门"""
    dept = SysDept(
        parent_id=form.parent_id, dept_name=form.dept_name,
        leader=form.leader, phone=form.phone, sort=form.sort, status=form.status
    )
    db.add(dept)
    db.commit()
    _add_log(db, "部门管理", "INSERT", current_user.username, f"新增部门: {form.dept_name}")
    return {"code": 200, "msg": "新增成功"}


@router.post("/depts/update")
def update_dept(form: DeptForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """更新部门信息"""
    dept = db.query(SysDept).filter(SysDept.id == form.id).first()
    if not dept:
        return {"code": 404, "msg": "部门不存在"}
    dept.parent_id = form.parent_id
    dept.dept_name = form.dept_name
    dept.leader = form.leader
    dept.phone = form.phone
    dept.sort = form.sort
    dept.status = form.status
    db.commit()
    _add_log(db, "部门管理", "UPDATE", current_user.username, f"更新部门: {form.dept_name}")
    return {"code": 200, "msg": "更新成功"}


@router.post("/depts/remove")
def remove_depts(form: DeptRemoveForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """删除部门"""
    db.query(SysDept).filter(SysDept.id.in_(form.ids)).delete(synchronize_session=False)
    db.commit()
    _add_log(db, "部门管理", "DELETE", current_user.username, f"删除部门ID: {form.ids}")
    return {"code": 200, "msg": "删除成功"}


# ===================== 字典管理 =====================

class DictForm(BaseModel):
    """字典表单数据模型"""
    id: Optional[int] = None
    dict_name: str = ""
    dict_type: str = ""
    status: int = 1
    remark: str = ""


class DictRemoveForm(BaseModel):
    """字典删除表单"""
    ids: List[int]


@router.get("/dicts/list")
def get_dict_list(
    keyword: str = Query("", description="搜索字典名称/类型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取字典列表（分页 + 搜索）"""
    query = db.query(SysDict)
    if keyword:
        query = query.filter(
            or_(SysDict.dict_name.like(f"%{keyword}%"), SysDict.dict_type.like(f"%{keyword}%"))
        )
    total = query.count()
    items = query.order_by(SysDict.id).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": d.id, "dict_name": d.dict_name, "dict_type": d.dict_type,
        "status": d.status, "remark": d.remark,
        "created_at": d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else ""
    } for d in items]
    return {"list": result, "total": total}


@router.post("/dicts/add")
def add_dict(form: DictForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """新增字典"""
    existing = db.query(SysDict).filter(SysDict.dict_type == form.dict_type).first()
    if existing:
        return {"code": 400, "msg": "字典类型已存在"}
    d = SysDict(
        dict_name=form.dict_name, dict_type=form.dict_type,
        status=form.status, remark=form.remark
    )
    db.add(d)
    db.commit()
    _add_log(db, "字典管理", "INSERT", current_user.username, f"新增字典: {form.dict_name}")
    return {"code": 200, "msg": "新增成功"}


@router.post("/dicts/update")
def update_dict(form: DictForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """更新字典"""
    d = db.query(SysDict).filter(SysDict.id == form.id).first()
    if not d:
        return {"code": 404, "msg": "字典不存在"}
    d.dict_name = form.dict_name
    d.dict_type = form.dict_type
    d.status = form.status
    d.remark = form.remark
    db.commit()
    _add_log(db, "字典管理", "UPDATE", current_user.username, f"更新字典: {form.dict_name}")
    return {"code": 200, "msg": "更新成功"}


@router.post("/dicts/remove")
def remove_dicts(form: DictRemoveForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """删除字典"""
    db.query(SysDict).filter(SysDict.id.in_(form.ids)).delete(synchronize_session=False)
    db.commit()
    _add_log(db, "字典管理", "DELETE", current_user.username, f"删除字典ID: {form.ids}")
    return {"code": 200, "msg": "删除成功"}


# ===================== 菜单管理 =====================

class MenuForm(BaseModel):
    """菜单表单数据模型"""
    id: Optional[int] = None
    parent_id: int = 0
    menu_name: str = ""
    icon: str = ""
    order_num: int = 0
    perms: str = ""
    component: str = ""
    status: int = 1


class MenuRemoveForm(BaseModel):
    """菜单删除表单"""
    ids: List[int]


def _build_menu_tree(menus, parent_id=0):
    """递归构建菜单树形结构"""
    tree = []
    for menu in menus:
        if menu.parent_id == parent_id:
            children = _build_menu_tree(menus, menu.id)
            node = {
                "id": menu.id, "parent_id": menu.parent_id,
                "menu_name": menu.menu_name, "icon": menu.icon,
                "order_num": menu.order_num, "perms": menu.perms,
                "component": menu.component, "status": menu.status,
                "created_at": menu.created_at.strftime("%Y-%m-%d %H:%M:%S") if menu.created_at else ""
            }
            if children:
                node["children"] = children
            tree.append(node)
    tree.sort(key=lambda x: x["order_num"])
    return tree


@router.get("/menus/list")
def get_menu_list(
    keyword: str = Query("", description="搜索菜单名称"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取菜单树形列表"""
    query = db.query(SysMenu)
    if keyword:
        query = query.filter(SysMenu.menu_name.like(f"%{keyword}%"))
    all_menus = query.all()
    tree = _build_menu_tree(all_menus)
    return {"list": tree, "total": len(all_menus)}


@router.post("/menus/add")
def add_menu(form: MenuForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """新增菜单"""
    menu = SysMenu(
        parent_id=form.parent_id, menu_name=form.menu_name, icon=form.icon,
        order_num=form.order_num, perms=form.perms, component=form.component, status=form.status
    )
    db.add(menu)
    db.commit()
    _add_log(db, "菜单管理", "INSERT", current_user.username, f"新增菜单: {form.menu_name}")
    return {"code": 200, "msg": "新增成功"}


@router.post("/menus/update")
def update_menu(form: MenuForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """更新菜单"""
    menu = db.query(SysMenu).filter(SysMenu.id == form.id).first()
    if not menu:
        return {"code": 404, "msg": "菜单不存在"}
    menu.parent_id = form.parent_id
    menu.menu_name = form.menu_name
    menu.icon = form.icon
    menu.order_num = form.order_num
    menu.perms = form.perms
    menu.component = form.component
    menu.status = form.status
    db.commit()
    _add_log(db, "菜单管理", "UPDATE", current_user.username, f"更新菜单: {form.menu_name}")
    return {"code": 200, "msg": "更新成功"}


@router.post("/menus/remove")
def remove_menus(form: MenuRemoveForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """删除菜单"""
    db.query(SysMenu).filter(SysMenu.id.in_(form.ids)).delete(synchronize_session=False)
    db.commit()
    _add_log(db, "菜单管理", "DELETE", current_user.username, f"删除菜单ID: {form.ids}")
    return {"code": 200, "msg": "删除成功"}


# ===================== 参数配置管理 =====================

class ConfigForm(BaseModel):
    """参数配置表单数据模型"""
    id: Optional[int] = None
    config_name: str = ""
    config_key: str = ""
    config_value: str = ""
    config_type: str = "N"
    remark: str = ""


class ConfigRemoveForm(BaseModel):
    """参数配置删除表单"""
    ids: List[int]


@router.get("/configs/list")
def get_config_list(
    keyword: str = Query("", description="搜索参数名称/键名"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取参数配置列表（分页 + 搜索）"""
    query = db.query(SysConfig)
    if keyword:
        query = query.filter(
            or_(SysConfig.config_name.like(f"%{keyword}%"), SysConfig.config_key.like(f"%{keyword}%"))
        )
    total = query.count()
    items = query.order_by(SysConfig.id).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": c.id, "config_name": c.config_name, "config_key": c.config_key,
        "config_value": c.config_value, "config_type": c.config_type,
        "remark": c.remark,
        "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else ""
    } for c in items]
    return {"list": result, "total": total}


@router.post("/configs/add")
def add_config(form: ConfigForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """新增参数配置"""
    existing = db.query(SysConfig).filter(SysConfig.config_key == form.config_key).first()
    if existing:
        return {"code": 400, "msg": "参数键名已存在"}
    c = SysConfig(
        config_name=form.config_name, config_key=form.config_key,
        config_value=form.config_value, config_type=form.config_type, remark=form.remark
    )
    db.add(c)
    db.commit()
    _add_log(db, "参数配置", "INSERT", current_user.username, f"新增参数: {form.config_name}")
    return {"code": 200, "msg": "新增成功"}


@router.post("/configs/update")
def update_config(form: ConfigForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """更新参数配置"""
    c = db.query(SysConfig).filter(SysConfig.id == form.id).first()
    if not c:
        return {"code": 404, "msg": "参数不存在"}
    c.config_name = form.config_name
    c.config_key = form.config_key
    c.config_value = form.config_value
    c.config_type = form.config_type
    c.remark = form.remark
    db.commit()
    _add_log(db, "参数配置", "UPDATE", current_user.username, f"更新参数: {form.config_name}")
    return {"code": 200, "msg": "更新成功"}


@router.post("/configs/remove")
def remove_configs(form: ConfigRemoveForm, db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """删除参数配置"""
    db.query(SysConfig).filter(SysConfig.id.in_(form.ids)).delete(synchronize_session=False)
    db.commit()
    _add_log(db, "参数配置", "DELETE", current_user.username, f"删除参数ID: {form.ids}")
    return {"code": 200, "msg": "删除成功"}


# ===================== 日志管理 =====================

@router.get("/logs/list")
def get_log_list(
    keyword: str = Query("", description="搜索模块/操作人员"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取操作日志列表（分页 + 搜索 + 日期筛选）"""
    query = db.query(SysLog)
    if keyword:
        query = query.filter(
            or_(SysLog.module.like(f"%{keyword}%"), SysLog.operator.like(f"%{keyword}%"))
        )
    # 日期范围筛选
    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(SysLog.created_at >= sd)
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(SysLog.created_at <= ed)
        except ValueError:
            pass
    total = query.count()
    items = query.order_by(SysLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": l.id, "module": l.module, "type": l.type,
        "operator": l.operator, "ip": l.ip, "location": l.location,
        "status": l.status, "detail": l.detail,
        "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else ""
    } for l in items]
    return {"list": result, "total": total}


@router.post("/logs/clear")
def clear_logs(db: Session = Depends(get_db), current_user: SysUser = Depends(get_current_user)):
    """清空所有操作日志"""
    db.query(SysLog).delete()
    db.commit()
    return {"code": 200, "msg": "日志已清空"}


# ===================== 辅助函数 =====================

def _add_log(db: Session, module: str, op_type: str, operator: str, detail: str):
    """
    写入操作日志的工具函数
    在各CRUD操作中调用，自动记录操作模块、类型、操作人和详情
    """
    log = SysLog(
        module=module, type=op_type, operator=operator,
        ip="127.0.0.1", location="内网IP", status=1, detail=detail
    )
    db.add(log)
    db.commit()
