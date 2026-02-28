<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <el-menu mode="horizontal" router :default-active="$route.path">
          <el-menu-item index="/models">模型库管理</el-menu-item>
          <el-menu-item index="/projects">标注工程</el-menu-item>
          <el-menu-item index="/annotation">在线标注</el-menu-item>
          <el-menu-item index="/training">训练管理</el-menu-item>
          <el-menu-item index="/inference">媒体识别</el-menu-item>
          <el-menu-item index="/history">识别记录</el-menu-item>
        </el-menu>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<style>
.el-header {
  padding: 0;
}
</style>
