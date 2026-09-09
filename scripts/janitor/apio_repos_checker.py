"""
Experimental code to analyzer repos crawling results.
"""

import os
from dataclasses import asdict, dataclass
import pickle
import json
import argparse
from pathlib import Path
from typing import List, Dict
import requests
from apio_repos_crawler import CrawlResults, crawl
from apio_repos_analyzer import AnalysisResults, analyze

parser = argparse.ArgumentParser(description="Apio Repos Janitor's check phase.")
parser.add_argument(
    "--work-dir",
    type=Path,
    default=Path("./_janitor"),
    help="Janitor's temp data dir (default = ./_janitor)",
)
args = parser.parse_args()

@dataclass(frozen=True)
class CheckFailures:
    """Checks that failed."""

    missing: Dict[str, List[str]]
    non_stable: Dict[str, List[str]]
    non_latest: Dict[str, str]

    def has_failures(self) -> bool:
        """Returns True if has any error."""
        return (
            len(self.missing) > 0
            or len(self.non_stable) > 0
            or len(self.non_latest) > 0
        )


@dataclass(frozen=True)
class CheckSuccesses:
    """Checks that were successful."""

    releases_stable: Dict[str, List[str]]
    releases_latest: Dict[str, str]


@dataclass(frozen=True)
class CheckResults:
    """The results of the Repos Check step."""

    failures: CheckFailures
    successes: CheckSuccesses

    def has_failures(self) -> bool:
        """Returns True if has any error."""
        return self.failures.has_failures()


@dataclass(frozen=True)
class ReleaseStatus:
    """Release status lookup result. Note that is_latest requires a separate
    request to Github so not included here."""

    exists: bool
    is_draft: bool
    is_prerelease: bool
    is_stable: bool


def github_release_status(repo: str, tag: str) -> ReleaseStatus:
    """Lookup the status of given release."""
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    r = requests.get(
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
        headers=headers,
        timeout=30,
    )
    if r.status_code == 404:
        return ReleaseStatus(
            exists=False,
            is_draft=False,
            is_prerelease=False,
            is_stable=False,
        )
    r.raise_for_status()
    data = r.json()

    is_draft = bool(data.get("draft"))
    is_prerelease = bool(data.get("prerelease"))
    return ReleaseStatus(
        exists=True,
        is_draft=is_draft,
        is_prerelease=is_prerelease,
        is_stable=not is_draft and not is_prerelease,
    )


def github_release_is_latest(repo: str, tag: str) -> bool:
    """Test if given release exists and is 'latest'."""
    print(f"Verifying that {repo} #{tag} is latest.")

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code == 404:
        return False
    r.raise_for_status()

    data = r.json()
    return data.get("tag_name") == tag


def check(analysis_results: AnalysisResults) -> CheckResults:
    """Check requirements from analysis report"""

    # errors = []

    missing: Dict[str, List[str]] = {}
    not_stable: Dict[str, List[str]] = {}
    is_stable: Dict[str, List[str]] = {}

    for repo, release_tags in analysis_results.should_be_stable.items():
        for release_tag in release_tags:
            release_status: ReleaseStatus = github_release_status(
                repo, release_tag
            )
            if not release_status.exists:
                missing[repo] = missing.get(repo, []) + [release_tag]
            elif not release_status.is_stable:
                not_stable[repo] = not_stable.get(repo, []) + [release_tag]
            else:
                # print(f"{is_stable=}")
                # print(f"{repo=}")
                # print(f"{release_tag=}")
                # print(f"{is_stable.get(repo, [])=}")
                is_stable[repo] = is_stable.get(repo, []) + [release_tag]

    not_latest: Dict[str, str] = {}
    is_latest: Dict[str, str] = {}
    for repo, release_tag in analysis_results.should_be_latest.items():
        if not github_release_is_latest(repo, release_tag):
            not_latest[repo] = release_tag
        else:
            is_latest[repo] = release_tag

    # check_results =
    return CheckResults(
        CheckFailures(missing, not_stable, not_latest),
        CheckSuccesses(is_stable, is_latest),
    )

    # if not errors:
    #     print("No errors.")
    #     return

    # print(f"Found {len(errors)} errors")
    # for error in errors:
    #     print(f"- {error}")
    # sys.exit(1)


def main():
    """Main for testing."""


    # -- Get the work dir path.
    work_dir_path = args.work_dir
    print(f"work_dir = {str(work_dir_path)}")

    # -- Load the crawler results
    with open(work_dir_path / "analysis_results.pkl", "rb") as f:
        analysis_results = pickle.load(f)
    

    # -- Check
    check_results: CheckResults = check(analysis_results)

    # -- Write results as json, for human consumption.
    (work_dir_path / "check_results.json").write_text(
        json.dumps(asdict(check_results), indent=2, default=str),
        encoding="utf-8",
    )

    # -- Write results as pickle, for consumption by next step.
    with (work_dir_path / "check_results.pkl").open("wb") as f:
        pickle.dump(check_results, f)




    # cache_file = Path("_crawl_cache.pkl")

    # if not cache_file.exists():
    #     crawl_results: CrawlResults = crawl()
    #     # pickle.dump(crawl_results, open(cache_file, "wb"))
    #     with open(cache_file, "wb") as f:
    #         pickle.dump(crawl_results, f)

    # # crawl_results = pickle.load(open(cache_file, "rb"))

    # with open(cache_file, "rb") as f:
    #     crawl_results = pickle.load(f)

    # print("\nCrawl results:")
    # print(json.dumps(asdict(crawl_results), indent=2, default=str))
    # print()

    # analysis_results: AnalysisResults = analyze(crawl_results)

    # prin("\nAnalysis results:")
    # print(json.dumps(asdict(analysis_results), indent=2, default=str))
    # print()t

    # check_results: CheckResults = check(analysis_results)

    # print("\nCheck results:")
    # print(json.dumps(asdict(check_results), indent=2, default=str))
    # print()

    # for repo in list(used_releases.keys()).sort():
    # for repo, tags in sorted(used_releases.items()):
    #     print(repo)
    #     for tag in tags:
    #       print(f"  {tag}")
    # used_releases = list(used_releases)
    # used_releases.sort()

    # for rel in used_releases:
    #     print(rel)


if __name__ == "__main__":
    main()
