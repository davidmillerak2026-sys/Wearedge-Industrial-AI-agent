#!/usr/bin/env bash
set -Eeuo pipefail

REMOTE="${WEAREDGE_ALIGN_REMOTE:-origin}"
BRANCH="${WEAREDGE_ALIGN_BRANCH:-main}"
BACKUP_ROOT="${WEAREDGE_ALIGN_BACKUP_ROOT:-$HOME/wearedge-worktree-backups}"
MODE="${1:---backup-only}"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/jetson_workspace_backup_align.sh --backup-only
  bash scripts/jetson_workspace_backup_align.sh --align

Modes:
  --backup-only  Capture local status, diffs, untracked files, and metadata only.
  --align        Capture backups, create a safety stash, then align this worktree to origin/main.

Environment:
  WEAREDGE_ALIGN_REMOTE       Default: origin
  WEAREDGE_ALIGN_BRANCH       Default: main
  WEAREDGE_ALIGN_BACKUP_ROOT  Default: $HOME/wearedge-worktree-backups
USAGE
}

if [[ "$MODE" != "--backup-only" && "$MODE" != "--align" ]]; then
  usage
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

RUN_ID="jetson-align-$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$RUN_ID"
mkdir -p "$BACKUP_DIR"
exec > >(tee -a "$BACKUP_DIR/run.log") 2>&1

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

write_restore_notes() {
  cat > "$BACKUP_DIR/restore-notes.txt" <<EOF
WearEdge Jetson workspace backup
Run id: $RUN_ID
Repo: $REPO_ROOT
Backup dir: $BACKUP_DIR
Remote target: $REMOTE/$BRANCH

Main files:
- status.before.txt: working tree state before alignment
- tracked.patch: unstaged tracked-file changes
- staged.patch: staged changes, if any
- untracked-files.tgz: untracked files captured before alignment, if any
- untracked-files.txt: readable list of untracked files
- stash-list-after.txt / stash-ref.txt: Git stash created by --align mode, if any
- local-head.bundle: bundle of the local HEAD commit before alignment

Restore options:
1. Inspect the backup first:
   less "$BACKUP_DIR/status.before.txt"
   less "$BACKUP_DIR/untracked-files.txt"

2. Restore from stash, if --align created one:
   git stash list
   git stash show --stat \$(cat "$BACKUP_DIR/stash-ref.txt")
   git stash apply \$(cat "$BACKUP_DIR/stash-ref.txt")

3. Restore tracked patches manually, if needed:
   git apply "$BACKUP_DIR/tracked.patch"
   git apply --cached "$BACKUP_DIR/staged.patch"

4. Restore untracked files manually, if needed:
   tar -xzf "$BACKUP_DIR/untracked-files.tgz" -C "$REPO_ROOT"
EOF
}

log "RUN_ID=$RUN_ID"
log "MODE=$MODE"
log "REPO_ROOT=$REPO_ROOT"
log "BACKUP_DIR=$BACKUP_DIR"
log "TARGET=$REMOTE/$BRANCH"

write_restore_notes

log "CAPTURE_METADATA"
{
  echo "date=$(date -Is)"
  echo "user=$(whoami)"
  echo "host=$(hostname)"
  echo "repo_root=$REPO_ROOT"
  echo "mode=$MODE"
  echo "remote=$REMOTE"
  echo "branch=$BRANCH"
  echo "local_head=$(git rev-parse HEAD)"
  echo "local_head_short=$(git rev-parse --short HEAD)"
  echo "origin_head=$(git rev-parse --verify --quiet "$REMOTE/$BRANCH" || true)"
} > "$BACKUP_DIR/metadata.txt"

git remote -v > "$BACKUP_DIR/remotes.txt" || true
git branch -vv > "$BACKUP_DIR/branches.before.txt" || true
git status --porcelain=v1 -uall > "$BACKUP_DIR/status.before.txt"
git status -sb > "$BACKUP_DIR/status-branch.before.txt"
git log --oneline --decorate -20 > "$BACKUP_DIR/git-log.before.txt" || true
git diff --binary > "$BACKUP_DIR/tracked.patch" || true
git diff --cached --binary > "$BACKUP_DIR/staged.patch" || true
git ls-files --others --exclude-standard -z > "$BACKUP_DIR/untracked-files.zlist" || true
tr '\0' '\n' < "$BACKUP_DIR/untracked-files.zlist" > "$BACKUP_DIR/untracked-files.txt"
git bundle create "$BACKUP_DIR/local-head.bundle" HEAD >/dev/null 2>&1 || true

if [[ -s "$BACKUP_DIR/untracked-files.zlist" ]]; then
  log "ARCHIVE_UNTRACKED"
  tar --null -czf "$BACKUP_DIR/untracked-files.tgz" -T "$BACKUP_DIR/untracked-files.zlist"
else
  log "ARCHIVE_UNTRACKED skipped: no untracked files"
fi

log "FETCH_TARGET"
git fetch "$REMOTE" "$BRANCH"
git rev-parse "$REMOTE/$BRANCH" > "$BACKUP_DIR/remote-head.after-fetch.txt"

if [[ "$MODE" == "--backup-only" ]]; then
  log "BACKUP_ONLY_COMPLETE"
  log "Review backup at $BACKUP_DIR"
  log "Run with --align when ready to stash local changes and align to $REMOTE/$BRANCH."
  exit 0
fi

BACKUP_BRANCH="backup/$RUN_ID"
log "CREATE_BACKUP_BRANCH $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH" HEAD
echo "$BACKUP_BRANCH" > "$BACKUP_DIR/backup-branch.txt"

if [[ -s "$BACKUP_DIR/status.before.txt" ]]; then
  log "CREATE_SAFETY_STASH"
  git stash push -u -m "$RUN_ID before aligning to $REMOTE/$BRANCH"
  git stash list -n 10 > "$BACKUP_DIR/stash-list-after.txt"
  git stash list -n 1 | cut -d: -f1 > "$BACKUP_DIR/stash-ref.txt"
else
  log "CREATE_SAFETY_STASH skipped: working tree already clean"
  : > "$BACKUP_DIR/stash-list-after.txt"
  : > "$BACKUP_DIR/stash-ref.txt"
fi

log "ALIGN_TO $REMOTE/$BRANCH"
git reset --hard "$REMOTE/$BRANCH"

log "CLEAN_DRY_RUN"
git clean -fd -n > "$BACKUP_DIR/clean-dry-run.txt" || true
cat "$BACKUP_DIR/clean-dry-run.txt"

log "CLEAN_WORKTREE"
git clean -fd

git status --porcelain=v1 -uall > "$BACKUP_DIR/status.after.txt"
git status -sb > "$BACKUP_DIR/status-branch.after.txt"
git rev-parse HEAD > "$BACKUP_DIR/local-head.after.txt"

log "ALIGN_COMPLETE"
git status -sb
log "BACKUP_DIR=$BACKUP_DIR"
