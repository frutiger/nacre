# nacre

A set of git-shell-commands to create and enumerate repositories.

## Commands

### `help`

```sh
help
```

List the possible commands.

### `create`

```sh
create <name>
```

Create a new bare repository `<name>.git`, with `main` as its default branch.
`<name>` may not contain `/` or start with `.`.

### `list`

```sh
list
```

List the available repositories.

