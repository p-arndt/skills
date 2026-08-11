# Python

Python is the awkward one, because the interpreter *is* the runtime and distroless pins its own
minor version.

**The caveat that decides everything:** `gcr.io/distroless/python3-debian13` ships whatever CPython
Debian 13 (trixie) ships — **3.13** — and contains **no pip and no uv**. Dependencies must be
resolved in a builder on the *same minor version*, or C extensions built against 3.14 fail to
import on 3.13. Build on `python:3.13-slim-trixie`, matching the runtime — not on whatever
`python:3-slim` resolves to today.

If you need a version distroless does not have, use `python:3.14-slim-trixie` with an explicit
non-root user instead. That is a legitimate, common choice — a slim base with a real UID beats a
distroless image running the wrong interpreter.

## uv

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.13-slim-trixie AS build
# Pin uv. `:latest` here changes the resolver underneath you between builds.
COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/venv

WORKDIR /app

# Dependencies only, before the source exists. The manifests arrive as bind mounts rather than
# COPY: uv needs them to resolve, but they never become a layer of their own.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Now the project itself — this is the only layer a source edit invalidates.
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM gcr.io/distroless/python3-debian13:nonroot
WORKDIR /app
# PYTHONPATH, not PATH: the ENTRYPOINT is this image's own /usr/bin/python3.13, so /venv/bin is
# never consulted (and /venv/bin/python is a dangling symlink into the builder). PYTHONPATH is
# what makes the packages importable — and it is why the minor versions must match, since the
# path literally contains "python3.13".
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/venv/lib/python3.13/site-packages
# --no-editable installed the project *into* the venv, so this one COPY is the whole app.
COPY --from=build /venv /venv
EXPOSE 8000
# distroless/python3's ENTRYPOINT is the interpreter; CMD is the args.
CMD ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Why each uv flag

- **`--locked`** fails the build if `uv.lock` is stale against `pyproject.toml`, instead of
  quietly resolving something new. This is the reproducibility guarantee; do not drop it.
  (`--frozen` skips the check entirely — for workspaces, where members are not all present yet.)
- **`--no-install-project`** on the first sync is the whole caching trick: dependencies resolve
  without the source tree, so editing a `.py` file does not reinstall numpy.
- **`--no-editable`** installs the project as a real package instead of a `.pth` link back to
  `/app`, which is what lets the final stage copy `/venv` and nothing else.
- **`UV_PROJECT_ENVIRONMENT=/venv`** puts the venv at a fixed path instead of `/app/.venv` —
  cosmetic, but it keeps the `PYTHONPATH` above readable.
- **`UV_COMPILE_BYTECODE=1`** ships `.pyc` precompiled, so the first request doesn't pay for
  compilation. Pairs with `PYTHONDONTWRITEBYTECODE=1` at runtime, where a read-only root
  filesystem could not write them anyway.
- **`UV_LINK_MODE=copy`** — uv hardlinks from its cache by default, which cannot cross the cache
  mount boundary; without this you get a warning and a slow fallback on every build.
- **`UV_PYTHON_DOWNLOADS=0`** stops uv from fetching its own managed CPython. You want the base
  image's interpreter, because that is the one the runtime image has.

## Notes

- On a `python:3.13-slim-trixie` final stage the venv works through `PATH="/venv/bin:$PATH"`
  as normal, because there the interpreter symlink resolves. The `PYTHONPATH` dance is a
  distroless-specific tax — one more reason slim + explicit `USER` is a reasonable call.
- **Legacy pip repos**: same stage shape. `python -m venv /venv`, `ENV PATH="/venv/bin:$PATH"`,
  then `pip install --require-hashes -r requirements.txt` with
  `--mount=type=cache,target=/root/.cache/pip`. Without `--require-hashes` or a lockfile the
  image differs from yesterday's for reasons nobody wrote down.
- Compiled dependencies still need `build-essential` in the builder — add it in one
  `apt-get update && apt-get install -y --no-install-recommends … && rm -rf /var/lib/apt/lists/*`
  layer. None of it reaches the final stage, which is the point of the split.
- `PYTHONUNBUFFERED=1` or your logs vanish when the container is killed.
- Gunicorn/uvicorn workers: one process per container is still the goal — scale replicas in the
  orchestrator rather than forking a worker pool inside one container, unless you measured otherwise.
