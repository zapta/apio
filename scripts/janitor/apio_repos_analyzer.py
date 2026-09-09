"""
Experimental code to analyzer repos crawling results.
"""

from dataclasses import asdict, dataclass
import pickle
import json
from pathlib import Path
from typing import List, Dict
from scripts.janitor.apio_repos_crawler import (
    CrawlResults,
    crawl,
    GithubReleaseRef,
)


@dataclass(frozen=True)
class AnalysisResults:
    """Contains analysis reports."""

    should_be_stable: Dict[str, List[str]]
    should_be_latest: Dict[str, str]


def analyze(crawl_results: CrawlResults) -> AnalysisResults:
    """Analyze crawling results and generate requirements report."""

    # used_releases: Set[GithubReleaseRef] = set()

    should_be_stable_releases: Dict[str, List[str]] = {}

    def append_stable_release(r: GithubReleaseRef):
        tags = should_be_stable_releases.get(r.repo, [])
        if r.tag not in tags:
            tags.append(r.tag)
            tags.sort(reverse=True)
        should_be_stable_releases[r.repo] = tags

    for _, c in crawl_results.vscode_marketplace_crawl.releases.items():
        append_stable_release(c.apio_vscode_release)
        append_stable_release(c.apio_cli_release)
        # used_releases.add(c.apio_vscode_release)
        # used_releases.add(c.apio_cli_release)

    for _, c in crawl_results.remote_configs_crawl.remote_configs.items():
        for _, p in c.packages.items():
            # used_releases.add(p.package_release)
            append_stable_release(p.package_release)

    # print(len(used_releases))
    # print(len(used_releases.keys()))

    should_be_stable_releases = dict(sorted(should_be_stable_releases.items()))

    should_be_latest_releases: Dict[str, str] = {}

    pypi_crawl = crawl_results.pypi_crawl
    pypi_latest_release = pypi_crawl.releases[str(pypi_crawl.latest)]
    should_be_latest_releases[pypi_latest_release.apio_cli_release.repo] = (
        pypi_latest_release.apio_cli_release.tag
    )

    vscode_crawl = crawl_results.vscode_marketplace_crawl
    vscode_latest_release = vscode_crawl.releases[str(vscode_crawl.latest)]
    should_be_latest_releases[
        vscode_latest_release.apio_vscode_release.repo
    ] = vscode_latest_release.apio_vscode_release.tag

    latest_remote_config_key = (
        str(pypi_crawl.latest.major) + "." + str(pypi_crawl.latest.minor)
    )
    latest_remote_config = crawl_results.remote_configs_crawl.remote_configs[
        latest_remote_config_key
    ]
    # print(latest_remote_config)
    for _, package in latest_remote_config.packages.items():
        release = package.package_release
        # print({name: package})
        # should_be_latest_releases.append(package.package_release)
        assert release.repo not in should_be_latest_releases
        should_be_latest_releases[release.repo] = release.tag

    # report = {
    #         "should-be-stable-releases" : should_be_stable_releases,
    #         "should-be-latest-releases" : should_be_latest_releases,}

    return AnalysisResults(
        should_be_stable_releases, should_be_latest_releases
    )


def main():
    """Main for testing."""

    cache_file = Path("_crawl_cache.pkl")

    if not cache_file.exists():
        crawl_results: CrawlResults = crawl()
        # pickle.dump(crawl_results, open(cache_file, "wb"))
        with open(cache_file, "wb") as f:
            pickle.dump(crawl_results, f)

    # crawl_results = pickle.load(open(cache_file, "rb"))

    with open(cache_file, "rb") as f:
        crawl_results = pickle.load(f)

    # print("\nCrawl results:")
    # print(json.dumps(asdict(crawl_results), indent=2, default=str))
    # print()

    analyze_results: AnalysisResults = analyze(crawl_results)

    print("\nAnalysis results:")
    print(json.dumps(asdict(analyze_results), indent=2, default=str))
    print()

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
