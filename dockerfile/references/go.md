# Go

Static by default: `CGO_ENABLED=0` makes the binary depend on nothing, so the final stage can be
`scratch`. If cgo is genuinely required (sqlite3, some crypto/DNS setups) you cannot use `scratch` —
build against glibc and land on `gcr.io/distroless/base-debian13:nonroot`.

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:1.26-trixie AS build
WORKDIR /src

# Manifests first: this layer survives every source edit.
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY . .
# -trimpath strips local paths from panics; -s -w drops the symbol table and DWARF (~30%).
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/app ./cmd/app

FROM scratch
# scratch has no CA bundle — any outbound HTTPS call fails with x509 errors without this.
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
# Only if the app formats times in a named zone:
# COPY --from=build /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=build /out/app /app
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/app"]
```

## Notes

- **Certs and tzdata do not justify leaving `scratch`.** The `COPY` above is ~200 KB, and
  `import _ "time/tzdata"` in `main.go` embeds the zone database into the binary, which removes
  the second `COPY` entirely and is the better answer for Go.
- **What does justify it:** the app needs a writable `/tmp`, or resolves the current user by name.
  `scratch` has neither a temp dir nor `/etc/passwd`, and neither is worth faking by hand — switch
  the final stage to `gcr.io/distroless/static-debian13:nonroot`, drop both `COPY` lines and the
  `USER` line (the tag is already UID 65532), and keep everything else identical.
- Version stamping: `-ldflags="-s -w -X main.version=$VERSION"` with `ARG VERSION` — an `ARG` is
  fine for a version string, never for a token.
- `go build ./cmd/app`, not `./...`, unless you actually want every binary.
- Static assets (templates, migrations, embedded configs) must be `COPY`'d into the final stage,
  or use `//go:embed` at build time and stop thinking about it. `embed` is the better answer.
- `GOFLAGS=-mod=readonly` in CI catches a `go.sum` that drifted from `go.mod`.
