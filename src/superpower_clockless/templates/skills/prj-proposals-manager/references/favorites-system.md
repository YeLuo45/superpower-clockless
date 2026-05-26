# prj-proposals-manager 收藏功能架构

## 数据存储

收藏数据保存在 GitHub 仓库 `data/favorites.json`：

```json
{
  "favorites": {
    "PRJ-001": { "timestamp": "2026-05-18T12:00:00Z", "pinned": true },
    "P-20260518-001": { "timestamp": "2026-05-18T12:00:00Z", "pinned": false }
  },
  "updatedAt": "2026-05-18T12:00:00Z"
}
```

**ID 前缀规则**：
- `PRJ-*` = 项目收藏
- `P-*` = 提案收藏
- 旧格式：纯时间戳字符串（`"2026-05-17T10:00:00Z"`），需兼容

## useFavorites Hook

路径：`src/hooks/useFavorites.js`

核心方法：
- `fetchFavorites()` — 从 GitHub 读取（5分钟本地缓存）
- `toggleFavorite(id)` — 添加/移除收藏
- `pinFavorite(id)` — 置顶/取消置顶
- `refreshFavorites()` — 强制刷新

**乐观更新**：先更新本地状态，再同步 GitHub；失败则回滚。

## 提案收藏集成

### ProposalCard 改造步骤

1. 导入 hook：
```jsx
import { useFavorites } from '../hooks/useFavorites';
```

2. 调用 hook：
```jsx
const { favorites, toggleFavorite, pinFavorite } = useFavorites();
```

3. 计算收藏状态：
```jsx
const isFavorite = !!favorites[proposal.id];
const favoriteData = favorites[proposal.id];
const isPinned = favoriteData?.pinned || false;
```

4. 添加按钮 UI（卡片右上角）：
```jsx
<div className="flex items-center gap-1">
  <button onClick={(e) => { e.stopPropagation(); toggleFavorite(proposal.id); }}>
    {isFavorite ? '⭐' : '☆'}
  </button>
  {isFavorite && (
    <button onClick={(e) => { e.stopPropagation(); pinFavorite(proposal.id); }}>
      {isPinned ? '📌' : '📍'}
    </button>
  )}
</div>
```

### 筛选逻辑修复

**错误**：按 `projectId` 过滤提案收藏
```jsx
.filter(p => favIds.has(p.projectId))  // ❌ 匹配的是项目ID
```

**正确**：按提案自己的 `id` 过滤
```jsx
.filter(p => favIds.has(p.id))  // ✅
```

排序应支持置顶优先：
```jsx
.sort((a, b) => {
  const pinnedA = favorites[a.id]?.pinned || false;
  const pinnedB = favorites[b.id]?.pinned || false;
  if (pinnedA !== pinnedB) return pinnedB - pinnedA;
  const timeA = favorites[a.id]?.timestamp || '';
  const timeB = favorites[b.id]?.timestamp || '';
  return timeB.localeCompare(timeA);
});
```

## Tab 切换实现

新增状态：
```jsx
const [favoritesTab, setFavoritesTab] = useState('proposals'); // 'projects' | 'proposals'
```

FilterBar 传参：
```jsx
favoritesTab={favoritesTab}
onFavoritesTabChange={setFavoritesTab}
```

FilterBar 内渲染：
```jsx
{showFavoritesOnly && (
  <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300">
    <button
      onClick={() => onFavoritesTabChange('projects')}
      className={favoritesTab === 'projects' ? 'bg-blue-500 text-white' : '...'}
    >
      📁 项目 ({favoritesCount?.projects || 0})
    </button>
    <button
      onClick={() => onFavoritesTabChange('proposals')}
      className={favoritesTab === 'proposals' ? 'bg-blue-500 text-white' : '...'}
    >
      📋 提案 ({favoritesCount?.proposals || 0})
    </button>
  </div>
)}
```

## 已知限制

1. **Token 必需**：写入收藏需要 GitHub Token（`VITE_GH_TOKEN` 或 `localStorage.github_token`），未设置时 toast 提示
2. **写入延迟**：乐观更新后，若 GitHub PUT 失败，本地状态回滚
3. **缓存 TTL**：5分钟，可能导致多设备间短暂不一致