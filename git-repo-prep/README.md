This script prepares book repositories for going public.

Staxly is the mechanism that actually makes the repositories public based on the settings in .github/settings.yml.

## What does this script do for each book in the ABL?

1. Remove `*.vsix` files from repositories
1. Remove `canonical.json` from repositories
1. Generate `README.md` based on the templates in `git-repo-prep/static`
1. Copy `git-repo-prep/static/repo-settings` into the repository
1. Remove all branches that DO NOT conform to the regex `[0-9]+e` (1e, 2e, etc.)
1. Remove all tags that DO conform to the regex `[0-9]+(rc){0,1}` (1, 1rc, etc.)
1. Ensure that all collections use the same license
1. Ensure that the correct license is used
1. Push the above changes to Github (only when there are not any errors)

## Is it idempotent?
The entire process is based on git commits. Consequently, if there are not changes detected by git, no changes are committed.

## How can I run it?

Make a copy of .env.example and rename it to .env.
Generate a token for your GitHub account that has repository access.
Paste your GitHub token in .env next to GITHUB_TOKEN=

**NOTE** these functions will make changes to the live repositories online: make sure they are commented out in main.py if you do not wish to push changes. (They are commented out at the time of writing this)
- cleanup_branches(git)
- cleanup_tags(git)
- git.push_changes()

Run it:
```bash
python3 main.py
```

Dependencies:
- npm
- python3
- wget
- git