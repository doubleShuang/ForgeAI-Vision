import request from '@/utils/request'

/**
 * 登录
 */
export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data,
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    transformRequest: [function (data) {
        let ret = ''
        for (let it in data) {
            ret += encodeURIComponent(it) + '=' + encodeURIComponent(data[it]) + '&'
        }
        ret = ret.substring(0, ret.lastIndexOf('&'))
        return ret
    }]
  })
}

/**
 * 获取用户信息和菜单
 */
export function getInfo() {
  return request({
    url: '/auth/info',
    method: 'get'
  })
}

// ===================== 用户管理 =====================
export function getUserList(params) { return request.get('/system/users/list', { params }) }
export function addUser(data) { return request.post('/system/users/add', data) }
export function updateUser(data) { return request.post('/system/users/update', data) }
export function removeUsers(ids) { return request.post('/system/users/remove', { ids: Array.isArray(ids) ? ids : [ids] }) }

// ===================== 角色管理 =====================
export function getRoleList(params) { return request.get('/system/roles/list', { params }) }
export function addRole(data) { return request.post('/system/roles/add', data) }
export function updateRole(data) { return request.post('/system/roles/update', data) }
export function removeRoles(ids) { return request.post('/system/roles/remove', { ids: Array.isArray(ids) ? ids : [ids] }) }

// ===================== 部门管理 =====================
export function getDeptList(params) { return request.get('/system/depts/list', { params }) }
export function addDept(data) { return request.post('/system/depts/add', data) }
export function updateDept(data) { return request.post('/system/depts/update', data) }
export function removeDepts(ids) { return request.post('/system/depts/remove', { ids: Array.isArray(ids) ? ids : [ids] }) }

// ===================== 字典管理 =====================
export function getDictList(params) { return request.get('/system/dicts/list', { params }) }
export function addDict(data) { return request.post('/system/dicts/add', data) }
export function updateDict(data) { return request.post('/system/dicts/update', data) }
export function removeDicts(ids) { return request.post('/system/dicts/remove', { ids: Array.isArray(ids) ? ids : [ids] }) }

// ===================== 菜单管理 =====================
export function getMenuList(params) { return request.get('/system/menus/list', { params }) }
export function addMenu(data) { return request.post('/system/menus/add', data) }
export function updateMenu(data) { return request.post('/system/menus/update', data) }
export function removeMenus(ids) { return request.post('/system/menus/remove', { ids: Array.isArray(ids) ? ids : [ids] }) }

// ===================== 参数配置 =====================
export function getConfigList(params) { return request.get('/system/configs/list', { params }) }
export function addConfig(data) { return request.post('/system/configs/add', data) }
export function updateConfig(data) { return request.post('/system/configs/update', data) }
export function removeConfigs(ids) { return request.post('/system/configs/remove', { ids: Array.isArray(ids) ? ids : [ids] }) }

// ===================== 日志管理 =====================
export function getLogList(params) { return request.get('/system/logs/list', { params }) }
export function clearLogs() { return request.post('/system/logs/clear') }

export default {
    login,
    getInfo,
    getUserList, addUser, updateUser, removeUsers,
    getRoleList, addRole, updateRole, removeRoles,
    getDeptList, addDept, updateDept, removeDepts,
    getDictList, addDict, updateDict, removeDicts,
    getMenuList, addMenu, updateMenu, removeMenus,
    getConfigList, addConfig, updateConfig, removeConfigs,
    getLogList, clearLogs
}
