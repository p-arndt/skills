# Hardening and hygiene

Language-independent. Apply all of it.

## .dockerignore

Write it in the same commit as the Dockerfile. Without it, the whole working tree — `.git`,
`node_modules`, `target/`, local `.env` files — is uploaded to the daemon as build context, which
is both slow and a secret-leak path, and any file touched anywhere busts the cache.

```
.git
.gitignore
.dockerignore
Dockerfile*
**/node_modules
**/__pycache__
target/
dist/
build/
.venv/
*.log
.env*
.DS_Store
**/.terraform
coverage/
```

Allowlist style (`*` then `!src`) is stricter and worth it for repos with a lot of loose files.

## Secrets

A secret that ever exists in a layer is in the image forever — `docker history` shows it, and a
later `RUN rm` does not remove it from the layer below.

- Build-time credentials: `RUN --mount=type=secret,id=<id>,target=<path> …`, passed with
  `docker build --secret id=<id>,src=<file>`.
- Private git deps: `RUN --mount=type=ssh …` with `--ssh default`.
- `ARG` is visible in `docker history`. Fine for a version string, never for a token.
- Runtime config comes from the environment or a mounted file at run time, never baked in.

## User and filesystem

```dockerfile
USER 65532:65532          # numeric — scratch has no /etc/passwd, and k8s runAsNonRoot needs a UID
```

- Distroless `:nonroot` tags are already UID 65532; keep the `USER` line anyway so the intent
  survives a base change.
- Anything the app writes to (cache, uploads, sockets) must be a volume or `--chown`'d at COPY
  time. Design for a **read-only root filesystem** (`readOnlyRootFilesystem: true`) — if the app
  needs `/tmp`, mount an `emptyDir` (or `--tmpfs /tmp` locally), don't make the root writable.
  That mount is also the escape hatch for a `scratch` image that turns out to need a temp dir —
  a tmpfs supplies one without a base change, if you control the deployment manifest.
- Drop capabilities at run time (`--cap-drop=ALL`, `--security-opt=no-new-privileges`); the
  Dockerfile cannot do this for you, so say it in the README or the manifest.

## Metadata

```dockerfile
ARG GIT_SHA=dev            # docker build --build-arg GIT_SHA=$(git rev-parse HEAD)
LABEL org.opencontainers.image.source="https://github.com/org/repo" \
      org.opencontainers.image.revision="${GIT_SHA}" \
      org.opencontainers.image.licenses="MIT"
```

`image.source` is what wires a registry package back to its repo; `revision` is what turns a
running container back into a commit during an incident.

`EXPOSE` documents the port — it does not publish it. Keep it accurate anyway; tooling reads it.

## Verify before claiming it works

1. `docker build -t app:test .` — note the size from `docker images`.
2. `docker run --rm -p 8080:8080 app:test` and hit a real endpoint. A container that starts and
   immediately exits with code 0 is a failed image, not a passing one.
3. `docker history app:test` — scan for secrets and for a fat layer that shouldn't be there.
4. `docker scout cves app:test` or `trivy image app:test` if available.
5. Multi-arch: `docker buildx build --platform linux/amd64,linux/arm64`. Cross-compiling Go and
   Rust is cheap; emulated native builds (`qemu`) are very slow — use `--platform=$BUILDPLATFORM`
   on the build stage plus `$TARGETARCH` in the compiler flags.
