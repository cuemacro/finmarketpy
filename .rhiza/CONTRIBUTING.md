# Contributing

This document is a guide to contributing to the project.

We welcome all contributions. You don't need to be an expert
to help out.

## Checklist

Contributions are made through
[pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests).
Before sending a pull request, make sure you do the following:

- Run `make fmt` to make sure your code adheres to our [coding style](#code-style)
and all tests pass.
- [Write unit tests](#writing-unit-tests) for new functionality added.

## Building from source

You'll need to build the project locally to start editing code.
To install from source, clone the repository from GitHub,
navigate to its root, and run the following command:

```bash
make install
```

## Contributing code

To contribute to the project, send us pull requests.
For those new to contributing, check out GitHub's
[guide](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests).

Once you've made your pull request, a member of the
development team will assign themselves to review it.
You might have a few
back-and-forths with your reviewer before it is accepted,
which is completely normal.
Your pull request will trigger continuous integration tests
for many different
Python versions and different platforms. If these tests start failing,
please
fix your code and send another commit, which will re-trigger the tests.

If you'd like to add a new feature, please propose your
change in a GitHub issue to make sure
that your priorities align with ours.

If you'd like to contribute code but don't know where to start,
try one of the
following:

- Read the source and enhance the documentation,
  or address TODOs
- Browse the open issues,
  and look for the issues tagged "help wanted".

## Commit conventions

We use [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must have a
structured prefix so tooling can generate changelogs automatically.

### Format

```
<type>(<scope>): <short summary>
```

`scope` is optional but encouraged when the change is limited to a specific area.

### Types

| Type       | When to use                                      |
|------------|--------------------------------------------------|
| `feat`     | New feature or capability                        |
| `fix`      | Bug fix                                          |
| `docs`     | Documentation only                               |
| `refactor` | Code change that is neither a fix nor a feature  |
| `test`     | Adding or updating tests                         |
| `ci`       | CI / build system changes                        |
| `chore`    | Maintenance tasks (deps, tooling, config)        |
| `perf`     | Performance improvement                          |
| `security` | Security fix or hardening                        |

### Examples

```
feat(templates): add devcontainer template for Python 3.13
fix: resolve path issue in bootstrap script
docs: update CONTRIBUTING with commit conventions
ci: cache uv dependencies in GitHub Actions
```

### Breaking changes

Append `!` after the type/scope and add a `BREAKING CHANGE:` footer:

```
feat!: rename make target from `book` to `docs`

BREAKING CHANGE: `make book` no longer exists; use `make docs`.
```

## Code style

We use ruff to enforce our Python coding style.
Before sending us a pull request, navigate to the project
root and run

```bash
make fmt
```

to make sure that your changes abide by our style conventions.
Please fix any errors that are reported before sending
the pull request.

## Writing unit tests

Most code changes will require new unit tests.
Even bug fixes require unit tests,
since the presence of bugs usually indicates insufficient tests.
When adding tests, try to find a file in which your tests should belong;
if you're testing a new feature, you might want to create a new test file.

We use the popular Python [pytest](https://docs.pytest.org/en/) framework for our
tests.

## Running unit tests

We use `pytest` to run our unit tests.
To run all unit tests run the following command:

```bash
make test
```

Please make sure that your change doesn't cause any
of the unit tests to fail.
