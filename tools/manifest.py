"""Write manifest.json from the tree, large.json and datasets.json, or check it.

  python tools/manifest.py v1          write the manifest for the tag v1
  python tools/manifest.py --check     verify the manifest against the files on disk

A file of 50 MiB or more is not committed: it is listed in large.json with the release it
is attached to, ignored by git, and its URL is the release asset. Every other file is served
from the raw URL at the tag. Needs only the Python standard library.
"""
import hashlib
import json
import os
import subprocess
import sys
from urllib.parse import quote

REPO = "mtex-toolbox/mtex-data"
LARGE = 50 * 2**20
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# the files of the repository itself, not data
OWN = {"README.md", "LICENSE", "manifest.json", "large.json", "datasets.json", ".gitignore"}


def sha256(path):
  h = hashlib.sha256()
  with open(path, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
      h.update(chunk)
  return h.hexdigest()


def load(name, default):
  path = os.path.join(ROOT, name)
  if not os.path.isfile(path):
    return default
  with open(path) as f:
    return json.load(f)


def dump(name, value):
  with open(os.path.join(ROOT, name), "w") as f:
    json.dump(value, f, indent=2, sort_keys=True)
    f.write("\n")


# the data files on disk, as paths relative to the root with forward slashes
def dataFiles():
  out = []
  for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d != "tools")
    for f in sorted(filenames):
      rel = os.path.relpath(os.path.join(dirpath, f), ROOT).replace(os.sep, "/")
      if rel not in OWN and not f.startswith("."):
        out.append(rel)
  return out


def rawUrl(tag, path):
  return f"https://raw.githubusercontent.com/{REPO}/{tag}/{quote(path)}"


def assetUrl(release, path):
  return f"https://github.com/{REPO}/releases/download/{release}/{quote(os.path.basename(path))}"


def write(tag):
  large = load("large.json", {})
  files = {}
  for path in dataFiles():
    full = os.path.join(ROOT, path)
    entry = {"sha256": sha256(full), "size": os.path.getsize(full)}
    if entry["size"] >= LARGE:
      # a new large file is attached to the release of this tag
      release = large.get(path, {}).get("release", tag)
      large[path] = dict(entry, release=release)
      entry["url"] = assetUrl(release, path)
    else:
      large.pop(path, None)
      entry["url"] = rawUrl(tag, path)
    files[path] = entry
  # a large file not on disk keeps its entry, its asset already published
  for path, entry in large.items():
    if path not in files:
      files[path] = {"sha256": entry["sha256"], "size": entry["size"], "url": assetUrl(entry["release"], path)}
  names = [os.path.basename(p) for p in large]
  assert len(names) == len(set(names)), "two large files share a name, their assets would collide"
  datasets = {}
  for d in load("datasets.json", []):
    missing = [f for f in d["files"] if f not in files]
    assert not missing, f"data set {d['name']} names missing files {missing}"
    datasets[d["name"]] = {k: d[k] for k in ("type", "description", "files")}
  dump("large.json", large)
  dump("manifest.json", {"version": tag, "repository": REPO, "files": files, "datasets": datasets})
  with open(os.path.join(ROOT, ".gitignore"), "w") as f:
    f.write("# the files attached to a release, listed in large.json\n")
    f.writelines(f"/{p}\n" for p in sorted(large))
  print(f"manifest.json: {len(files)} files, {len(large)} as release assets, {len(datasets)} data sets")


def check():
  manifest = load("manifest.json", None)
  assert manifest is not None, "no manifest.json"
  bad = []
  onDisk = set(dataFiles())
  for path, entry in manifest["files"].items():
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
      if entry["size"] < LARGE:
        bad.append(f"missing: {path}")
    elif sha256(full) != entry["sha256"]:
      bad.append(f"changed: {path}")
  bad += [f"not in the manifest: {p}" for p in sorted(onDisk - set(manifest["files"]))]
  tracked = set(subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n"))
  bad += [f"large file tracked by git: {p}" for p in load("large.json", {}) if p in tracked]
  print("\n".join(bad) or f"manifest.json {manifest['version']} matches the tree")
  return not bad


if __name__ == "__main__":
  if sys.argv[1:] == ["--check"]:
    sys.exit(0 if check() else 1)
  if len(sys.argv) != 2 or sys.argv[1].startswith("-"):
    sys.exit(__doc__)
  write(sys.argv[1])
