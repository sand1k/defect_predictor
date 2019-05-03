from git import Repo
import re
import pprint
from unidiff import PatchSet
from functools import reduce
import os

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
      a_path = "--- " + d.a_rawpath.decode('utf-8')
      b_path = "+++ " + d.b_rawpath.decode('utf-8')
      print(a_path)
      print(b_path)
      print(d.diff.decode('utf-8'))

      # Get detailed info
      patch = PatchSet(a_path + os.linesep + b_path + os.linesep + d.diff.decode('utf-8'))
      print("")
      removed_lines = []
      added_lines = []
      for h in patch[0]:
        for l in h:
          if l.source_line_no is None and l.target_line_no is not None:
            added_lines.append(l.target_line_no)
          elif l.source_line_no is not None and l.target_line_no is None:
            removed_lines.append(l.source_line_no)

      print("Removed lines in old file: " + str(removed_lines))
      print("Added lines in new file: " + str(added_lines))
      print("")

    input("Press Enter to continue...")

  prev_commit = commit
