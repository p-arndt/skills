---
name: dockerfile
description: 'Write or fix a production Dockerfile: pick the smallest correct base (scratch for static Go/Rust, distroless nonroot for Node/Python/JVM), split build from runtime, order layers so the dependency cache actually holds, and run as a non-root user. Use when adding a Dockerfile to a repo, shrinking or hardening an existing one, or debugging slow rebuilds and fat images.'
argument-hint: '[path] [--fix]'
---

# dockerfile

An image is a deployment artifact, not a dev box. Everything the build needed — compilers,
package managers, headers, test fixtures, `.git` — is a liability once the binary exists. The
job is to end at a final stage that contains the artifact, its runtime, and nothing else, and
to get there without re-downloading the world on every rebuild.

Three decisions carry almost all the weight: **which base**, **where the stage boundary falls**,
and **what order the layers go in**. Get those right and the rest is hygiene.

## Usage

```
/dockerfile            write one for the repo in the current directory
/dockerfile <path>     that repo or that Dockerfile
/dockerfile --fix      audit an existing Dockerfile and rewrite it
```

## Pick the base

| Runtime | Final stage | Why |
|---|---|---|
| Go, Rust (static) | `scratch` | Nothing to link against. Image is the binary. Certs and tzdata are one `COPY` — see below. |
| …that needs a writable `/tmp` or `/etc/passwd` | `gcr.io/distroless/static-debian13:nonroot` | ~2 MB. Ships the things you *cannot* cheaply fake on `scratch`. |
| Go with cgo | `gcr.io/distroless/base-debian13:nonroot` | glibc + OpenSSL. Enough for cgo Go; no libstdc++. |
| Rust/C/C++ linked against glibc | `gcr.io/distroless/cc-debian13:nonroot` | `base` + libgcc/libstdc++. Still no shell. |
| Node | `gcr.io/distroless/nodejs24-debian13:nonroot` | Node 24 Active LTS. Node runtime, no npm, no shell. |
| Python | `gcr.io/distroless/python3-debian13:nonroot` | CPython 3.13. See the version caveat in `references/python.md`. |
| JVM | `gcr.io/distroless/java25-debian13:nonroot` | Java 25 LTS. Or `java-base` + a `jlink` runtime. |
| Genuinely needs a shell/apt at runtime | `debian:trixie-slim` + explicit `USER` | Alpine only if you have measured musl is fine — it is not, for glibc-linked or CPython-heavy workloads. |

**Distroless is on Debian 13 (trixie) now.** The language images (`nodejs*`, `python3`, `java*`)
are published as `-debian13` only; `-debian12` still exists for `static`/`base`/`cc` but is the
older line. Do not carry a `nodejs22-debian12`-shaped tag forward from an old Dockerfile — check
it (`docker manifest inspect`) rather than assuming it still resolves.

Language recipes, copy-ready and commented, live in `references/`: `go.md`, `rust.md`,
`node.md`, `python.md`, `jvm.md`. Read the one that matches before writing. Their tags were
current in **August 2026** (Go 1.26, Rust 1.97, Node 24 LTS, CPython 3.13, Java 25 LTS, uv 0.12) —
treat them as the major line to aim at, and resolve to the exact version the repo pins, per the
rule under Non-negotiables. If today is much later than that, verify before trusting any of them. `references/hardening.md`
covers the rules that apply to every image regardless of language.

`scratch` vs `distroless/static` is not a certs question. A CA bundle is one `COPY` line and
~200 KB, and Go can embed tzdata with `import _ "time/tzdata"` — neither is a reason to leave
`scratch`. What `scratch` genuinely lacks is a **writable `/tmp`** (anything calling
`os.CreateTemp`, or a library that spools to disk, gets ENOENT) and **`/etc/passwd`** (only
matters if code resolves the current user by name — a numeric `USER` works either way). Those are
the two questions to answer; if both are "no", stay on `scratch` and copy the certs. (A `/tmp`
you control at deploy time can also come from a tmpfs mount — see `references/hardening.md`.)

**Distroless has no shell.** `docker exec … sh` fails, `RUN` fails, and shell-form `CMD ls | grep`
fails. That is the security property, not a bug. Use the `:debug-nonroot` tag variant when you need to
get inside, and never ship it. Every `CMD`/`ENTRYPOINT` must be exec form (`["/app", "--flag"]`) — and note that the
language distroless images already set an `ENTRYPOINT`, so your `CMD` supplies only the
arguments to it. Each recipe says what that base expects.

## Procedure

1. **Read the repo first.** Language, build tool, lockfile, entrypoint, what the app opens at
   runtime (config files, templates, static assets, migrations, CA trust, timezone data).
   Assets the binary reads at runtime must be `COPY`'d into the final stage — this is the
   single most common way a `scratch` image dies on first boot.
2. **Check the versions.** Match the toolchain in `go.mod` / `rust-toolchain.toml` /
   `.nvmrc` / `pyproject.toml` / `requires-python`. Do not paste a version from a recipe or from
   memory — confirm the tag exists (`docker manifest inspect <image>`), because distroless
   publishes only a few language versions, moves them between Debian releases, and drops old ones.
   Prefer the runtime's **LTS/stable** line (Node 24 over Node 26, Java 25 over the newest EA) —
   "latest" and "what you should deploy" are not the same tag.
3. **Write the build stage** on the full toolchain image, and the final stage on the base from
   the table. Named stages (`AS build`), never numeric.
4. **Order for cache** — the rule below.
5. **Write `.dockerignore`** in the same commit. Without it the build context ships `.git`,
   `node_modules`, and every local secret to the daemon, and busts the cache on every file
   touched.
6. **Drop to non-root**, exec-form entrypoint, `EXPOSE` documented, no secrets in layers.
7. **Build it and run it.** `docker build` succeeding proves nothing. Start the container,
   hit the port, check the process UID: `docker run --rm <img> id` won't work on distroless —
   inspect the config instead, or exercise the real endpoint.

## The cache rule

Layers invalidate top-down: change one line and every layer below it rebuilds. So the file is
ordered by *how often things change*, slowest first.

```dockerfile
COPY go.mod go.sum ./      # changes when a dependency changes
RUN go mod download        # the expensive step, cached across every source edit
COPY . .                   # changes on every single edit
RUN go build …
```

Copying manifests separately from source is the whole trick, and it is the same shape in every
language: `go.mod`/`go.sum`, `Cargo.toml`/`Cargo.lock`, `package.json`/`package-lock.json`,
`pyproject.toml`/`uv.lock`, `pom.xml`. `COPY . .` before installing dependencies throws the
cache away on every keystroke.

Two more, both BuildKit (assume it; it is the default since Docker 23):

- **Cache mounts** keep the package manager's own store warm *across* invalidations:
  `RUN --mount=type=cache,target=/root/.cache/go-build …`. Even when the layer rebuilds, the
  compiler doesn't start from zero. Cache mounts are build-host state — never write anything
  the image needs into one; it is not in the layer.
- **Secret mounts** for private registries and tokens:
  `RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci`. A secret in an `ARG`, an `ENV`,
  or a `COPY`'d file is in the image history forever, whether or not a later layer deletes it.

## Non-negotiables

- **Multi-stage, always.** If the final stage has a compiler or a package manager in it, it is wrong.
- **Non-root.** `:nonroot` tag, or explicit `USER 65532:65532`. A numeric UID works on `scratch`,
  which has no `/etc/passwd` to resolve a name against. Kubernetes `runAsNonRoot` rejects images
  whose `USER` is a name it cannot resolve — prefer the numeric form.
- **Pin the base.** `node:24.19-trixie-slim`, not `node:latest`. Pin by digest
  (`@sha256:…`) for anything that must rebuild reproducibly. "Latest version" means the latest
  version *you verified today*, written down — not a floating tag.
- **One process, no init hacks.** No `supervisord`, no `sleep`-and-poll wrapper scripts. If PID 1
  needs to reap children, `docker run --init` or `tini` — decided deliberately, not by default.
- **No `HEALTHCHECK` on distroless.** It shells out; there is no shell. Health-check from the
  orchestrator (`livenessProbe` hitting a real endpoint), which is where it belongs anyway.
- **`WORKDIR`, never `RUN cd`.** `cd` doesn't persist across layers.
- **Combine `apt-get update` with `install`** in one `RUN`, `--no-install-recommends`, and
  `rm -rf /var/lib/apt/lists/*` in the same layer. Split across layers you get a stale index
  and the deleted files still weigh in the layer below.

## Report

Say what the final image contains, what base and why, and the measured size (`docker images`).
If you could not verify a tag or could not run the container, say that plainly rather than
implying it works.
