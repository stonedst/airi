我认为完全可以用dev分支开发，main分支保持同步，然后合并到dev分支

### 1. 确保你已经克隆了远程仓库

如果你还没有克隆远程仓库，可以使用以下命令进行克隆：
```bash
git clone https://github.com/moeru-ai/airi.git
cd airi
```

### 2. 添加上游仓库（如果需要）

如果你是从一个 fork 的仓库中工作，可能需要添加上游仓库以便获取原始仓库的更新：
```bash
git remote add upstream https://github.com/moeru-ai/airi.git
```

### 3. 拉取远程仓库的最新更改

确保你在 `main` 分支上：
```bash
git checkout main
```

然后拉取远程仓库的最新更改：
```bash
git fetch upstream
```

### 4. 合并远程仓库的更改

你可以选择使用 `merge` 或 `rebase` 来合并远程仓库的更改。

#### 使用 `merge` 合并

最好使用merge

这会创建一个新的合并提交，包含所有更改：
```bash
git merge upstream/main
```

#### 使用 `rebase` 重新应用你的提交

这会将你的提交重新应用在远程仓库的最新提交之上，使历史记录更加线性：
```bash
git rebase upstream/main
```

### 5. 解决冲突（如果有）

在合并或变基过程中，可能会出现冲突。Git 会提示你哪些文件有冲突，你需要手动解决这些冲突。解决冲突后，使用以下命令继续操作：
```bash
# 如果是 merge
git commit

# 如果是 rebase
git rebase --continue
```

### 6. 推送更改到你的远程仓库

完成合并或变基后，你可以将更改推送到你的远程仓库：
```bash
git push origin main
```

### 7. 提交 PR（如果需要）

如果你是从一个 fork 的仓库中工作，并且希望将更改合并到原始仓库中，可以创建一个 Pull Request (PR)：
1. 在 GitHub 上访问你的 fork 仓库。
2. 点击 "New pull request"。
3. 选择 `main` 分支作为 base 和 compare 分支。
4. 填写 PR 描述并提交。

### 总结

通过以上步骤，你可以将远程仓库的最新更改合并到你的本地仓库中，同时保留你的本地提交。根据你的需求选择使用 `merge` 或 `rebase`，并解决可能出现的冲突。最后，将更改推送到你的远程仓库，并根据需要创建 PR。
