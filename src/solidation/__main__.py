from __future__ import annotations
from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, dataclass, field
from datetime import datetime, timedelta, timezone
import logging
import os
from pathlib import Path
from random import sample
from statistics import quantiles
from typing import TYPE_CHECKING, Any, List
import click
from click_loglevel import LogLevel
from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from pydantic import BaseModel, Field, constr
from ruamel.yaml import YAML
from . import __version__

log = logging.getLogger("solidation")

if TYPE_CHECKING:
    GHUser = str
    GHRepo = str
else:
    GHUser = constr(regex=r"^[-_A-Za-z0-9]+$")
    GHRepo = constr(regex=r"^[-_A-Za-z0-9]+/[-_.A-Za-z0-9]+$")


class Configuration(BaseModel):
    project: str = "Project"
    recent_days: int = Field(default=7, ge=1)
    repositories: List[GHRepo]
    members: List[GHUser]


@dataclass
class Consolidator:
    token: InitVar[str]
    gh: Github = field(init=False)
    config: Configuration
    since: datetime = field(init=False)

    def __post_init__(self, token: str) -> None:
        self.gh = Github(token)
        self.since = datetime.now(timezone.utc) - timedelta(
            days=self.config.recent_days
        )

    def run(self) -> Report:
        repostats = {}
        open_prs = []
        active_issues = []
        active_prs = []
        open_ip = []
        for rn in self.config.repositories:
            details = self.process_repo(rn)
            repostats[rn] = details
            open_prs.extend(details.open_prs)
            active_issues.extend(details.active_issues)
            active_prs.extend(details.active_prs)
            open_ip.extend(details.open_ip)
        return Report(
            config=self.config,
            repostats=repostats,
            open_prs=open_prs,
            active_issues=active_issues,
            active_prs=active_prs,
            open_ip=open_ip,
        )

    def process_repo(self, reponame: str) -> RepoDetails:
        log.info("Processing repo %s", reponame)
        repo = self.gh.get_repo(reponame)
        active_ip = repo.get_issues(state="all", since=self.since)
        return RepoDetails(
            full_name=repo.full_name,
            size=repo.size,
            stargazers_count=repo.stargazers_count,
            watchers_count=repo.watchers_count,
            forks_count=repo.forks_count,
            open_issues_count=repo.open_issues_count,
            network_count=repo.network_count,
            subscribers_count=repo.subscribers_count,
            open_prs=list(repo.get_pulls(state="open")),
            active_prs=[i for i in active_ip if i.pull_request],
            active_issues=[i for i in active_ip if i.pull_request is None],
            open_ip=list(repo.get_issues(state="open")),
        )


@dataclass
class RepoDetails:
    full_name: str
    size: int
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    network_count: int
    subscribers_count: int
    open_prs: list[PullRequest]
    active_prs: list[Issue]
    active_issues: list[Issue]
    open_ip: list[Issue]

    @property
    def open_prs_count(self) -> int:
        return len(self.open_prs)


@dataclass
class Report:
    config: Configuration
    repostats: dict[str, RepoDetails]
    open_prs: list[PullRequest]
    active_issues: list[Issue]
    active_prs: list[Issue]
    # Open issues and PRs:
    open_ip: list[Issue]

    def get_issue_commenter_count(self, since: datetime) -> Counter[str]:
        commenters: Counter[str] = Counter()
        for i in self.active_issues:
            for c in i.get_comments():
                if since > ensure_aware(c.created_at):
                    # does not fall into the reporting window
                    continue
                commenters[c.user.login] += 1
        return commenters

    def to_markdown(self) -> str:
        now = datetime.now(timezone.utc)
        dayscovered = self.config.recent_days
        since = now - timedelta(days=dayscovered)

        s = f"#### {self.config.project} Health Update\n"
        s += "##### Covered projects (PRs/issues/stars/watchers/forks)\n"
        s += (
            "; ".join(
                f"[{k.split('/')[-1].replace('datalad-', 'dl-')}]"
                f"(https://github.com/{k})"
                f" ([{v.open_prs_count}](https://github.com/{k}/pulls)/"
                f"[{v.open_issues_count}](https://github.com/{k}/issues)/"
                f"{v.stargazers_count}/{v.subscribers_count}/{v.forks_count})"
                for k, v in self.repostats.items()
            )
        ) + "\n"

        outsider_issues = [
            i
            for i in self.active_issues
            if i.state == "open" and i.user.login not in self.config.members
        ]
        if outsider_issues:
            s += (
                f"##### Non-{self.config.project} member issues active/opened"
                f" in the last {dayscovered} days\n"
            )
            for i in sorted(outsider_issues, key=lambda x: x.number):
                s += (
                    f"- [{i.title}]({i.html_url}) by {i.user.name}"
                    f" [{i.repository.full_name}]\n"
                )

        recently_opened_issues = [
            i for i in self.active_issues if ensure_aware(i.created_at) >= since
        ]
        if recently_opened_issues:
            s += (
                f"##### Issues opened in the last {dayscovered} days:"
                f" {len(recently_opened_issues)}\n"
            )

        untriaged_issues = [
            i
            for i in self.active_issues
            if i.state == "open" and i.comments < 1 and not i.labels
        ]
        if untriaged_issues:
            s += "##### Untriaged issues of the last {dayscovered} days\n"
            for i in sorted(untriaged_issues, key=lambda x: x.created_at):
                s += f"- [{i.title}]({i.html_url}) [{i.repository.full_name}]\n"

        s += (
            f"##### Max 10 oldest, open, non-draft PRs ({len(self.open_prs)}"
            " PRs open in total)\n"
        )
        for pr in sorted(
            (p for p in self.open_prs if not p.draft), key=lambda x: x.created_at
        )[:10]:
            age = now - ensure_aware(pr.created_at)
            s += f"- [{pr.title}]({pr.html_url}) ({age.days} days)\n"

        n_random_ip = min(5, len(self.open_ip))
        if n_random_ip:
            s += (
                f"##### {n_random_ip} random open issues to fix (of a total of"
                f" {len(self.open_ip)})\n"
            )
            # Shuffle self.open_ip without changing the original list:
            for i in sample(self.open_ip, len(self.open_ip)):
                if i.pull_request is not None:
                    # Note: Trying to do this filtering on all issues before
                    # shuffling apparently results in an API request for each
                    # issue, which slows things down considerably.
                    continue
                age = now - ensure_aware(i.created_at)  # type: ignore[unreachable]
                s += f"- [{i.title}]({i.html_url}) ({age.days} days old)\n"
                n_random_ip -= 1
                if n_random_ip == 0:
                    break

        s += (
            f"##### Active issues in the past {dayscovered} days: "
            f"{len(self.active_issues)} "
            f"({len(self.active_issues) / len(self.open_ip) * 100:.0f}%)\n"
        )
        s += (
            "- Commenters: "
            + ", ".join(
                f"{user} ({qty})"
                for user, qty in self.get_issue_commenter_count(since).most_common()
            )
            + "\n"
        )

        recent_closed_issues = [i for i in self.active_issues if i.state == "closed"]
        if recent_closed_issues:
            s += (
                f"##### Issues closed in the past {dayscovered} days:"
                f" {len(recent_closed_issues)}\n"
            )
            closed_age = [
                (i.closed_at - i.created_at).days for i in recent_closed_issues
            ]
            s += f"- Age quantiles (days): {quantiles(closed_age)}\n"
            s += (
                "- Closed by: "
                + ", ".join(
                    f"{user} ({qty})"
                    for user, qty in get_by_counts(
                        recent_closed_issues, "closed_by"
                    ).most_common()
                )
                + "\n"
            )
        recent_closed_prs = [
            i.as_pull_request() for i in self.active_prs if i.state == "closed"
        ]
        if recent_closed_prs:
            s += (
                f"##### PRs completed in the past {dayscovered} days:"
                f" {len(recent_closed_prs)}\n"
            )

        merged_prs = [i for i in recent_closed_prs if i.merged_at]
        if merged_prs:
            for label, attr in (("Proposed", "user"), ("Merged", "merged_by")):
                s += (
                    f"- {label} by: "
                    + ", ".join(
                        f"{user} ({qty})"
                        for user, qty in get_by_counts(merged_prs, attr).most_common()
                    )
                    + "\n"
                )
            pr_durations = [(i.merged_at - i.created_at).days for i in merged_prs]
            s += f"- PR duration quantiles (days): {quantiles(pr_durations)}\n"
        return s


def get_by_counts(iterable: Iterable[Any], attr: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for i in iterable:
        name = getattr(i, attr).login
        counts[name] += 1
    return counts


def ensure_aware(dt: datetime) -> datetime:
    # Pygithub returns naïve datetimes for timestamps with a "Z" suffix.  Until
    # that's fixed <https://github.com/PyGithub/PyGithub/pull/1831>, we need to
    # make such datetimes timezone-aware manually.
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


@click.command()
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="solidation.yaml",
    help="Read configuration from the given file",
    show_default=True,
)
@click.option(
    "-l",
    "--log-level",
    type=LogLevel(),
    default=logging.INFO,
    help="Set logging level  [default: INFO]",
)
def main(config: Path, log_level: int) -> None:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=log_level,
    )
    log.info("solidation %s", __version__)
    with config.open() as fp:
        cfg = Configuration.parse_obj(YAML(typ="safe").load(fp))
    cs = Consolidator(token=os.environ["GITHUB_TOKEN"], config=cfg)
    report = cs.run()
    print(report.to_markdown(), end="")


if __name__ == "__main__":
    main()
