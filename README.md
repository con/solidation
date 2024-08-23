`solidation` is a Python program for producing a Markdown report of recent
issue & pull request activity across a set of GitHub repositories.

# Usage

    solidation [<options>]

`solidation` reads from a configuration file (`solidation.yaml` by default,
though a different one can be specified with the `-c`/`--config` option) and
outputs a Markdown report to standard output.  It is recommended to set a
GitHub API token to use for API requests via the `GITHUB_TOKEN` environment
variable.

## Options

- `-c <FILE>`, `--config <FILE>` — Specify the configuration file to use;
  defaults to `solidation.yaml`.  See "Configuration" below for details.

- `-l <LEVEL>`, `--log-level <LEVEL>` — Set the log level to the given value.
  Possible values are "`CRITICAL`", "`ERROR`", "`WARNING`", "`INFO`", "`DEBUG`"
  (all case-insensitive) and their Python integer equivalents.  [default value:
  INFO]


# Configuration

The configuration file is a YAML file containing a mapping with the following
keys (all optional):

- `project` (string) — The name of the project to which the detailed
  repositories belong, used in the header of the report; defaults to "Project".

- `repositories` (list of mappings) — A list of repositories for which to fetch
  recent issue & pull request activity.  Each repository is specified as a
  mapping with the following fields:

    - `name` (string; required) — The name of the GitHub repository, in the
      form "OWNER/NAME"
    - `member_activity_only` (boolean) — Whether to restrict the issues & pull
      requests fetched for this repository to just those created or assigned to
      users listed in (or automatically added to) `members`; defaults to
      `false`

    As a convenience, a repository may instead be specified as just a string of
    the form "OWNER/NAME", which is equivalent to specifying a mapping with
    that as the `name` and the default values for all other fields.

- `organizations` (list of mappings) — A list of GitHub organizations whose
  repositories will all have their recent issue & pull request activity
  fetched.  Each organization is specified as a mapping with the following
  fields:

    - `name` (string; required) — The name of the GitHub organization
    - `fetch_members` (boolean or regex) — Whether to automatically add the
      organization's members to the `members` list; a value of `False` (the
      default) means to not add any members, a value of `True` means to add all
      members, and a regex value means to add those members whose login names
      match the given regex (anchored at the start)
    - `member_activity_only` (boolean) — Whether to restrict the issues & pull
      requests fetched for this organization's repositories to just those
      created or assigned to users listed in (or automatically added to)
      `members`; defaults to `false`

    As a convenience, an organization may instead be specified as just a
    string, which is equivalent to specifying a mapping with that as the `name`
    and the default values for all other fields.

- `members` (list of strings) — A list of the login names of GitHub users that
  should be considered part of the project being reported on; this can be
  automatically extended with one or more organizations' members by setting
  those organizations' `fetch_members` fields appropriately.  The list of
  members is used to filter out issues for the "Non-{project} member issues"
  section and to filter activity for repositories & organizations for which
  `member_activity_only` is true.

- `recent_days` (integer) — The number of days to look back for recent issue &
  pull request activity; defaults to 7.

- `num_oldest_prs` (integer) — Number of pull requests to list for the "oldest,
  open, non-draft PRs" section; defaults to 10.

- `max_random_issues` (integer) — Maximum number of issues to list for the
  "random open issues to fix" section; defaults to 5.


# Example Output

#### DataLad Health Update
##### Covered projects (PRs/issues/stars/watchers/forks)
[datalad](https://github.com/datalad/datalad) ([13](https://github.com/datalad/datalad/pulls)/[464](https://github.com/datalad/datalad/issues)/388/26/104); [dl-gooey](https://github.com/datalad/datalad-gooey) ([2](https://github.com/datalad/datalad-gooey/pulls)/[51](https://github.com/datalad/datalad-gooey/issues)/4/7/6); [dl-container](https://github.com/datalad/datalad-container) ([2](https://github.com/datalad/datalad-container/pulls)/[30](https://github.com/datalad/datalad-container/issues)/9/9/14); [dl-deprecated](https://github.com/datalad/datalad-deprecated) ([2](https://github.com/datalad/datalad-deprecated/pulls)/[34](https://github.com/datalad/datalad-deprecated/issues)/0/7/3); [dl-metalad](https://github.com/datalad/datalad-metalad) ([2](https://github.com/datalad/datalad-metalad/pulls)/[110](https://github.com/datalad/datalad-metalad/issues)/9/9/10); [dl-fuse](https://github.com/datalad/datalad-fuse) ([2](https://github.com/datalad/datalad-fuse/pulls)/[19](https://github.com/datalad/datalad-fuse/issues)/1/4/2); [dl-catalog](https://github.com/datalad/datalad-catalog) ([2](https://github.com/datalad/datalad-catalog/pulls)/[47](https://github.com/datalad/datalad-catalog/issues)/10/8/9); [dl-neuroimaging](https://github.com/datalad/datalad-neuroimaging) ([4](https://github.com/datalad/datalad-neuroimaging/pulls)/[27](https://github.com/datalad/datalad-neuroimaging/issues)/16/12/13); [dl-ukbiobank](https://github.com/datalad/datalad-ukbiobank) ([0](https://github.com/datalad/datalad-ukbiobank/pulls)/[10](https://github.com/datalad/datalad-ukbiobank/issues)/4/5/8); [dl-installer](https://github.com/datalad/datalad-installer) ([0](https://github.com/datalad/datalad-installer/pulls)/[3](https://github.com/datalad/datalad-installer/issues)/4/4/2); [dl-osf](https://github.com/datalad/datalad-osf) ([1](https://github.com/datalad/datalad-osf/pulls)/[18](https://github.com/datalad/datalad-osf/issues)/13/12/11); [dl-crawler](https://github.com/datalad/datalad-crawler) ([0](https://github.com/datalad/datalad-crawler/pulls)/[34](https://github.com/datalad/datalad-crawler/issues)/5/9/16); [dl-xnat](https://github.com/datalad/datalad-xnat) ([1](https://github.com/datalad/datalad-xnat/pulls)/[13](https://github.com/datalad/datalad-xnat/issues)/3/12/8); [dl-next](https://github.com/datalad/datalad-next) ([4](https://github.com/datalad/datalad-next/pulls)/[47](https://github.com/datalad/datalad-next/issues)/4/8/6); [dl-dataverse](https://github.com/datalad/datalad-dataverse) ([3](https://github.com/datalad/datalad-dataverse/pulls)/[24](https://github.com/datalad/datalad-dataverse/issues)/9/8/10); [dl-ebrains](https://github.com/datalad/datalad-ebrains) ([0](https://github.com/datalad/datalad-ebrains/pulls)/[8](https://github.com/datalad/datalad-ebrains/issues)/1/4/4); [datasets.datalad.org](https://github.com/datalad/datasets.datalad.org) ([0](https://github.com/datalad/datasets.datalad.org/pulls)/[31](https://github.com/datalad/datasets.datalad.org/issues)/6/5/4); [datalad.org](https://github.com/datalad/datalad.org) ([1](https://github.com/datalad/datalad.org/pulls)/[8](https://github.com/datalad/datalad.org/issues)/5/13/10); [dl-mihextras](https://github.com/mih/datalad-mihextras) ([1](https://github.com/mih/datalad-mihextras/pulls)/[2](https://github.com/mih/datalad-mihextras/issues)/1/2/1); [dl-debian](https://github.com/psychoinformatics-de/datalad-debian) ([4](https://github.com/psychoinformatics-de/datalad-debian/pulls)/[39](https://github.com/psychoinformatics-de/datalad-debian/issues)/1/7/5)
##### Non-DataLad member issues active/opened in the last 7 days
- [RFE: Add environment variables option](https://github.com/datalad/datalad-container/issues/194) by Austin Macdonald [datalad/datalad-container]
- [ main:Database.Handle error](https://github.com/datalad/datalad/issues/7278) by Dorota Jarecka [datalad/datalad]
##### Issues opened in last 7 days: 10
##### Untriaged issues of the last 7 days
- [Handle unknown root-dataset identifier](https://github.com/datalad/datalad-metalad/issues/317) [datalad/datalad-metalad]
- [Appveyor tests stall on MacOS](https://github.com/datalad/datalad-neuroimaging/issues/116) [datalad/datalad-neuroimaging]
- [Read the Docs builds failing](https://github.com/datalad/datalad-neuroimaging/issues/117) [datalad/datalad-neuroimaging]
- [Webdav clone - empty repository](https://github.com/datalad/datalad-next/issues/233) [datalad/datalad-next]
- [Extend ``meta-dumps`` path-parameter to include metadata format as a selection criteria](https://github.com/datalad/datalad-metalad/issues/318) [datalad/datalad-metalad]
- [Consider using `sphinx-jsonschema` to render schema in docs](https://github.com/datalad/datalad-catalog/issues/249) [datalad/datalad-catalog]
- [Warn about extractor parameter when using legacy extractors](https://github.com/datalad/datalad-metalad/issues/319) [datalad/datalad-metalad]
- [Installing git-annex via deb-url failed in an Appveyor CI run](https://github.com/datalad/datalad-installer/issues/146) [datalad/datalad-installer]
##### Max 10 oldest, open, non-draft PRs (46 PRs open in total)
- [Add external links to files (if available) and display in context menu](https://github.com/datalad/datalad-deprecated/pull/37) (517 days)
- [add version handling](https://github.com/datalad/datalad-dataverse/pull/103) (241 days)
- [`git annex testremote` may run into path length issues on windows](https://github.com/datalad/datalad-dataverse/pull/128) (224 days)
- [Addressing #39](https://github.com/psychoinformatics-de/datalad-debian/pull/98) (217 days)
- [Configure builder args](https://github.com/psychoinformatics-de/datalad-debian/pull/104) (217 days)
- [Equip `GitRepo.diffstatus()` with typechange detection](https://github.com/datalad/datalad-next/pull/91) (205 days)
- [Update walkthrough_collab.rst](https://github.com/psychoinformatics-de/datalad-debian/pull/142) (175 days)
- [ENH: add web-based metadata entry with HTML/JS and `QWebEngineView`](https://github.com/datalad/datalad-gooey/pull/319) (126 days)
- [Use datalad-nexts constraints system](https://github.com/datalad/datalad-gooey/pull/401) (116 days)
- [MNT: add gooey to index page](https://github.com/datalad/datalad.org/pull/126) (102 days)
##### 5 random open issues to fix (of a total of 1038)
- [What is needed to publish metadata?](https://github.com/datalad/datalad-metalad/issues/91) (693 days old)
- [Creating a new subject subdataset in a large superdataset takes a long time](https://github.com/datalad/datalad/issues/5283) (769 days old)
- [Update an open metadata editor widget when selected browser item changes](https://github.com/datalad/datalad-gooey/issues/320) (125 days old)
- [Develop  FAIRly-big inspired build workflow and user-facing tooling (possibly as datalad commands in an extension)](https://github.com/psychoinformatics-de/datalad-debian/issues/23) (272 days old)
- [Improve rendering of project or subject lists ](https://github.com/datalad/datalad-xnat/issues/45) (503 days old)
##### Active issues in the past 7 days: 22 (2%)
- Commenters: mih (10), yarikoptic (9), djarecka (3), jwodder (2), christian-monch (2), mattcieslak (1)
##### Issues closed in the past 7 days: 8
- Age quantiles (days): [0.75, 3.5, 5.5]
- Closed by: yarikoptic (5), mih (3)

##### PRs completed in the past 7 days: 13
- Proposed by: mih (6), jwodder (4), TheChymera (1), mslw (1), jsheunis (1)
- Merged by: mih (6), yarikoptic (4), bpoldrack (1), christian-monch (1), jsheunis (1)
- PR duration quantiles (days): [0.0, 0.0, 5.0]
