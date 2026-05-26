# prj-proposals-manager 数据恢复手册

## 场景

网站数据损坏（垃圾项目、孤儿提案、项目数量异常），需要从 Git 历史恢复到干净状态。

## 恢复流程

### Step 1：找到最后一个干净版本

```bash
cd /path/to/prj-proposals-manager

# 按提交时间找
git log --format="%H %ci %s" --before="2026-05-14 10:00" origin/master | head -20

# 直接检查历史版本的项目数量
for sha in $(git log --oneline --before="2026-05-14 10:00" origin/master | cut -d' ' -f1 | head -20); do
  count=$(git show $sha:data/proposals.json 2>/dev/null | python3 -c "
import json,sys; d=json.load(sys.stdin); print(len(d.get('projects',[])))
" 2>/dev/null)
  echo "$sha: $count projects"
done
```

**干净版本特征**：项目数量符合预期、无 `p-*` 垃圾项目、名称规范。

### Step 2：验证候选版本

```bash
git show <SHA>:data/proposals.json > /tmp/candidate.json
python3 -c "
import json
with open('/tmp/candidate.json') as f:
    d = json.load(f)
projects = d['projects']
has_garbage = any(p.get('id','').startswith('p-') for p in projects)
print(f'Projects: {len(projects)}, Proposals: {sum(len(p.get(\"proposals\",[])) for p in projects)}')
print(f'Has p-* garbage: {has_garbage}')
"
```

### Step 3：合并新项目

```python
import json
with open('/tmp/clean_version.json') as f:
    clean = json.load(f)
with open('/tmp/current_main.json') as f:
    main = json.load(f)

clean_ids = {p['id'] for p in clean['projects']}
new_projects = [p for p in main['projects'] if p['id'] not in clean_ids]
combined = clean['projects'] + new_projects
with open('/tmp/final_proposals.json', 'w') as f:
    json.dump({'version': clean.get('version', 3), 'projects': combined}, f, ensure_ascii=False, indent=2)
```

### Step 4：推送

```bash
cp /tmp/final_proposals.json data/proposals.json
git add data/proposals.json && git commit -m "restore: N projects from <SHA>" && git push origin master
```

## 常见损坏模式

| 症状 | 根因 | 修复 |
|------|------|------|
| 项目数 200+ | sync 脚本把每个 `p-*` 孤儿当项目 | 过滤 `p-*` 前缀 |
| 只有 13 个 | proposals.json 被覆盖 | 从 master 历史恢复 |
| 泳道无 url/gitRepo 链接 | dist build 没更新 | rebuild + GitHub Actions |

## 预防

1. 每次数据更新后验证项目数量
2. git push 后检查 GitHub Actions 状态
3. 记录已知正常的 SHA
