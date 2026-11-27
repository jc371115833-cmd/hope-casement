"""Validate the candidate version before building or tagging it in Actions."""

import os
import re
import subprocess
import tomllib
from pathlib import Path


def project_version(toml: str) -> str:
    version = tomllib.loads(toml)["project"]["version"]
    if not re.fullmatch(r"(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)){2}", version, re.ASCII):
        raise SystemExit(f"Expected a numeric major.minor.patch version, got {version!r}")
    return version


def main() -> None:
    version = project_version(Path("pyproject.toml").read_text(encoding="utf-8"))
    tag = f"v{version}"
    ref = os.environ["GITHUB_REF"]
    is_tag = ref.startswith("refs/tags/")
    if os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch" and not is_tag:
        raise SystemExit("Dispatch the release workflow on its version tag.")
    changed = False
    if is_tag:
        if ref != f"refs/tags/{tag}":
            raise SystemExit(f"{ref} does not match project version {version}")
        subprocess.run(["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], check=True)
    else:
        base = os.environ["BEFORE"]
        if not re.fullmatch(r"[0-9a-f]{40}", base) or base == "0" * 40:
            raise SystemExit("Missing comparison commit for the version check.")
        old_toml = subprocess.check_output(["git", "show", f"{base}:pyproject.toml"], encoding="utf-8")
        old = project_version(old_toml)
        changed = version != old
        if changed and tuple(map(int, version.split("."))) < tuple(map(int, old.split("."))):
            raise SystemExit(f"Version decreased from {old} to {version}")
    if is_tag or changed:
        notes = Path(f"docs/releases/{tag}.md")
        if not notes.is_file() or not notes.read_text(encoding="utf-8").strip():
            raise SystemExit(f"Missing release notes in {notes}")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        print(f"version={version}", file=output)
        if changed and ref == "refs/heads/main":
            print(f"release_tag={tag}", file=output)


if __name__ == "__main__":
    main()
