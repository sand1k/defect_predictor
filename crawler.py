from git import Repo
import re
import pprint

def dump(obj):
  for attr in dir(obj):
    print("  obj.%s = %r" % (attr, getattr(obj, attr)))

def findWholeWord(w):
    return re.compile(r'(^| )({0})( |$)'.format(w), flags=re.IGNORECASE).search

repo = Repo('data/atom')
words_to_search = ['bug', 'fix', 'refactor']

commits = list(repo.iter_commits('master', reverse=True))
prev_commit = commits[0]
for commit in commits[1:]:
  commit_message_lines = commit.message.splitlines()
  if not commit_message_lines:
    continue

  commit_message_frist_line = commit_message_lines[0].lower()
  diffs = []
  if any(findWholeWord(x)(commit_message_frist_line) for x in words_to_search):
    diff_index = commit.diff(prev_commit, create_patch=True)
    for diff in diff_index.iter_change_type('M'):
      if diff.a_path[-3:] == ".js":
        diffs.append(diff)
  if diffs:
    print(commit_message_frist_line)
    for d in diffs:
      print(d)
    input("Press Enter to continue...")

  prev_commit = commit
