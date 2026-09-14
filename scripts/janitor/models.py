"""
Contains the dataclasses that are used to communicate data
between janitor steps. Having them in a separate python
module resolves some issues with the pickling.
"""

from typing import List, Dict, Any, Set, Optional
from datetime import date
from dataclasses import dataclass, field
from enum import Enum
from packaging.version import Version
from scripts.janitor import consts

# ---------- Common


class ReleaseState(Enum):
    """Represents the state of a release."""

    # -- Draft.
    DRAFT = "draft"
    # -- Pre-release.
    PRERELEASE = "pre-release"
    # -- Stable but not latest.
    STABLE = "stable"
    # -- Stable and latest (only one per repo)
    LATEST = "latest"

    @classmethod
    def from_flags(
        cls, draft: bool, prerelease: bool, is_latest: bool
    ) -> "ReleaseState":
        """Map github release flags to a state enum."""
        if draft:
            return cls.DRAFT
        if prerelease:
            return cls.PRERELEASE
        if is_latest:
            return cls.LATEST
        return cls.STABLE

    def __str__(self) -> str:
        """Using the string value as string representation. Used by json dumps
        when default=str.
        """
        return self.value

    @property
    def is_stable(self) -> bool:
        """Returns True if the release is stable."""
        return self in (ReleaseState.STABLE, ReleaseState.LATEST)

    @property
    def is_latest(self) -> bool:
        """Returns true if the release is marked as 'latest'."""
        return self is ReleaseState.LATEST


def _check_repo_str(repo: str):
    """Check repo string."""
    assert repo == repo.lower(), repo
    assert repo in consts.APIO_REPOS, repo


def _check_tag_str(repo: str):
    """Check release tag string."""
    # TBD
    _ = repo


def _repo_and_tag_to_str(repo: str, tag: str) -> str:
    """Convert repo and release tag string to a string for humans."""
    _check_repo_str(repo)
    _check_tag_str(tag)
    return f"{repo} #{tag}"


# @dataclass(frozen=True)
# class RepoRef:
#     repo: str

#     def __post_init__(self):
#         """Sanity checks."""
#         _check_repo_str(self.repo)

#     def __str__(self) -> str:
#         """Human friendly representation of the object."""
#         return self.repo


@dataclass(frozen=True)
class GithubReleaseRef:
    """A reference to an Apio github repo."""

    repo: str
    tag: str

    def __post_init__(self):
        """Sanity checks."""
        _check_repo_str(self.repo)

    def __str__(self) -> str:
        """Human friendly representation of the object."""
        return _repo_and_tag_to_str(self.repo, self.tag)


class RequirementType(Enum):
    """Represents the state of a release."""

    RELEASE_SHOULD_BE_STABLE = "release-should-be-stable"
    RELEASE_SHOULD_BE_SAFE = "release-should-be-stable"
    REPO_SHOULD_HAVE_RECENT_BUILD = "repo-should-have-a-recent-build"

    @property
    def is_repo_scope(self) -> bool:
        """Returns true if this requirement type is of repo scope and thus
        should not contain release tag"""
        return self in {
            RequirementType.REPO_SHOULD_HAVE_RECENT_BUILD,
        }

    @property
    def is_release_scope(self) -> bool:
        """Returns true if this requirement type is of release scope and thus
        should contain a release tag"""
        return not self.is_repo_scope


@dataclass(frozen=True, kw_only=True, order=True)
class Requirement:
    """Represent a requirement that should met."""

    # -- The requirement type.
    req_type: RequirementType
    # -- The repo name, e.g. "fpgawars/apio"
    repo: str
    # -- The release tag, only if req_type.is_repo_scope.
    release_tag: Optional[str]
    # -- Note lines that are collected during verifier.
    notes: List[str] = field(default_factory=list, compare=False)

    def __post_init__(self):
        """Sanity checks."""
        assert self.repo == self.repo.lower(), self
        assert self.repo in consts.APIO_REPOS, self
        assert (self.release_tag is None) == self.req_type.is_repo_scope
        assert isinstance(self.notes, list)
        assert len(self.notes) == 0


#     def __str__(self) -> str:
#         """Human friendly representation of the object."""
#         return self.repo + " #" + self.tag


# @dataclass(frozen=True)
# class RepoRequirement(Requirement):
#     pass


# @dataclass(frozen=True)
# class ReleaseRequirement(Requirement):
#     release: ReleaseRef


# @dataclass(frozen=True)
# class ReleaseShouldBeStable(ReleaseRequirement):
#     pass


# @dataclass(frozen=True)
# class ReleaseShouldBeLatest(ReleaseRequirement):
#     pass


# T = TypeVar("T", bound=Requirement)


class RequirementsSet:
    """A set of Requirement with Janitor specific operations."""

    def __init__(self):
        self._members: Set[Requirement] = set()

    def add(self, requirement: Requirement) -> None:
        """Add a member to the set. No change if already in the set."""
        assert isinstance(requirement, Requirement)
        self._members.add(requirement)

    def __len__(self) -> int:
        """Allows to use len(release_set) to find the number of releases."""
        return len(self.members)

    def __contains__(self, requirement: Requirement) -> bool:
        """Allows to use 'requirement in set' operator"""
        assert isinstance(requirement, Requirement)
        return requirement in self._members

    def group_by_repo(
        self,
    ) -> Dict[str, Dict[RequirementType, Set[Requirement]]]:
        """Return all the members as a repo/type/requirement tree."""
        result: Dict[str, Dict[RequirementType, Set[Requirement]]] = {}
        for req in self._members:
            by_type = result.setdefault(req.repo, {})
            by_type.setdefault(req.req_type, set()).add(req)
        return result

    def group_by_type(
        self,
    ) -> Dict[RequirementType, Dict[str, Set[Requirement]]]:
        """Return all the members as a type/repo/requirement tree."""
        result: Dict[RequirementType, Dict[str, Set[Requirement]]] = {}
        for req in self._members:
            by_repo = result.setdefault(req.req_type, {})
            by_repo.setdefault(req.repo, set()).add(req)
        return result

    # def members_for_repo(self, repo: str) -> Set[T]:
    #     """Return a list of requirements of given repo."""
    #     _check_repo_str(repo)
    #     return {m for m in self._members if m.repo == repo}

    # def add(self, release: GithubReleaseRef) -> None:
    #     """Add a release reference to the set."""
    #     repo = release.repo
    #     # -- Case 1: This is the first for this repo.
    #     if repo not in self._repos:
    #         self._repos[repo] = set([release])
    #         return
    #     # -- Case 2: Repo already has at least one release.
    #     self._repos[repo].add(release)

    def repos(self) -> Set[str]:
        """Return a set of repos that have at least one requirement."""
        return {m.repo for m in self._members}

    # def as_dict(self) -> Dict[str, Set[T]]:
    #     """Converts to a dict of repo -> release_ref."""
    #     return {repo: self.members_for_repo(repo) for repo in self.repos()}

    # def items(self):
    #     """Allows for each iteration of (repo, requirement)."""
    #     return self.as_dict().items()

    def members(self) -> Set[Requirement]:
        """Returns a flat set of all members."""
        return self._members

    # def as_str_dict(self) -> Dict[str, List[str]]:
    #     """Converts to a dict of strings."""
    #     repos_list = sorted(self.repos())
    #     if self._is_repo_scope:
    #         return repos_list
    #     result = {}
    #     for repo in repos_list:
    #         tags = [r.tag for r in self.members_for_repo(repo)]
    #         tags = sorted(tags, reverse=True)
    #         result[repo] = tags
    #     return result

    # def to_json_dict(self) -> Dict[str, Any]:
    #     """Return a dict that can be serialized to json. Called from
    #     the json serializer."""

    # TODO: Tweak the json tree.
    def to_json_dict(self) -> Dict[str, Any]:
        """Return a dict that can be serialized to json. Called from
        the json serializer."""

        def type_key(req_type: RequirementType) -> str:
            return req_type.name.lower().replace("_", "-")

        def req_dict(req: Requirement) -> Dict[str, Any]:
            d: Dict[str, Any] = {
                "req_type": type_key(req.req_type),
                "repo": req.repo,
                "release_tag": req.release_tag,
            }
            if req.notes:
                d["notes"] = list(req.notes)
            return d

        return {
            type_key(req_type): {
                repo: [req_dict(req) for req in reqs]
                for repo, reqs in by_repo.items()
            }
            for req_type, by_repo in self.group_by_type().items()
        }

    def check_partitioning(
        self,
        partition1: "RequirementsSet",
        partition2: "RequirementsSet",
    ):
        """Check that partition1 and partition2 are proper partitioning of this
        set."""
        assert isinstance(partition1, RequirementsSet)
        assert isinstance(partition2, RequirementsSet)

        # -- Check that there are no dupes and no missing.
        members1 = partition1.members()
        members2 = partition2.members()

        assert members1.isdisjoint(members2)
        assert members1.union(members2) == self._members


# @dataclass(frozen=True, order=True)
# class GithubReleaseRef:
#     """Represents a single release on a github repo."""

#     # -- The github repo. E.g. "fpgawars/apio"
#     repo: str
#     # -- The release tag, e.g. "2026-08-13"
#     tag: str

#     def __post_init__(self):
#         """Sanity checks."""
#         assert self.repo == self.repo.lower(), self
#         assert self.repo in consts.APIO_REPOS, self

#     def __str__(self) -> str:
#         """Human friendly representation of the object."""
#         return self.repo + " #" + self.tag


# class ReleaseSet:
#     """Represent a set of GithubReleaseRef that can be be grouped by
#     repo."""

#     def __init__(self):
#         """Constructs an empty set."""
#         self._repos: Dict[str, Set[GithubReleaseRef]] = {}

#     def __len__(self) -> int:
#         """Allows to use len(release_set) to find the number of releases."""
#         return sum(len(releases) for releases in self._repos.values())

#     def __contains__(self, release: GithubReleaseRef) -> bool:
#         """Allows to use 'release in set' operator"""
#         assert isinstance(release, GithubReleaseRef), release
#         repo_releases: Set[GithubReleaseRef] = self._repos.get(
#             release.repo, set()
#         )
#         return release in repo_releases

#     def repo_releases(self, repo: str) -> Set[GithubReleaseRef]:
#         """Return a list of the releases of a single repo."""
#         return self._repos.get(repo, set())

#     def add(self, release: GithubReleaseRef) -> None:
#         """Add a release reference to the set."""
#         repo = release.repo
#         # -- Case 1: This is the first for this repo.
#         if repo not in self._repos:
#             self._repos[repo] = set([release])
#             return
#         # -- Case 2: Repo already has at least one release.
#         self._repos[repo].add(release)

#     def as_dict(self) -> Dict[str, Set[GithubReleaseRef]]:
#         """Converts to a dict of repo -> release_ref."""
#         return self._repos

#     def repos(self) -> Set[str]:
#         """Return a set of repos that have at least one release."""
#         return set(self._repos.keys())

#     def items(self):
#         """Allows for each iteration of (repo, releases)."""
#         return self.as_dict().items()

#     def releases(self) -> Set[GithubReleaseRef]:
#         """Returns a set of all releases in the set."""
#         all_releases: Set[GithubReleaseRef] = set()
#         for s in self._repos.values():
#             all_releases.update(s)
#         return all_releases

#     def as_tag_dict(self) -> Dict[str, List[str]]:
#         """Converts to a dict of repo -> release_tag."""
#         result = {}
#         for repo in sorted(self._repos.keys()):
#             tags = [r.tag for r in self._repos[repo]]
#             # tags = sorted(self._repos[repo])
#             tags = sorted(tags, reverse=True)
#             result[repo] = tags
#         return result

#     def to_json_dict(self) -> Dict[str, Any]:
#         """Return a dict that can be serialized to json. Called from
#         the json serializer."""
#         return self.as_tag_dict()

#     def check_partitioning(
#         self,
#         partition1: "ReleaseSet",
#         partition2: "ReleaseSet",
#     ):
#         """Check that partition1 and partition2 are proper partitioning of
#  this
#         set."""
#         assert isinstance(partition1, ReleaseSet)
#         assert isinstance(partition2, ReleaseSet)

#         # -- Convert to plain sets of releases.
#         self_releases = self.releases()
#         releases1 = partition1.releases()
#         releases2 = partition2.releases()

#         # -- Check no dupes and no missing.
#         assert releases1.isdisjoint(releases2)
#         assert releases1.union(releases2) == self_releases


# ---------- Crawler output


@dataclass(frozen=True)
class PypiReleaseCrawl:
    """Crawling information of a single Pypi Apio CLI release. See
    https://pypi.org/project/apio/#history
    """

    # -- The date on which the released for published on Pypi.
    published: date

    # -- A reference to the Apio CLI release from which this pypi release
    # -- was created.
    apio_cli_release: GithubReleaseRef


@dataclass(frozen=True)
class PypiCrawl:
    """Pypi crawling information."""

    # -- The default release for 'pip install apio', this is considered the
    # -- 'latest' stable release.
    latest: Version
    # -- Dict from pypi release version to the release information.
    releases: Dict[str, PypiReleaseCrawl]
    # -- List of pypi apio releases that were skipped, either too old
    # -- or known to be problematic.
    skipped_versions: List[Version]


@dataclass(frozen=True)
class VscodeReleaseCrawl:
    """Crawling information of a single VSCode Marketplace Apio IDE release.
    https://marketplace.visualstudio.com/items?itemName=fpgawars.apio
    """

    # -- The date on which the release was published on the VSCode Marketplace.
    published: date
    # -- The github release of this extension version.
    apio_vscode_release: GithubReleaseRef
    # -- The github release of the underlying Apio CLI that is used by this
    # -- extension.
    apio_cli_release: GithubReleaseRef


@dataclass(frozen=True)
class VscodeMarketplaceCrawl:
    """VSCode Marketplace crawling information."""

    # -- The default Apio Vscode extension version. This considered to be the
    # -- 'latest' stable release.
    latest: Version
    # -- List of relevant releases that were crawled.
    releases: Dict[str, VscodeReleaseCrawl]
    # -- List of extension versions that were skipped, e.g. for being too old.
    skipped_versions: List[Version]


@dataclass(frozen=True)
class RemoteConfigPackageCrawl:
    """Crawling result of a single package configuration in a remote
    config file.
    """

    # -- Package repo and release tag
    package_release: GithubReleaseRef
    # -- True iff the asset contains a ${PLATFORM} placeholder.
    platform_dependent: bool
    # -- The asset name.
    asset: str


@dataclass(frozen=True)
class RemoteConfigFileCrawl:
    """Crawling results of a single remote config file."""

    # -- Two num version of the file, e.g. (1, 5) for "1.7.x"
    # version_selector: Version
    # -- List of crawled package configurations..
    packages: Dict[str, RemoteConfigPackageCrawl]


@dataclass(frozen=True)
class RemoteConfigsCrawl:
    """Crawling results of all the remote config files."""

    remote_configs: Dict[str, RemoteConfigFileCrawl]


@dataclass(frozen=True)
class ReleaseCrawl:
    """Represents crawl information of a single repo release."""

    state: ReleaseState
    created_date: date


@dataclass(frozen=True)
class RepoCrawl:
    """Results of crawling a single repo"""

    # -- Maps release tag to release info. Order is
    # -- descending created_date.
    releases: Dict[str, ReleaseCrawl]


@dataclass(frozen=True)
class ReposCrawl:
    """The repos crawling results."""

    repos: Dict[str, RepoCrawl]

    def get_release_crawl(
        self, release: GithubReleaseRef, default: Any
    ) -> ReleaseCrawl | Any:
        """Lookup the given release crawl. If found, return it, otherwise
        return 'default'."""
        assert isinstance(release, GithubReleaseRef)

        # -- Lookup at repo level
        repo_crawl = self.repos.get(release.repo, None)
        if repo_crawl is None:
            return default

        # -- Lookup at release tag level
        assert isinstance(repo_crawl, RepoCrawl)
        release_crawl = repo_crawl.releases.get(release.tag, None)
        if repo_crawl is None:
            return default

        # -- All done.
        assert isinstance(release_crawl, ReleaseCrawl)
        return release_crawl


@dataclass(frozen=True)
class CrawlResults:
    """Contains the output of the crawl step with all the information
    collected.
    """

    # -- Results of crawling Apio CLI releases on Pypi.
    pypi_crawl: PypiCrawl
    # -- Results of crawling Apio VSCode releases on the VSCode Marketplace.
    vscode_marketplace_crawl: VscodeMarketplaceCrawl
    # -- Results of crawling the remote config files on fpgawars/apio.
    remote_configs_crawl: RemoteConfigsCrawl
    # -- Results of crawling the repos.
    repos_crawl: ReposCrawl


# # ---------- Analyzer output


# @dataclass
# class JanitorRequirements:
#     """Requirements that need to be satisfied."""

#     # -- Releases in use that should be stable (including latest)
#     release_should_be_stable: RequirementsSet
#     # -- Releases that should be marked latest
#     release_should_be_latest: RequirementsSet  # Singleton
#     # -- Release should be checked for consistency. We do this only
#     # -- for some of the repos.
#     release_should_be_consistent: ReleaseSet
#     # -- Draft releases that are old enough to be deleted.
#     draft_should_be_deleted: ReleaseSet
#     # -- Prereleases that are old enough to be deleted.
#     pre_release_should_be_deleted: ReleaseSet

#     def release_sets(self) -> dict[str, ReleaseSet]:
#         """Return a dict with the ReleaseSet fields of this instance.
#         Keys are string names and values are the sets. This methods
#         simplifies operations that applies to all the sets."""
#         result = {
#             f.name: getattr(self, f.name)
#             for f in fields(self)
#             if f.type is ReleaseSet or f.type == "ReleaseSet"
#         }
#         return result

#     def __post_init__(self):
#         """Sanity checks."""
#         release_sets = self.release_sets()
#         assert len(release_sets) == 5
#         for release_set in release_sets.values():
#             assert isinstance(release_set, ReleaseSet)

#     def get_repos(self) -> Set[str]:
#         """Returns the set of repos that have at least one requirement."""
#         repos: Set[str] = set()
#         for release_set in self.release_sets().values():
#             repos.update(release_set.repos())
#         return repos

#     def check_partitioning(
#         self,
#         requirements1: "JanitorRequirements",
#         requirements2: "JanitorRequirements",
#     ):
#         """Checks that the requirements in this object are properly
#         partitioned into requirements1 and requirements2 with no missing or
#         duplicates. The partitions typically represent success and failure
#         sets.
#         """
#         for name, release_set in self.release_sets().items():
#             release_set.check_partitioning(
#                 requirements1.release_sets()[name],
#                 requirements2.release_sets()[name],
#             )

#     @classmethod
#     def make_empty(cls) -> "JanitorRequirements":
#         """Make a new Requirements that contains no requirements."""
#         return JanitorRequirements(
#             release_should_be_stable=ReleaseSet(),
#             release_should_be_latest=ReleaseSet(),
#             release_should_be_consistent=ReleaseSet(),
#             draft_should_be_deleted=ReleaseSet(),
#             pre_release_should_be_deleted=ReleaseSet(),
#         )

#     def is_empty(self) -> bool:
#         """Returns True if there are no requirements."""
#         return all(len(s) == 0 for s in self.release_sets().values())


# @dataclass(frozen=True)
# class AnalysisResults:
#     """Contains the result of the analysis step."""

#     requirements: JanitorRequirements


# # ---------- Verifier output


# @dataclass(frozen=True)
# class VerificationResults:
#     """The results of the Verifier step."""

#     # -- An explicit pass/fail flag to make it accessible for the
#     # -- workflow using jq.
#     passed: bool

#     # -- Requirements that are not met.
#     failures: JanitorRequirements
#     # -- Requirements that are met.
#     successes: JanitorRequirements

#     def __post_init__(self):
#         """Sanity check."""
#         assert self.passed == self.failures.is_empty()
