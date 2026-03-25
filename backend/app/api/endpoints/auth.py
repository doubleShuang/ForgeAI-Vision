from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.system import SysUser, SysRole, SysMenu

router = APIRouter()

@router.post("/login")
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 兼容的 token 登录接口，获取 access token 以供后续请求使用。
    """
    user = db.query(SysUser).filter(SysUser.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    elif user.status != 1:
        raise HTTPException(status_code=400, detail="用户已被停用")
        
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/info")
def get_user_info(
    db: Session = Depends(deps.get_db),
    current_user: SysUser = Depends(deps.get_current_user)
) -> Any:
    """
    获取当前登录用户信息、角色和权限菜单路由。
    """
    # 获取角色信息
    roles = ["visitor"]
    role = db.query(SysRole).filter(SysRole.id == current_user.role_id).first()
    if role:
        roles = [role.role_key]
        
    # 获取菜单信息 (简化逻辑：admin获取所有，其余根据需要过滤。这里假定目前普通用户直接给业务菜单，不给系统菜单)
    # 真实企业项目一般会建立 RoleMenu 表连接查询，本系统直接用约定和 perms/component 匹配
    is_admin = "admin" in roles
    
    if is_admin:
        menus = db.query(SysMenu).filter(SysMenu.status == 1).order_by(SysMenu.order_num).all()
    else:
        # 非管理员（普通用户与访客），只下发不带 system: 开头权限的非系统菜单，即业务功能菜单
        menus = db.query(SysMenu).filter(SysMenu.status == 1, ~SysMenu.component.like('system/%')).order_by(SysMenu.order_num).all()

    # 构建动态路由所需的菜单树结构
    def build_tree(pid=0):
        result = []
        for m in menus:
            if m.parent_id == pid:
                node = {
                    "id": m.id,
                    "name": m.menu_name,
                    "path": f"/{m.component}" if m.component and not m.component.startswith('Layout') else "",
                    "component": m.component,
                    "meta": {
                        "title": m.menu_name,
                        "icon": m.icon,
                        "roles": ["admin"] if m.component and m.component.startswith('system/') else ["admin", "common", "guest"]
                    },
                    "children": build_tree(m.id)
                }
                # 若是没有children的目录（Layout），过滤掉？保留以便展开
                if node["children"]:
                    result.append(node)
                elif m.component != "Layout":
                    result.append(node)
        return result

    menu_tree = build_tree(0)

    return {
        "code": 200,
        "msg": "获取成功",
        "data": {
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "nickname": current_user.nickname,
                "avatar": "https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png",
                "roles": roles
            },
            "menus": menu_tree
        }
    }
