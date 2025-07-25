import requests
import toml
import sys
import os
from packaging.version import Version, InvalidVersion

UPSTREAM_REPO = "snakemake/snakemake-executor-plugin-slurm"
PYPROJECT = "pyproject.toml"

EXIT_OK = 0         # no changes
EXIT_ERROR = 1      # script failure
EXIT_NEW_RELEASE = 42  # desired trigger

def error(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(EXIT_ERROR)

def get_latest_upstream_version():
    url = f"https://api.github.com/repos/{UPSTREAM_REPO}/releases/latest"
    headers = {"Accept": "application/vnd.github+json"}

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        error(f"Failed to fetch upstream release info: {r.status_code}, response: {r.text}")

    try:
        version_str = r.json()["tag_name"].lstrip("v")
        return Version(version_str)
    except Exception:
        error("Failed to parse upstream version from tag")

def get_local_main_version():
    try:
        data = toml.load(PYPROJECT)
        version_str = data["tool"]["poetry"]["version"]
        base = Version(version_str).base_version  # base_version is a str
        return Version(base)  # convert base_version string back to Version object
    except Exception as e:
        error(f"Could not parse pyproject.toml version: {e}")

def main():
    upstream = get_latest_upstream_version()
    local = get_local_main_version()

    print(f"Local main version = {local}")
    print(f"Upstream version   = {upstream}")

    if upstream > local:
        print("New upstream release detected!")
        sys.exit(EXIT_NEW_RELEASE)
    else:
        print("No new release")
        sys.exit(EXIT_OK)

if __name__ == "__main__":
    ######
    ## TESTS
    # # Simulated version for testing
    # simulated_upstream_version = "1.2.99"

    # # Print output GitHub Actions will parse
    # print(f"Local main version = 1.2.1")
    # print(f"Upstream version   = {simulated_upstream_version}")
    # print("New upstream release detected!")

    # # Emit output for GitHub Actions
    # #print(f"upstream-version={simulated_upstream_version}")

    # # Exit code triggers the sync workflow
    # sys.exit(42)
    ######

    main()