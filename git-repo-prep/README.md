This script prepares book repositories for going public.

Staxly is the mechanism that actually makes the repositories public based on the settings in .github/settings.yml.

## What does this script do for each book in the ABL?

1. Remove `*.vsix` files from repositories
1. Remove `canonical.json` from repositories
1. Generate `README.md` based on the templates in `git-repo-prep/static`
1. Copy `git-repo-prep/static/repo-settings` into the repository
1. Remove all branches that DO NOT conform to the regex `[0-9]+e` (1e, 2e, etc.)
1. Remove all tags
1. Ensure that all collections use the same license
1. Ensure that the correct license is used
1. Push the above changes to Github (only when there are not any errors)

## Is it idempotent?
The entire process is based on git commits. Consequently, if there are not changes detected by git, no changes are committed.

## How can I run it?

Make a copy of .env.example and rename it to .env.
Generate a token for your GitHub account that has repository access.
Paste your GitHub token in .env next to GITHUB_TOKEN=

**NOTE** By default, the script will not make changes to the live repositories online. If you want to push changes add an argument the the script with a value of `p`, `push`, or `sync`.

**NOTE** The script will set your git user to `Staxly` globally. You should reset it when you are done. This should really be done automatically, but it is not.

Run it:
```bash
# dry run
python3 main.py
# push changes
python3 main.py push
```

Dependencies:
- nodejs/npm
- python3
- wget
- git