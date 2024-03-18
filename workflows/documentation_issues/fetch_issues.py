#!/usr/bin/env python
"""
Write CSV table with Subproject's issues labeled as 'documentation'

The list of subprojects to query is provided in `DEFAULT_REPOS_FILE` variable,
entries in this file are repository names in GitHub -- *fullnames --,
specified as "{org}/{repository}" (eg, `jupyterlab/jupyterlab`).

The repositories are queried for all their issues with 'documetation' label.
For each issue returned, we take note of its `number` (ID), title, and URL.

The answer is written as a CSV table with fields defined in FIELDNAMES_CSV.
"""

## Repositories to query
DEFAULT_REPOS_FILE='repos.txt'
#
## Output table filename
DEFAULT_ISSUES_FILE='issues.csv'

# Table columns
FIELDNAMES = ['repo', 'number', 'title', 'url', 'date']


import csv
import requests


def read_repos(filename):
    """
    Return list of repositories in 'filename'.

    Example 'filename':
    $ cat > filename.txt << EOF
    jupyterlab/jupyterlab
    jupyterlab/jupyterlab-desktop
    jupyter/notebook
    jupyterhub/jupyterhub
    EOF
    """
    with open(filename) as file:
        lines = file.readlines()
    lines = [ line.strip() for line in lines ]
    lines = [ line for line in lines if line and line[0] != '#' ]
    return lines


def fetch_issues(repo, label='documentation'):
    """
    Query Github repos for issues with 'label'
    """
    url = f"https://api.github.com/repos/{repo}/issues?labels={label}"
    response = requests.get(url)
    issues = {}
    if response.status_code == 200:
        for issue in response.json():
            key = f"{repo}:{issue['number']}"
            issues[key] = {
                'title': issue['title'],
                'url': issue['html_url'],
                'date': issue['created_at'][:10]
            }
    return issues


# CSV reader/writer arguments for our 'issues' file
_CSV_ARGS = dict(
    fieldnames = FIELDNAMES,
    quoting = csv.QUOTE_NONNUMERIC,
)


def write_issues(issues, filename):
    """
    Write 'issues' to CSV 'filename'.

    Write a Markdown version if 'write_md'.
    Write an HTML version if 'write_html'.

    Return list of filename(s) created.
    """
    with open(filename, 'w') as file:
        writer = csv.DictWriter(file, **_CSV_ARGS)
        # Write header line (ie, fieldnames)
        writer.writeheader()
        for key,issue in issues.items():
            repo, number = key.split(':')
            issue.update({'repo':repo, 'number':number})
            writer.writerow(issue)

    return filename


def read_issues(filename:str) -> dict:
    """
    Return dictionary with issues from CSV 'filename'

    Supposed 'filename' (CSV) table has the following lines::

        "repo","number","title","url"
        "orgA/repo1","27","Improve something","url-A1"
        "orgA/repo2","99","Improve anotherthing","url-A2"
        "orgB/repo1","12","Fix stuff","url-B1"

    The return issues object will be::

        {
            'orgA/repo1:27' : {
                'title' : 'Improve something',
                'url' : 'url-A1'
            },
            'orgA/repo2:99' : {
                'title' : 'Improve anotherthing',
                'url' : 'url-A2'
            },
            'orgB/repo1:12' : {
                'title' : 'Fix stuff',
                'url' : 'url-B1'
            }
        }
    """
    issues = {}
    with open(filename) as file:
        reader = csv.DictReader(file, **_CSV_ARGS)
        # Escape the first/header line
        next(reader)
        for issue in reader:
            repo = issue.pop('repo')
            number = issue.pop('number')
            key = f"{repo}:{number}"
            issues[key] = issue
    return issues


def main(repos_file, issues_file):
    """
    Write CSV file from 'documentation' issues from 'repos_source.txt' file

    Github repositories listed in 'repos.list' file are queried for issues
    with label 'documentation' associated. Title, URL, and issue's number
    are collected and written in 'issues.csv'.
    """
    ## Issues' label (applied to all repos)
    label = 'documentation'

    ## Read list of repositories
    repos = read_repos(repos_file)

    ## Query repos for issues with 'label'
    issues = {}
    for repo in repos:
        print(f"Querying repo: '{repo}'")
        issues.update(
            fetch_issues(repo, label=label)
            )

    print(f"{len(issues)} issues found.")

    ## Write "new-current" list of issues
    csv_file = write_issues(issues, issues_file)
    print("Issues CSV table:", csv_file)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_REPOS_FILE,
                        help="Filename with list of Jupyter repos")
    parser.add_argument("--output", default=DEFAULT_ISSUES_FILE,
                        help="Filename for issues table (CSV)")
    args = parser.parse_args()

    main(
        repos_file=args.input,
        issues_file=args.output
        )
