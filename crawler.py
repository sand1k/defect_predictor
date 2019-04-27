from git import Repo

repo = Repo('data/atom')
for commit in repo.iter_commits('master', max_count=50):
  print(commit.message)
