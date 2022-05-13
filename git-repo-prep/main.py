import json
import logging
import os
import re
import shutil
from pathlib import Path
from shlex import split
from subprocess import PIPE, run
from typing import Any, Dict, List, Optional

SCRIPT_ROOT = Path(__file__).parent
REPO_PREP_SCRIPT = SCRIPT_ROOT/'index.ts'


class GHResponse:
    def __init__(self, response: bytes):
        self.response = response

    @property
    def text(self):
        return self.response.decode('utf-8').strip()

    @property
    def json(self):
        return json.loads(self.response)


def clone_repo(remote_repo: str, path: str):
    gh(f'repo clone "{remote_repo}" "{path}"')


class GitRepo:
    def __init__(self, path: str = ".", working_branch: str = 'main',
                 remote_repo: Optional[str] = None, create: bool = False):
        self.path = path
        self.working_branch = working_branch
        self.remote_repo = remote_repo
        self._init(create)

    def __call__(self, command: str) -> str:
        return sspawn(
            f'git -C "{self.path}" {command}').decode('utf-8').strip()

    @property
    def branch(self) -> str:
        return self('branch --show-current')

    @property
    def branches_local(self) -> List[str]:
        return [br.lstrip('*').strip() for br in self('branch -l').split('\n')]

    @property
    def branches_remote(self) -> List[str]:
        return list(
            filter(len, map(str.strip, self('branch -rl').split('\n'))))

    @property
    def tags(self) -> List[str]:
        return list(filter(len, map(str.strip, self('tag -l').split('\n'))))

    @property
    def has_changes(self) -> bool:
        return self('status -s') != ''

    def checkout(self, branch: str, create: bool = False):
        if create:
            self(f'checkout -b "{branch}"')
        else:
            self(f'checkout "{branch}"')
        self.working_branch = branch

    def commit_all(self, msg: str):
        if self.has_changes:
            self('add .')
            self(f'commit -m "{msg}"')

    def push_changes(self):
        if self(f'diff origin "{self.working_branch}"') != '':
            self(f'push origin "{self.working_branch}"')

    def clone_repo(self):
        parent_path = Path(self.path).parent
        parent_path.mkdir(parents=True, exist_ok=True)
        git_url = f'https://github.com/{self.remote_repo}.git'
        sspawn(f'git -C {parent_path} clone {git_url}')

    @staticmethod
    def configure_secrets():
        github_token = os.environ.get('GITHUB_TOKEN', None)
        if github_token is None:
            logging.warning('No GitHub creds, cannot access private repos')
            return
        creds_dir = Path.cwd()/'tmp-gh-creds'
        creds_file = creds_dir/'gh-creds'
        creds_dir.mkdir(parents=True, exist_ok=True)
        sspawn('git config --global credential.helper'
               f' "store --file={creds_file}"')
        creds_file.write_text(
            f'https://{github_token}:x-oauth-basic@github.com')

    def _init(self, create: bool = False):
        branch = None
        try:
            branch = self.branch
        except Exception:
            if self.remote_repo is not None:
                self.clone_repo()
            elif not create:
                raise
            else:
                self('init')
            branch = self.branch
        if branch != self.working_branch:
            branch = self.working_branch
            if self.has_changes:
                self('stash')
            if branch not in self.branches_local:
                self.checkout(branch, True)
            else:
                self.checkout(branch, False)
        if self.remote_repo is not None:
            self(f'pull origin "{branch}"')


def create_process(command: List[str]):
    logging.info(' '.join(command))
    return run(command, stdout=PIPE, stderr=PIPE)


def spawn(command: List[str]) -> bytes:
    p = create_process(command)
    if p.returncode != 0:
        if p.stderr:
            err = f'{command}: {p.stderr.decode("utf-8")}'
        else:
            err = f'ERROR: could not run {command}'
        raise Exception(err)
    return p.stdout


def sspawn(command: str) -> bytes:
    return spawn(split(command))


def gh(command: str) -> GHResponse:
    return GHResponse(spawn(['gh'] + split(command)))


def get_books_list() -> List[str]:
    cache = SCRIPT_ROOT/'books-list.json'
    if cache.exists():
        return json.loads(cache.read_bytes())
    response = gh('repo list openstax --private')
    books_list = [
        line.split('\t')[0]
        for line in response.text.split('\n')
        if 'osbooks-' in line]
    cache.write_text(json.dumps(books_list))
    return books_list


def get_approved_books() -> List[str]:
    abl_path = Path('approved-book-list.json')
    if not abl_path.exists():
        sspawn(f'wget {os.environ["ABL_URL"]}')
    abl = json.loads(abl_path.read_bytes())
    return [
        book['repository_name']
        for book in abl['approved_books']
    ]


def get_branches_to_delete(git: GitRepo):
    remote_branches = [
        bs.strip()
        for bs in git.branches_remote
        # filter out HEAD branch and 1e, 2e, etc.
        if 'HEAD' not in bs and re.match(r'\s*origin/[0-9]+e', bs) is None]
    # remove instead of filter: this ensures it exists
    remote_branches.remove('origin/main')
    return remote_branches


def cleanup_branches(git: GitRepo):
    for branch_spec in get_branches_to_delete(git):
        remote, branch = branch_spec.split('/')
        git(f'push "{remote}" --delete "{branch}"')


def get_tags_to_delete(git: GitRepo):
    return git.tags


def cleanup_tags(git: GitRepo):
    for tag in get_tags_to_delete(git):
        git(f'push origin --delete "{tag}"')


def remove_orphans(book_path: Path, directory_whitelist: List[Path]):
    p = create_process(split(f'poet orphans {book_path}'))

    # https://github.com/openstax/poet/blob/c3c6c37d43d60f4501aead37c43cbbb3faa24704/server/src/model/_cli.ts#L189
    if p.returncode != 111:
        return

    poet_errors = p.stderr.decode('utf-8').strip().split('\n')
    poet_output = p.stdout.decode('utf-8').strip().split('\n')

    for line in poet_errors:
        if 'Validation Errors' in line:
            error_count = int(line.split(':')[1].strip())
            raise Exception('Validation Errors:\n' +
                            '\n'.join(poet_output[:error_count]))

    orphans = filter(lambda p: p.exists(), map(Path, poet_output))

    total = 0
    for orphan in orphans:
        if (not orphan.is_file() or orphan.parent not in directory_whitelist):
            continue
        if orphan.name == 'index.cnxml':
            orphan.unlink()
            orphan.parent.rmdir()
        else:
            orphan.unlink()
        total += 1
        logging.info(f'Removing {orphan}')
    logging.info(f'Removed {total} orphan(s)')


def cleanup_files(git: GitRepo, book_path: Path):
    remove_orphans(book_path, [book_path])
    git.commit_all('Remove unnecessary files from root directory')


def ensure_correct_license(
    git: GitRepo,
    book_path: Path,
    book_meta: Dict[str, Any]
):
    license_dir = Path('licenses')
    slugs_meta = book_meta['slugsMeta']
    license_info = slugs_meta[0]['colMeta']['license']
    for slug_meta in slugs_meta[1:]:
        col_meta = slug_meta['colMeta']
        col_license_info = col_meta['license']
        if license_info != col_license_info:
            raise Exception('Licenses differ between collections')
    license_type = license_info['type']
    license_version = license_info['version']
    license_file = license_dir/f'{license_type}-{license_version}.txt'
    if not license_file.exists():
        logging.warning(f'Unknown license: {license_file}')
        return
    shutil.copy(license_file, book_path/'LICENSE')
    git.commit_all('Update LICENSE')


def run_repo_prep(git: GitRepo, book_path: Path):
    book_meta = json.loads(sspawn(f'ts-node {REPO_PREP_SCRIPT} {book_path}'))
    git.commit_all('Add README and repo settings')
    return book_meta


def update_path(new_segment: str):
    path = os.environ.get('PATH', None)
    if path is not None:
        os.environ['PATH'] = f'{new_segment}:{path}'
    else:
        os.environ['PATH'] = f'{new_segment}'


def install_gh_cli():
    ver = os.environ.get('GH_CLI_VERSION', '2.9.0')
    cli_root = f'gh_{ver}_linux_amd64'
    tar_file = f'gh_{ver}_linux_amd64.tar.gz'
    if not cli_bin.exists():
        tar_file_path = Path(tar_file)
        if not tar_file_path.exists():
            sspawn('wget https://github.com/cli/cli/releases/download/'
                   f'v{ver}/{tar_file}')
        sspawn(f'tar -xf {tar_file}')
        tar_file_path.unlink()
    update_path(Path(cli_root)/'bin')


def install_node_modules():
    node_modules = REPO_PREP_SCRIPT.parent/'node_modules'
    if not node_modules.exists():
        sspawn(f'npm install "{REPO_PREP_SCRIPT.parent}"')
    update_path(node_modules/'.bin')


def install_poet():
    poet_dir = SCRIPT_ROOT/'poet'
    _ = GitRepo(poet_dir, remote_repo='openstax/poet')
    update_path(poet_dir)


def list_prs():
    # Example return value:
    # number  title                                           status
    # 1       add style to META-INF/books.xml meta-inf-style  OPEN
    for book in get_approved_books():
        repo = f'openstax/{book}'
        print(sspawn(f'gh pr list -R {repo}').decode('utf-8'))


def init():
    logging.getLogger().setLevel(logging.INFO)
    env = SCRIPT_ROOT/'.env'
    if env.exists():
        for line in env.read_text().split('\n'):
            k, v = [s.strip() for s in line.split('=')]
            os.environ[k] = v
    install_node_modules()
    install_poet()
    # This was not needed after all
    # install_gh_cli()
    GitRepo.configure_secrets()
    sspawn('git config --global user.email "staxly@openstax.org"')
    sspawn('git config --global user.name "Staxly"')


def main():
    for book in get_approved_books():
        repo = f'openstax/{book}'
        book_path = Path(book)
        logging.info(f'\x1b[33m========> {repo} <========\x1b[37m')
        try:
            git = GitRepo(str(book_path), remote_repo=repo)
            print(f'Would remove {get_branches_to_delete(git)}')
            print(f'Would remove {get_tags_to_delete(git)}')
            cleanup_files(git, book_path)
            book_meta = run_repo_prep(git, book_path)
            ensure_correct_license(git, book_path, book_meta)
            # NOTE: These steps are commented out during testing because they
            #       all push changes to the Github repositories
            # cleanup_branches(git)
            # cleanup_tags(git)
            # git.push_changes()
        except Exception as e:
            logging.error(f'\x1b[31m{repo}: {e}\x1b[37m')


if __name__ == '__main__':
    init()
    main()
