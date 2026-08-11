# Rust

Two viable shapes. Pick by whether the crate graph pulls in C.

**musl → `scratch`.** Fully static, nothing to link. The CA bundle is one `COPY` (below); swap
the final stage for `gcr.io/distroless/static-debian13:nonroot` only if the app needs a writable
`/tmp` or `/etc/passwd`, which `scratch` does not have. Fails if a dependency needs a C library
that has no musl build; `ring`/`openssl-sys` are the usual culprits (use `rustls` and
`reqwest`'s `rustls-tls` feature to avoid the whole problem).

**glibc → `gcr.io/distroless/cc-debian13:nonroot`.** Dynamically linked against libc/libgcc, no
shell, ~20 MB. The pragmatic default when the crate graph has C in it.

```dockerfile
# syntax=docker/dockerfile:1

FROM rust:1.97-trixie AS chef
RUN rustup target add x86_64-unknown-linux-musl && \
    apt-get update && apt-get install -y --no-install-recommends musl-tools && \
    rm -rf /var/lib/apt/lists/*
RUN cargo install cargo-chef --locked
WORKDIR /src

# The planner is its own stage on purpose. recipe.json depends only on the manifests, so
# the cook layer below is keyed on *that* file's content — copying sources into the same
# stage would invalidate cook on every source edit and defeat the entire point of chef.
FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS build
COPY --from=planner /src/recipe.json recipe.json
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo chef cook --release --target x86_64-unknown-linux-musl --recipe-path recipe.json
COPY . .
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo build --release --target x86_64-unknown-linux-musl --locked

FROM scratch
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=build /src/target/x86_64-unknown-linux-musl/release/app /app
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/app"]
```

## Notes

- Without `cargo-chef`, the poor-man's version is `COPY Cargo.toml Cargo.lock ./` + a dummy
  `src/main.rs` + `cargo build --release` before copying real sources. It works and it is
  fragile — workspaces break it. Prefer chef for anything with more than one crate.
- Do **not** put `target/` on a cache mount while also copying the binary out of it in a later
  stage: a cache mount is not part of the layer, so the `COPY --from` finds nothing. Cache the
  cargo *registry*, build into a real `target/`.
- Size: `strip = true` and `panic = "abort"` in `[profile.release]`, plus `opt-level = "z"` if
  binary size beats throughput for you.
- `--locked` fails the build when `Cargo.lock` is stale instead of silently resolving something new.
