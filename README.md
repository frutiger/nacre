# nacre

A set of git-shell-commands to create and enumerate repositories, and to run
sandboxed, network-policed agent sessions against them.

## Commands

Everything is menu-driven — pick from a numbered list; a blank line (or Ctrl-C)
steps back out.

- **`update`** — update these commands themselves: fetch their repo's remote,
  then pick a revision reachable from the remote HEAD to switch to (`>` marks
  the current one), 10 per page. Checkouts are detached, so this rolls
  forward or back freely
- **`help`** — list the commands
- **`create <name>`** — create a bare repo `<name>.git`, asking for the
  default branch name (`main` if left blank)
- **`list`** — list the repositories
- **`work` / `work <repo>`** — browse repositories (each tagged
  `running/total`) and their projects, or jump straight into one repository
- **`hosts`** — edit or show the user-wide host policy layered under every
  project's own (see Host policy)
- **`login`** — renew an agent type's credentials by re-running its login
  flow outside any sandbox. Running sessions pick the new credentials up;
  exited ones need **resume**

### Project actions (under `work`)

From a repository you pick **new project** or an existing one; from a project
you pick an action. Only actions valid in the project's current state are
shown:

- **new project** — clone `<repo>` at a detached HEAD (nacre never creates a
  project branch), seed the agent type's host policy, start the session, and
  watch. The type (`claude`, the only one today) is fixed for the project's
  life.
- **watch** *(running)* — decide each host queued in `.pending/`: **a**llow,
  **d**eny, **w**ildcard (allow `*.parent`), or **s**kip; a `u` prefix (`ua`,
  `ud`, `uw`) writes the decision to the user-wide file instead. Ctrl-C
  returns to the menu; the session keeps running. If the session dies instead
  (a crash, or expired credentials), watch reports it with the last log
  lines — pointing at `login` when it looks like an auth failure — and
  returns to the menu.
- **resume** *(stopped)* — restart the session, then watch.
- **stop** *(running)* — stop the session and its proxy.
- **erase** *(stopped)* — delete the checkout and its metadata. Confirms first
  if that would lose uncommitted changes or commits held nowhere else.
- **sync** — land the project's committed work into its repository, then stop
  the session (if running) and erase the project. See below.
- **edit hosts** — edit `.hosts` in `$EDITOR`; the draft is validated before it
  replaces the policy, so an invalid file never lands.
- **show hosts** / **show log** — print the project's policy followed by the
  user-wide one (plus any undecided `? host` lines), or the session + proxy
  log.

## Sync

An agent can't push from inside the sandbox, so integration happens from the
outside: the canonical repo fetches the checkout's `HEAD` and fast-forwards its
own `HEAD` (whatever the default branch is — never named or assumed). It
refuses anything but a strict fast-forward, and refuses a dirty tree — a
refusal returns to the menu with the session untouched. On success it stops
the session and erases the project.

## Layout

Everything lives under the git user's home directory. A repository is a bare
git directory; its projects are checkouts nested inside it:

```
~/<repo>.git/                        canonical bare repository
~/<repo>.git/nacre/<proj>/worktree   project checkout (detached HEAD)
~/<repo>.git/nacre/<proj>/hosts      host policy
~/<repo>.git/nacre/<proj>/pending/   hosts awaiting an allow/deny decision
~/<repo>.git/nacre/<proj>/log        session + proxy log
~/.nacre/hosts                       user-wide host policy (optional)
```

Only `worktree` is writable inside the sandbox. Project names are unique only
within a repository, so the menus are always scoped to one repository.
Checkouts are cloned `--no-hardlinks`, so a session never shares inodes with
the canonical object store.

## Sandbox

**new project** starts the agent headless in the background (for claude:
`claude remote-control`, driven from claude.ai or the Claude app). Sessions are
detached — they survive ssh disconnects, **watch** can re-enter any time, and
**stop** ends one deliberately.

Each session runs inside bubblewrap:

- the filesystem is read-only except the project checkout and the agent's own
  state (`~/.claude`, `~/.claude.json`); integrating a project's work therefore
  means fetching from the checkout, not pushing from within it (what `sync`
  does).
- there is no network namespace; the only route out is a loopback bridge to a
  per-session proxy running outside the sandbox.

## Host policy

The proxy allows CONNECT tunnels to port 443 and forwards absolute-form HTTP(S)
requests (ports 80/443), decided per hostname by the project's `.hosts` file.
CONNECT passes through end-to-end encrypted; absolute-form https gets a
certificate-validated TLS connection originated by the proxy. DNS resolves in
the proxy, so the sandbox needs none.

`.hosts` format: `+ host` allows, `- host` denies, one per line; `#` comments
and blank lines are fine. `*.example.com` matches subdomains (not the apex).
Deny wins, and deny lines must come first so the file reads in precedence
order. Malformed files are refused, never silently fixed.

Besides each project's `.hosts` there is an optional user-wide policy at
`~/.nacre/hosts` (same format, edited or shown with the `hosts` command) that
applies to every project. The project file takes precedence: the
user file is consulted only for hosts the project's policy does not mention at
all, so a project `+ host` overrides a user-wide `- host` and vice versa.
Hosts decided in neither file are parked as usual; decisions made in
**watch** land in the project's file, or in the user-wide one when prefixed
with `u`.

A request to an undecided host is **parked**: the proxy holds it open and
queues the host in `.pending/`. Deciding (via **watch** or **edit hosts**)
releases it; if the client gives up first, the pending entry survives so a late
decision still covers the retry. Edits apply to running sessions on their next
connection. `.hosts` is the source of truth; `.pending/` is only a hint queue.

## Server prerequisites (Arch)

```sh
pacman -S git openssh python nodejs npm bubblewrap socat iproute2
npm install -g @anthropic-ai/claude-code
```

Install these scripts in the git user's `~/git-shell-commands/`, executable,
with `git-shell` as the login shell. The git user needs Claude Code
credentials: `ANTHROPIC_API_KEY`, or stored ones from the `login` command.
Stored credentials expire eventually: **watch** reports the dead session when
they do, and `login` renews them.
