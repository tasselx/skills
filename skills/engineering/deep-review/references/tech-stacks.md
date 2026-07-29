# Technology Specific Review

When the change touches a technology listed below, apply the additional checks for that stack. If none matches, the generic categories in Phase 3 already provide full coverage.

## Flutter / Dart

**Widget** — unnecessary rebuilds, expensive build methods, incorrect widget lifecycle.

**Async** — Future lifecycle, Stream lifecycle, missing dispose, controller leaks, BuildContext misuse after async gap.

**Performance** — excessive setState, unnecessary allocations, isolate usage, image/resource handling.

**Platform** — Android compatibility, iOS compatibility, permissions, native integration risks.

## Frontend (React / Vue / Angular / Svelte)

**Rendering** — unnecessary re-renders, missing memoization, stale closures, incorrect dependency arrays in hooks.

**State** — global state mutation outside intended flow, race conditions in async state updates, stale state after navigation.

**Security** — XSS via dangerouslySetInnerHTML / v-html / bypassSecurityTrust, unsafe user input in templates.

**Performance** — bundle size impact, missing code splitting, unoptimized images/assets, excessive DOM nodes.

**Accessibility** — missing ARIA attributes, keyboard navigation gaps, color contrast issues.

## iOS (Swift / Objective-C)

**Memory** — retain cycles (strong self in closures), missing weak/unowned references, autorelease pool issues.

**Concurrency** — data races in Swift Concurrency, actor isolation violations, MainActor usage correctness.

**Lifecycle** — UIViewController lifecycle misuse, missing deinit cleanup, observation leaks (Combine/Notification observers).

**UI** — Auto Layout ambiguity, missing safe area handling, incorrect trait collection adaptation.

**Platform** — iOS version compatibility, deprecated API usage, App Store review risks (private API, entitlements).

## Android (Kotlin / Java)

**Memory** — activity/fragment leaks, static context references, unclosed Cursor/InputStream.

**Lifecycle** — lifecycle-aware component misuse, observing LiveData after view destroyed, missing onStop/onPause cleanup.

**Concurrency** — Coroutine cancellation handling, Dispatchers correctness, shared mutable state.

**Security** — exported components without permission checks, intent injection, insecure local storage (SharedPreferences for secrets).

**Compatibility** — minSdkVersion requirements, platform version checks, manufacturer-specific behavior.

## Backend (Server / API / Microservice)

**API** — API compatibility, validation, authentication, authorization, rate limiting.

**Database** — transaction problems, consistency issues, migration risks, locking problems, N+1 queries.

**Distributed System** — concurrency, retries, idempotency, caching consistency, circuit breaker gaps.

**Resource** — connection pool exhaustion, thread pool starvation, file descriptor leaks, backpressure handling.

## DevOps / Infrastructure (Terraform / K8s / CI-CD)

**IaC** — state file safety, resource deletion risks, missing depends_on, drift between code and cloud.

**K8s** — resource limits/requests, liveness/readiness probe correctness, ConfigMap/Secret mounting, RBAC over-permission.

**CI/CD** — secret leakage in logs, missing caching, flaky pipeline steps, deployment ordering.

**Security** — IAM over-permission, public exposure of internal resources, missing network policies.

## Python

**Typing** — type annotation correctness, mypy/pyright issues, runtime vs declared type mismatch.

**Async** — missing await, blocking calls in async functions, event loop blocking.

**Resource** — missing context managers (with statements), unclosed files/connections, generator cleanup.

**Packaging** — dependency pinning, import path changes, __init__.py side effects.

## Go

**Concurrency** — goroutine leaks, missing context cancellation, race conditions, channel misuse (deadlock, close on send).

**Error Handling** — unwrapped errors, missing errors.Is/As checks, swallowed errors, sentinel error comparison.

**Resource** — unclosed defer (file/conn/body), missing defer in loops, goroutine not cleaned up on error path.

**Interface** — interface pollution, empty interface abuse, interface compatibility on signature changes.

**Memory** — slice pre-allocation, unnecessary copies, map pre-sizing, escape analysis issues.

## Rust

**Ownership** — borrow checker conflicts, unnecessary clones, lifetime annotation correctness, dangling references.

**Unsafe** — unsafe block justification, FFI boundary safety, memory layout assumptions, uninitialized memory.

**Concurrency** — Send/Sync trait correctness, lock ordering deadlocks, lock-free data structure soundness.

**Error Handling** — Result propagation, panic vs Result, unwrap/expect in production code, error context chaining.

**Performance** — unnecessary allocations, Box vs stack, iterator chain efficiency, zero-copy opportunities.

## Java / Kotlin (JVM)

**Null Safety** — NullPointerException risks, Optional misuse, Kotlin nullable type correctness.

**Concurrency** — thread safety of shared state, synchronized vs Lock vs CAS, ThreadPool sizing, CompletableFuture error handling.

**Memory** — memory leaks (static collections, unclosed resources, listener registration), excessive object creation, GC pressure.

**Spring** — bean scope correctness, transaction boundary issues, circular dependencies, missing @Transactional on multi-write operations.

**JVM** — classloader issues, reflection risks, serialization security (deserialization gadgets), JVM version compatibility.

## C / C++

**Memory** — buffer overflow, use-after-free, double free, uninitialized memory read, memory leak, dangling pointers.

**Concurrency** — data races, missing synchronization, TOCTOU, lock ordering deadlocks, atomics memory ordering.

**Type Safety** — implicit conversions, integer overflow/underflow, sign extension, pointer arithmetic correctness.

**Resource** — file descriptor leak, socket leak, missing RAII, exception safety (resource leak on throw).

**Undefined Behavior** — strict aliasing violation, sequence point violations, shift count overflow, null pointer dereference.

## .NET / C#

**Async** — async void misuse, missing await, .Result/.Wait() deadlocks, CancellationToken not propagated.

**Memory** — IDisposable not disposed, missing using statements, large object heap fragmentation, GC pressure.

**LINQ** — multiple enumeration of IEnumerable, deferred execution side effects, N+1 in EF Core queries.

**Security** — SQL injection via Entity Framework raw queries, insecure deserialization, CAS issues.

**Compatibility** — .NET version compatibility, NuGet package breaking changes, API surface changes.

## Node.js / TypeScript

**Async** — unhandled promise rejections, missing await, callback hell patterns, event loop blocking.

**Typing** — TypeScript type assertion abuse (as any), missing type guards, runtime vs compile-time type mismatch.

**Security** — prototype pollution, command injection via child_process, path traversal, ReDoS in regex.

**Performance** — blocking the event loop, memory leaks in long-lived listeners, stream backpressure, unbounded buffers.

**Module** — circular dependencies, CommonJS/ESM interop issues, dynamic import risks, tree-shaking breakage.

## Ruby / Rails

**Type** — duck typing assumptions, NoMethodError risks, nil checks missing, frozen string issues.

**Concurrency** — GIL limitations, thread safety of shared state, Fiber/Async correctness.

**Security** — SQL injection via string interpolation in ActiveRecord, mass assignment, missing strong params, CSRF protection bypass, insecure deserialization (YAML).

**Resource** — unclosed file/connection blocks, missing ensure cleanup, memory bloat in long-running processes.

**Rails Query** — N+1 queries, missing indexes, inefficient ActiveRecord callbacks, raw SQL injection.

**Rails Convention** — callback abuse, concerns overuse, STI misuse, route exposure, deprecation warnings.

## PHP

**Security** — SQL injection, XSS (unescaped output), file inclusion (LFI/RFI), session fixation, CSRF token gaps.

**Type** — type coercion bugs, null handling, strict_types declaration missing, union type compatibility.

**Resource** — memory limit exhaustion, unclosed connections, missing cleanup in error paths.

**Framework** — Laravel Eloquent mass assignment, Symfony autowiring issues, composer dependency conflicts.

## Database / SQL

**Migration** — backward incompatible schema changes, missing rollback, lock duration during DDL, data loss risks.

**Query** — N+1 patterns, missing indexes, SELECT * abuse, missing pagination, Cartesian products.

**Transaction** — long-running transactions, missing isolation level, deadlock potential, partial commit.

**Security** — SQL injection, missing parameterization, over-privileged DB user, sensitive data in plain text columns.

## GraphQL

**Schema** — breaking field/type removal, deprecation path missing, nullability changes, enum value changes.

**Security** — introspection enabled in production, missing query depth/complexity limits, batching abuse for DoS.

**Performance** — N+1 resolvers, missing DataLoader batching, over-fetching, missing persisted queries.

**Error** — sensitive data in error messages, stack trace leakage, inconsistent error shape.

## Mobile (Cross-Platform: React Native / Expo)

**Bridge** — native module compatibility, JS thread blocking, serialization overhead.

**Lifecycle** — AppState handling, background task cleanup, notification handler leaks.

**Platform** — iOS/Android API parity, native dependency conflicts, Expo module availability.

**Performance** — unnecessary re-renders, large bundle, image caching, Hermes compatibility.

## Game (Unity / Unreal)

**Unity** — MonoBehaviour lifecycle misuse, missing OnDestroy cleanup, Coroutines vs async, serialize field changes.

**Unreal** — UObject ownership, garbage collection, Blueprint/C++ boundary, delegate cleanup, Tick performance.

**Performance** — GC spikes, allocation in hot loops, draw call batching, physics performance.

**Asset** — resource loading/unloading, texture memory, scene transition leaks.
