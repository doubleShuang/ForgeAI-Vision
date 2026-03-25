"""
系统管理模块 - 数据库模型定义
包含：用户、角色、部门、字典、菜单、参数配置、操作日志等系统管理所需的数据表模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class SysUser(Base):
    """系统用户表"""
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(64), unique=True, index=True, nullable=False, comment="用户名")
    nickname = Column(String(64), default="", comment="用户昵称")
    email = Column(String(128), default="", comment="邮箱")
    phone = Column(String(20), default="", comment="手机号码")
    dept_id = Column(Integer, default=0, comment="所属部门ID")
    role_id = Column(Integer, default=0, comment="角色ID")
    password = Column(String(128), default="", comment="密码（明文存储，简化处理）")
    status = Column(Integer, default=1, comment="状态：1=正常，0=停用")
    remark = Column(String(500), default="", comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class SysRole(Base):
    """系统角色表"""
    __tablename__ = "sys_role"

    id = Column(Integer, primary_key=True, index=True, comment="角色ID")
    role_name = Column(String(64), nullable=False, comment="角色名称")
    role_key = Column(String(64), unique=True, nullable=False, comment="角色权限字符串")
    sort = Column(Integer, default=0, comment="显示排序")
    status = Column(Integer, default=1, comment="状态：1=正常，0=停用")
    remark = Column(String(500), default="", comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


class SysDept(Base):
    """系统部门表"""
    __tablename__ = "sys_dept"

    id = Column(Integer, primary_key=True, index=True, comment="部门ID")
    parent_id = Column(Integer, default=0, index=True, comment="父部门ID，0表示顶级部门")
    dept_name = Column(String(64), nullable=False, comment="部门名称")
    leader = Column(String(64), default="", comment="负责人")
    phone = Column(String(20), default="", comment="联系电话")
    sort = Column(Integer, default=0, comment="显示排序")
    status = Column(Integer, default=1, comment="状态：1=正常，0=停用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


class SysDict(Base):
    """系统字典表"""
    __tablename__ = "sys_dict"

    id = Column(Integer, primary_key=True, index=True, comment="字典ID")
    dict_name = Column(String(128), nullable=False, comment="字典名称")
    dict_type = Column(String(128), unique=True, nullable=False, comment="字典类型")
    status = Column(Integer, default=1, comment="状态：1=正常，0=停用")
    remark = Column(String(500), default="", comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


class SysMenu(Base):
    """系统菜单表"""
    __tablename__ = "sys_menu"

    id = Column(Integer, primary_key=True, index=True, comment="菜单ID")
    parent_id = Column(Integer, default=0, index=True, comment="父菜单ID，0表示顶级菜单")
    menu_name = Column(String(64), nullable=False, comment="菜单名称")
    icon = Column(String(64), default="", comment="菜单图标")
    order_num = Column(Integer, default=0, comment="显示排序")
    perms = Column(String(128), default="", comment="权限标识")
    component = Column(String(255), default="", comment="组件路径")
    status = Column(Integer, default=1, comment="状态：1=正常，0=停用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


class SysConfig(Base):
    """系统参数配置表"""
    __tablename__ = "sys_config"

    id = Column(Integer, primary_key=True, index=True, comment="参数ID")
    config_name = Column(String(128), nullable=False, comment="参数名称")
    config_key = Column(String(128), unique=True, nullable=False, comment="参数键名")
    config_value = Column(String(500), default="", comment="参数键值")
    config_type = Column(String(1), default="N", comment="系统内置：Y=是，N=否")
    remark = Column(String(500), default="", comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


class SysLog(Base):
    """系统操作日志表"""
    __tablename__ = "sys_log"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    module = Column(String(64), default="", comment="系统模块")
    type = Column(String(20), default="", comment="操作类型：INSERT/UPDATE/DELETE/SELECT等")
    operator = Column(String(64), default="", comment="操作人员")
    ip = Column(String(64), default="", comment="操作IP地址")
    location = Column(String(128), default="", comment="操作地点")
    status = Column(Integer, default=1, comment="操作状态：1=成功，0=失败")
    detail = Column(Text, default="", comment="操作详情")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="操作时间")
