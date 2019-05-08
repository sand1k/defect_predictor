from git import Repo
import re
import pprint
from unidiff import PatchSet
from functools import reduce
import os
import zmq
import sys
import json
from bisect import bisect_left, bisect_right
import numpy as np
import pickle


def dump(obj):
  for attr in dir(obj):
    print("  obj.%s = %r" % (attr, getattr(obj, attr)))

def findWholeWord(w):
  return re.compile(r'(^| )({0})( |$)'.format(w), flags=re.IGNORECASE).search


def find_ge(a, x):
  'Find leftmost item greater than or equal to x'
  i = bisect_left(a, x)
  if i != len(a):
    return i
  raise ValueError

def find_le(a, x):
  'Find rightmost value less than or equal to x'
  i = bisect_right(a, x)
  if i:
    return i - 1
  raise ValueError

def find_function_at_line(funcs_line, line_no):
  i = find_le(funcs_line, line_no)
  return i

def get_function_metrics_as_np_array(f_metrics):
  'Convert function metrics from escomplex format to numpy array'
  arr = [f_metrics["cyclomatic"],
         f_metrics["halstead"]["operands"]["distinct"],
         f_metrics["halstead"]["operands"]["total"],
         f_metrics["halstead"]["operators"]["distinct"],
         f_metrics["halstead"]["operators"]["total"],
         f_metrics["halstead"]["length"],
         f_metrics["halstead"]["vocabulary"],
         f_metrics["halstead"]["difficulty"],
         f_metrics["halstead"]["volume"],
         f_metrics["halstead"]["effort"],
         f_metrics["halstead"]["bugs"],
         f_metrics["halstead"]["time"],
         f_metrics["params"],
         f_metrics["sloc"]["logical"],
         f_metrics["sloc"]["physical"],
         f_metrics["cyclomaticDensity"]]
  return arr

def check_and_add_functions_metrics(metrics, f_metrics_a, f_metrics_b):
  name_a = f_metrics_a["name"]
  np_metr_a = get_function_metrics_as_np_array(f_metrics_a)

  name_b = f_metrics_b["name"]
  np_metr_b = get_function_metrics_as_np_array(f_metrics_b)

  if name_a == name_b and not np.array_equal(np_metr_a, np_metr_b):
    np_metr_a.append(1.0)
    metrics.append(np_metr_a)
    np_metr_b.append(0.0)
    metrics.append(np_metr_b)

    print("function a (name: %s, line: %s, sloc: %s" % (name_a,
                                                        f_metrics_a["line"],
                                                        f_metrics_a["sloc"]["physical"]))
    print(np_metr_a)
    print("function b (name: %s, line: %s, sloc: %s" % (name_b,
                                                        f_metrics_b["line"],
                                                        f_metrics_b["sloc"]["physical"]))
    print(np_metr_b)

  return metrics

def save_data(metrics):
  print("Dump %s metrics." % (len(metrics)))
  np_metrics = np.asarray(metrics)
  with open('metrics.pkl', 'wb') as f:
    pickle.dump(np_metrics, f)

#
# main code
#
SAVE_CHUNK_SIZE = 50
save_limit = SAVE_CHUNK_SIZE

np.set_printoptions(precision = 3)
metrics = []

# setup zmq client
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://127.0.0.1:5557")

repo = Repo('data/atom')
words_to_search = ['bug', 'fix', 'refactor', 'error', 'fail']

commits = list(repo.iter_commits('master', reverse=True))
prev_commit = commits[0]
for commit in commits[1:]:
  commit_message_lines = commit.message.splitlines()
  if not commit_message_lines:
    continue

  commit_message_frist_line = commit_message_lines[0].lower()
  diffs = []
  if any(findWholeWord(x)(commit_message_frist_line) for x in words_to_search):
    diff_index = prev_commit.diff(commit, create_patch=True)
    for diff in diff_index.iter_change_type('M'):
      if diff.a_path[-3:] == ".js":
        diffs.append(diff)

  if diffs:
    print(commit_message_frist_line)
    for d in diffs:
      a_path = "--- " + d.a_rawpath.decode('utf-8')
      b_path = "+++ " + d.b_rawpath.decode('utf-8')

      # Get detailed info
      patch = PatchSet(a_path + os.linesep + b_path + os.linesep + d.diff.decode('utf-8'))

      # Parse old file
      socket.send(d.a_blob.data_stream.read())
      report = socket.recv()
      metrics_a = json.loads(report.decode('utf-8'))
      if "error" in metrics_a:
        print("error: %s" % (metrics_a["error"]))
        continue
      functions_a = metrics_a["functions"]
      funcs_line_a = [f["line"] for f in functions_a]

      # Parse new file
      socket.send(d.b_blob.data_stream.read())
      report = socket.recv()
      metrics_b = json.loads(report.decode('utf-8'))
      if "error" in metrics_b:
        print("error: %s" % (metrics_b["error"]))
        continue
      functions_b = metrics_b["functions"]
      funcs_line_b = [f["line"] for f in functions_b]

      for h in patch[0]:
        try:
          for l in h:
            if (l.source_line_no is not None
                and l.target_line_no is not None):

              ind_a = find_function_at_line(funcs_line_a, l.source_line_no)
              f_metrics_a = functions_a[ind_a]

              ind_b = find_function_at_line(funcs_line_b, l.target_line_no)
              f_metrics_b = functions_b[ind_b]

              if "seen" in functions_a[ind_a] or "seen" in functions_b[ind_b]:
                continue

              metrics = check_and_add_functions_metrics(metrics, f_metrics_a, f_metrics_b)
              functions_a[ind_a]["seen"] = True
              functions_b[ind_b]["seen"] = True

        except ValueError:
          continue

      print("")

  prev_commit = commit

  if len(metrics) > save_limit:
    save_data(metrics)
    save_limit += SAVE_CHUNK_SIZE

save_data(metrics)

