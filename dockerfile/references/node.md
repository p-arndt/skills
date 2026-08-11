# Node

Final stage is `gcr.io/distroless/nodejs24-debian13:nonroot`. Its `ENTRYPOINT` is already
`["/nodejs/bin/node"]`, so `CMD` is *just the script path* — `CMD ["server.js"]`, not
`CMD ["node", "server.js"]`.

Node 24 is Active LTS (24.19.0 as of August 2026) and the right default. Node 26 is the Current
line and `nodejs26-debian13` exists, but Current is not what you deploy. Note the **debian13**
suffix — distroless publishes its language images on Debian 13 now, and there is no
`nodejs24-debian12`. Confirm before relying on any tag here:
`docker manifest inspect gcr.io/distroless/nodejs24-debian13:nonroot`.

```dockerfile
# syntax=docker/dockerfile:1

FROM node:24-trixie-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# npm ci obeys the lockfile exactly and fails if it drifted from package.json.
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Production dependencies as their own stage. `npm ci` wipes node_modules before installing,
# so re-running it with --omit=dev inside the build stage would discard what was just copied
# in; a separate stage keeps both installs cached and lets them run concurrently.
FROM node:24-trixie-slim AS prod-deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --omit=dev

FROM node:24-trixie-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM gcr.io/distroless/nodejs24-debian13:nonroot
WORKDIR /app
ENV NODE_ENV=production
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./
EXPOSE 3000
CMD ["dist/server.js"]
```

## Notes

- **No npm, no shell** in the final image. Anything in `scripts` (`npm start`, `prestart`
  migrations) will not run — call the entry file directly and run migrations as a separate job.
- **Native modules** compiled in the builder must match the runtime's glibc and Node ABI. Build on
  `node:24-trixie-slim` for `nodejs24-debian13` and they line up; mixing Alpine/musl builders
  with Debian runtimes does not.
- **pnpm/yarn**: same shape. `pnpm install --frozen-lockfile` with
  `--mount=type=cache,target=/pnpm/store`, then `pnpm deploy --prod /out` to get a flat,
  dev-free `node_modules` worth copying.
- **Next.js**: use `output: "standalone"` and copy `.next/standalone` + `.next/static` + `public`.
  Entry is `CMD ["server.js"]` from the standalone root.
- **Private registries**: `RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci`. Never
  `COPY .npmrc`.
- `ENV NODE_ENV=production` matters for framework behavior, not just for `npm install`.
