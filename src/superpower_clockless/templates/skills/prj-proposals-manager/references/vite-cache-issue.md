# 前端 build 后 bundle 不更新

> **发现日期**: 2026-05-14

## 问题描述

修改了源代码文件（如 `.jsx`、`.ts`、`.tsx`）后，运行 `npm run build` 但生成的 `dist/assets/*.js` 文件没有变化。浏览器访问时仍显示旧版本。

## 症状

```bash
# 1. 修改了源文件
$ grep onEditProject src/
src/pages/SettingsPage.jsx:  const handleEditProject = (project) => {

# 2. 但 dist 中找不到这个符号
$ grep onEditProject dist/assets/*.js
# (无输出)

# 3. 源文件确实有，但 bundle 没有
```

## 根因

Vite 的持久化缓存没有因源文件改变而失效。具体原因可能是：

1. **缓存键冲突**：Vite 使用内容哈希作为缓存键，但如果构建配置中的某些全局状态（如 `define` 注入的版本常量）没有变化，Vite 可能跳过重新构建
2. **文件系统时间戳问题**：在某些情况下（特别是 WSL 与 Windows 双系统），文件时间戳可能不一致
3. **node_modules/.vite 缓存目录**保留了旧的构建结果

## 解决方案

```bash
# 清除所有缓存后重新构建
rm -rf node_modules/.cache
rm -rf node_modules/.vite
npm run build
```

或者更彻底地：

```bash
# 删除 node_modules 外的所有缓存
rm -rf node_modules/.cache
rm -rf dist
npm run build
```

## 预防措施

在 `vite.config.js` 中确保缓存配置正确：

```javascript
// vite.config.js
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    // 确保不使用缓存
    cache: false,
  },
  // 或者明确指定 output 目录
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  }
})
```

## 相关项目

- `prj-proposals-manager`（主站点）
- 其他使用 Vite 构建的 React/Vue 项目

## 验证方法

构建完成后，验证关键代码是否在 bundle 中：

```bash
# 检查关键字符串是否在输出中
grep -l "onEditProject" dist/assets/*.js

# 或者检查哈希值是否变化
ls -la dist/assets/*.js | head -5
```
