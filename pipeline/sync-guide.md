# 如何与其他机器同步

本文件现在是 `CarloooK/team-workflow` 仓库的源文件。
所有机器的 ~/.hermes/skills/ 都是这个仓库的副本。

## 同步方式

```bash
# 每台机器：首次初始化
git clone git@github.com:CarloooK/team-workflow.git ~/team-workflow
cd ~/team-workflow && bash setup.sh

# 日常同步（当流程有更新时）
cd ~/team-workflow && git pull && bash setup.sh
```

## 修改流程

1. 改 `team-workflow/pipeline/SKILL.md`
2. `git commit && git push`
3. 通知其他 bot 执行 `git pull && bash setup.sh`

## 补丁提示

如果只用 `skill_manage(action='patch', ...)` 改了本地的 skill，
记得同步回仓库：

```bash
cp ~/.hermes/skills/software-development/hermes-multi-agent-pipeline/SKILL.md ~/team-workflow/pipeline/
cd ~/team-workflow && git commit -am "patch: ..." && git push
```
