#/usr/bin/env python3

import sys
import os
from datetime import datetime
from github import Github
from pathlib import Path
from pprint import pprint

repos = (
    'datalad/datalad',
    'datalad/datalad-gooey',
    'datalad/datalad-container',
    'datalad/datalad-deprecated',
    'datalad/datalad-metalad',
    'datalad/datalad-fuse',
    'datalad/datalad-catalog',
    'datalad/datalad-neuroimaging',
    'datalad/datalad-ukbiobank',
    'datalad/datalad-installer',
    'datalad/datalad-osf',
    'datalad/datalad-crawler',
    'datalad/datalad-xnat',
    'datalad/datalad-next',
    'datalad/datalad-dataverse',
    'datalad/datalad-ebrains',
    'datalad/datalad-fuse',
    'datalad/datasets.datalad.org',
    'datalad/datalad.org',
    'mih/datalad-mihextras',
    'psychoinformatics-de/datalad-debian',
)

members = (
    'adswa', 'yarikoptic', 'mih', 'jsheunis', 'jwodder', 'bpoldrack',
    'christian-monch', 'mslw', 'kyleam',
)


class HealthReport(object):
    def __init__(self, github_token, project="Project", basepath=None, recent_days=7, repos=None, members=None):
        self.basepath = Path(basepath) if basepath else Path.cwd()
        self.gh = Github(github_token)
        self.issues_since = datetime.fromtimestamp(
            datetime.utcnow().timestamp() - recent_days * 24 * 3600)
        self.project = project
        self.repos = repos
        self.open_prs = []
        self.active_issues = []
        self.active_prs = []
        # open issues and PRs
        self.open_ip = []
        if members is None:
            raise NotImplemented("Pick up all members")
            # something like flattening of
            # members = list(set(sum(
            #     (
            #         m.login for m in self.gh.get_organization(o).get_members()
            #         for o in set(r.split('/')[0] for r in repos)
            #     ),
            #     []
            # )))
        self.members = members

    def get_repo_status(self, repo):
        retrieve = (
            'full_name', 'size', 'stargazers_count', 'watchers_count',
            'forks_count', 'open_issues_count', 'network_count',
            'subscribers_count',
        )
        props = {
            k: getattr(repo, k)
            for k in retrieve
        }
        return props

    def proc_repo(self, name):
        repo = self.gh.get_repo(name)
        # basic status scores
        rstatus = self.get_repo_status(repo)
        # we already have open issue count, get open PRs too
        open_prs = repo.get_pulls(state='open')
        rstatus['open_prs_count'] = open_prs.totalCount
        self.repostats[name] = rstatus
        # write to a JSON file per repo
        # the git history will have the longitudinal change wrt these scores
        #status_dir = self.basepath / 'status'
        #status_dir.mkdir(parents=True, exist_ok=True)
        #with (status_dir / (name.replace('/', '__') + '.json')).open('w') as f:
        #    json.dump(rstatus, f)
        active_ip = repo.get_issues(state='all', since=self.issues_since)
        active_issues = (i for i in active_ip if i.pull_request is None)
        active_prs = (i for i in active_ip if i.pull_request)
        open_issuesprs = repo.get_issues(state='open')
        return dict(
            open_prs=open_prs,
            active_prs=active_prs,
            active_issues=active_issues,
            open_ip=open_issuesprs,
        )

    def get_issue_commenter_count(self):
        commenters = {}
        for i in self.active_issues:
            for c in i.get_comments():
                if self.issues_since > c.created_at:
                    # does not fall into the reporting window
                    continue
                count = commenters.get(c.user.login, 0)
                commenters[c.user.login] = count + 1
        return commenters

    def main(self):
        # to aggregate issues across all repos
        self.repostats = {}
        self.open_prs = []
        self.active_issues = []
        self.active_prs = []
        self.open_ip = []
        for rn in self.repos:
            props = self.proc_repo(rn)
            self.open_prs.extend(props['open_prs'])
            self.active_issues.extend(props['active_issues'])
            self.active_prs.extend(props['active_prs'])
            self.open_ip.extend(props['open_ip'])

    def render_matrix_summary(self):
        import statistics
        now = datetime.utcnow()
        dayscovered = (now - self.issues_since).days

        print(f'#### {self.project} Health Update')
        print(f'##### Covered projects (PRs/issues/stars/watchers/forks)')
        print('; '.join(
            f"[{k.split('/')[-1].replace('datalad-', 'dl-')}](https://github.com/{k})"
            f" ([{v['open_prs_count']}](https://github.com/{k}/pulls)/"
            f"[{v['open_issues_count']}](https://github.com/{k}/issues)/"
            f"{v['stargazers_count']}/{v['subscribers_count']}/{v['forks_count']})"
            for k, v in self.repostats.items()
        ))

        non_dl_issues = [
            i for i in self.active_issues
            if i.state == 'open' and i.user.login not in self.members
        ]
        if non_dl_issues:
            print(f'##### Non-{self.project} member issues active/opened in the last '
                  f'{dayscovered} days')
            for i in sorted(non_dl_issues, key=lambda x: x.number):
                age = now - i.created_at
                print(f'- [{i.title}]({i.html_url}) by {i.user.name} [{i.repository.full_name}]')

        recently_opened_issues = [
            i for i in self.active_issues if i.created_at >= self.issues_since
        ]
        if recently_opened_issues:
            print('##### Issues opened in last '
                  f'{dayscovered} days: {len(recently_opened_issues)}')
        untriaged_issues = [
            i for i in self.active_issues
            if i.state == 'open' and i.comments < 1 and not i.labels
        ]
        if untriaged_issues:
            print('##### Untriaged issues of the last '
                  f'{dayscovered} days')
            for i in sorted(untriaged_issues, key=lambda x: x.created_at):
                age = now - i.created_at
                print(f'- [{i.title}]({i.html_url}) [{i.repository.full_name}]')

        print(f'##### Max 10 oldest, open, non-draft PRs ({len(self.open_prs)} PRs open in total)')
        pr_count = 10
        for pr in sorted((p for p in self.open_prs if not p.draft),
                         key=lambda x: x.created_at):
            pr_count -= 1
            age = now - pr.created_at
            print(f"- [{pr.title}]({pr.html_url}) ({age.days} days)")
            if not pr_count:
                break
        n_random_ip = min(5, len(self.open_ip))
        if n_random_ip:
            print(f'##### {n_random_ip} random open issues to fix (of a total of {len(self.open_ip)})')
            from random import shuffle
            idx = list(range(len(self.open_ip)))
            shuffle(idx)
            count = 0
            while n_random_ip:
                i = self.open_ip[idx[count]]
                if i.pull_request is not None:
                    count += 1
                    continue
                print(f'- [{i.title}]({i.html_url}) ({(now - i.created_at).days} days old)')
                n_random_ip -= 1
                count += 1

        print(f'##### Active issues in the past {dayscovered} days: '
              f'{len(self.active_issues)} '
              f'({len(self.active_issues) / len(self.open_ip) * 100:.0f}%)')
        print('- Commenters:', ', '.join([
            f"{k[0]} ({k[1]})"
            for k in sorted(self.get_issue_commenter_count().items(),
                            key=lambda x: x[1],
                            reverse=True)
        ]))
        recent_closed_issues = [
            i for i in self.active_issues if i.state == 'closed'
        ]
        if recent_closed_issues:
            print(f'##### Issues closed in the past {dayscovered} days: {len(recent_closed_issues)}')
            closed_age = [
                (i.closed_at - i.created_at).days for i in recent_closed_issues
            ]
            print(f'- Age quantiles (days): {statistics.quantiles(closed_age)}')
            print('- Closed by:', ', '.join([
                f"{k[0]} ({k[1]})"
                for k in sorted(
                    get_by_counts(recent_closed_issues, 'closed_by').items(),
                    key=lambda x: x[1],
                    reverse=True)
            ]))
        recent_closed_prs = [
            i.as_pull_request() for i in self.active_prs if i.state == 'closed'
        ]
        if recent_closed_prs:
            print(f'##### PRs completed in the past {dayscovered} days: {len(recent_closed_prs)}')

        merged_prs = [i for i in recent_closed_prs if i.merged_at]
        if merged_prs:
            for label, attr in (('Proposed', 'user'),
                                ('Merged', 'merged_by')):
                print(f'- {label} by:', ', '.join([
                    f"{k[0]} ({k[1]})"
                    for k in sorted(
                        get_by_counts(merged_prs, attr).items(),
                        key=lambda x: x[1],
                        reverse=True)
                ]))
            pr_durations = [
                (i.merged_at - i.created_at).days for i in merged_prs]
            print(f'- PR duration quantiles (days): {statistics.quantiles(pr_durations)}')


def get_by_counts(iter, attr):
    counts = {}
    for i in iter:
        name = getattr(i, attr).login
        count = counts.get(name, 0)
        counts[name] = count + 1
    return counts


if __name__ == '__main__':
    dh = HealthReport(
        os.environ['GITHUB_TOKEN'],
        basepath=sys.argv[1] if len(sys.argv) > 1 else None,
        project="DataLad",
        repos=repos,
        members=members,
    )
    dh.main()
    dh.render_matrix_summary()
    #print('\n\n')
    #rl = dh.gh.get_rate_limit()
    #pprint(rl.raw_data['core'])
