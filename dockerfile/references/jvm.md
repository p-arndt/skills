# JVM

Two options, in increasing order of effort and decreasing order of size.

**Simple:** build with `eclipse-temurin:25-jdk`, run on
`gcr.io/distroless/java25-debian13:nonroot` (a full JRE, ~200 MB). Java 25 is
the current LTS; `java17-debian13` and `java21-debian13` are still published if you are pinned back.

**Small:** `jlink` a custom runtime containing only the modules your app uses, and land on
`gcr.io/distroless/java-base-debian13:nonroot` (~90 MB total). Worth it for anything you deploy
often.

```dockerfile
# syntax=docker/dockerfile:1

FROM eclipse-temurin:25-jdk AS build
WORKDIR /src
# Wrapper + manifests first — dependency resolution is the slow part.
COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw -B dependency:go-offline
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw -B -DskipTests package

FROM gcr.io/distroless/java25-debian13:nonroot
WORKDIR /app
# Maven names the jar <artifactId>-<version>.jar unless <finalName> says otherwise —
# check yours rather than copying this literally.
COPY --from=build /src/target/app.jar ./app.jar
EXPOSE 8080
# distroless/javaNN's ENTRYPOINT is ["java", "-jar"], so CMD is just the jar path.
CMD ["app.jar"]
```

## Notes

- **Layered jars beat fat jars for cache.** Spring Boot: `java -Djarmode=tools -jar app.jar extract
  --layers --destination /out` in the builder, then `COPY --from=build` each layer directory
  separately (dependencies, spring-boot-loader, snapshot-dependencies, application). Dependencies
  change rarely, application code changes constantly — one `COPY` per layer means a code edit
  reships only the last one. **The catch:** an exploded layout is launched with
  `ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]`, which collides with
  `distroless/javaNN`'s fixed `java -jar`. Either override the `ENTRYPOINT` or use
  `gcr.io/distroless/java-base-debian13:nonroot`, which does not set one. Pick layering or the
  stock entrypoint — you cannot have both silently.
- **Memory:** modern JVMs read cgroup limits automatically. Set
  `JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75"` rather than a fixed `-Xmx` so the container limit
  stays the single source of truth.
- **Gradle:** `--mount=type=cache,target=/root/.gradle` and `gradle --no-daemon build`.
- The distroless Java images already run as `nonroot` with the `:nonroot` tag; do not add `USER root`
  to fix a permissions problem — fix the file ownership with `COPY --chown=nonroot:nonroot`.
