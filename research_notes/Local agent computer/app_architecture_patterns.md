# App architecture patterns for a local-first macOS screen-capture + local-AI + MCP app (from source code of high-star repos)

Method: shallow clones (`git clone --depth 1`, read-only, nothing built or run) on 2026-10-17 under
`/tmp/claude-0/-home-user-albers-club/3712d12f-853b-5b60-93d4-c8956af51529/scratchpad/clones/`. Star counts come from GitHub repository search on 2026-10-17. Source links use `blob/HEAD/<path>` so they resolve against the current default branch. The line numbers are from the snapshot read that day.

| Repo | Stars (approx) | Shape |
|---|---|---|
| [ollama/ollama](https://github.com/ollama/ollama) | 183.5k | Go daemon (`ollama serve`) + HTTP API + macOS/Windows tray app that supervises it; model runners as child processes |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 118k | Python library + CLI + MCP server |
| [immich-app/immich](https://github.com/immich-app/immich) | 116k | NestJS server + separate Python ML service + Flutter mobile app with Rust core over a C ABI; OpenAPI-generated clients; Extism (WASM) plugins |
| [zed-industries/zed](https://github.com/zed-industries/zed) | 92k | Pure Rust (own GPUI framework), WASM extensions, out-of-process crash handler |
| [syncthing/syncthing](https://github.com/syncthing/syncthing) | 89k | Go daemon + REST API + web UI; self-supervising "monitor" process |
| [ghostty-org/ghostty](https://github.com/ghostty-org/ghostty) | 62k | Zig core (libghostty) exposed through a C header + native Swift/AppKit macOS shell |
| [tailscale/tailscale](https://github.com/tailscale/tailscale) | 37.6k | Go daemon (tailscaled) + "LocalAPI" over a unix socket/localhost TCP; CLI, GUI and systray are all clients |
| [jordanbaird/Ice](https://github.com/jordanbaird/Ice) | 29.8k | Swift-only menu bar app |
| [screenpipe (moved to screenpipe/screenpipe; clone origin mediar-ai/screenpipe)](https://github.com/screenpipe/screenpipe) | 22k | Rust engine crates + Tauri app + localhost:3030 HTTP API + TS MCP server + "pipes" (agent plugins). **Now under a commercial license** (LICENSE.md) |
| [p0deje/Maccy](https://github.com/p0deje/Maccy) | 22k | Swift-only menu bar clipboard manager |
| [ActivityWatch/activitywatch](https://github.com/ActivityWatch/activitywatch) | 19.3k | Rust server (aw-server-rust) on localhost:5600 + separate watcher processes that POST heartbeats + web UI |
| [Hammerspoon/hammerspoon](https://github.com/Hammerspoon/hammerspoon) | 16.3k | ObjC app + embedded Lua + 91 extension modules; CFMessagePort IPC for the `hs` CLI |
| [signalapp/libsignal](https://github.com/signalapp/libsignal) | 6k | Rust core with generated FFI (Swift), JNI (Android) and Node bridges |

## Pattern 1: shared core + thin native shells (C ABI / FFI)

### Takeaway
Shells that are fully native and call a portable core through a narrow, generated C ABI are proven at the top end: Ghostty (Zig→Swift), libsignal (Rust→Swift/Java/TS) and Immich mobile (Rust→Dart). The cost is boilerplate at the boundary, which each project handles with code generation and strict rules (opaque handles, callbacks, catching panics at the edge). The pattern pays off when the same core must ship in more than one native UI (macOS + iOS + Android). For a single macOS app it is mostly overhead.

### Cited Findings
- Ghostty's macOS app is a Swift/Xcode app that embeds the core as a library. `src/apprt/embedded.zig` says: "Application runtime for the embedded version of Ghostty... used for example for the macOS build of Ghostty so that we can use a native Swift+XCode-based application." — [embedded.zig](https://github.com/ghostty-org/ghostty/blob/HEAD/src/apprt/embedded.zig)
- The ABI is one C header with opaque handles (`typedef void* ghostty_app_t; ghostty_surface_t; ghostty_config_t`) plus a `ghostty_runtime_config_s` struct of callbacks. The header warns: "All the types below are fully defined and must be kept in sync with their Zig counterparts." The enum already includes `GHOSTTY_PLATFORM_IOS`. — [include/ghostty.h](https://github.com/ghostty-org/ghostty/blob/HEAD/include/ghostty.h)
- The Swift shell drives the core through a wakeup callback plus a tick (`wakeup_cb: { userdata in App.wakeup(userdata) }`, `ghostty_app_new(...)`, `ghostty_app_tick(app)`). This is an inverted event loop where the native side owns the run loop. — [macos/Sources/Ghostty/Ghostty.App.swift](https://github.com/ghostty-org/ghostty/blob/HEAD/macos/Sources/Ghostty/Ghostty.App.swift)
- The build emits an xcframework for Apple ("libghostty-vt xcframework (Apple only, universal binary)"). — [build.zig](https://github.com/ghostty-org/ghostty/blob/HEAD/build.zig)
- Ghostty's native shell has OS features that a webview app cannot easily get: App Intents, AppleScript (`Ghostty.sdef`), Services, Secure Input, QuickTerminal, Global Keybinds, Sparkle Update. — [macos/Sources/Features](https://github.com/ghostty-org/ghostty/tree/HEAD/macos/Sources/Features), [macos/AGENTS.md](https://github.com/ghostty-org/ghostty/blob/HEAD/macos/AGENTS.md)
- libsignal writes each API once in Rust with `#[bridge_fn]`. The macro "Generates C, JVM, and Node entry points for Rust functions... It is explicitly *not* a goal for this layer to generate perfect C, Java, or TypeScript APIs. Rather, it should generate safe interfaces to *Rust* APIs, on top of which idiomatic Swift, Java, and TypeScript APIs can be built." Per-platform opt-outs look like `#[bridge_fn(ffi = false)]`. — [rust/bridge/shared/macros/src/lib.rs](https://github.com/signalapp/libsignal/blob/HEAD/rust/bridge/shared/macros/src/lib.rs), [rust/bridge/shared/src/protocol.rs](https://github.com/signalapp/libsignal/blob/HEAD/rust/bridge/shared/src/protocol.rs)
- libsignal catches Rust panics at the FFI boundary (`std::panic::catch_unwind` in the async FFI glue), so a panic does not unwind into Swift. — [rust/bridge/shared/types/src/ffi/futures.rs](https://github.com/signalapp/libsignal/blob/HEAD/rust/bridge/shared/types/src/ffi/futures.rs)
- Immich mobile ships a Rust "native core" inside the Flutter app: "`crates/native_core_ffi`: the C ABI, cbindgen writes `include/native_core.h`... ffigen bindings". — [native/README.md](https://github.com/immich-app/immich/blob/HEAD/native/README.md)
- ActivityWatch compiles its Rust server for Android and exposes it through JNI (`jni::objects::{JClass, JString}` in `aw-server/src/android`), with a `compile-android.sh` script. The same core runs on desktop and Android. — [aw-server-rust/aw-server/src/android](https://github.com/ActivityWatch/aw-server-rust/tree/HEAD/aw-server/src/android), [compile-android.sh](https://github.com/ActivityWatch/aw-server-rust/blob/HEAD/compile-android.sh)
- Screenpipe (Tauri/Rust) moved its heaviest UI surface out of the webview into native Swift. "The timeline is the one surface that renders thousands of elements while a video decodes... In the webview each frame bar was a DOM node... Trackpad scroll and pinch arrive as real `NSEvent`s rather than being bridged from Rust because WKWebView swallowed them." The Swift timeline gets its data over the engine's local API (`TimelineAPI.swift — /stream/frames websocket + REST`), with only window glue over C FFI (`TimelineWindow.swift — NSWindow, input handling, C FFI`). — [docs/NATIVE_TIMELINE.md](https://github.com/screenpipe/screenpipe/blob/HEAD/docs/NATIVE_TIMELINE.md)

### Inferences
- Ghostty's model (core library, Swift owns the run loop, the core calls back through a small C struct) is the cleanest "integrated feel" pattern. It needs discipline: a hand-maintained header, or a generator such as cbindgen/uniffi/`bridge_fn`.
- Screenpipe's move from webview to Swift for its timeline is direct evidence that a menu-bar/search-panel UI with heavy media is better in native Swift than in a webview. It also shows the data boundary can be the local API, not FFI.
- For a solo builder, the boundary that holds up best is a typed, generated one: uniffi or cbindgen for Rust, or simply HTTP/JSON with an OpenAPI or JSON schema. A hand-written C header is the most fragile option.

### Gaps
- None of the cloned repos uses uniffi or swift-bridge (libsignal uses its own macros, Immich uses cbindgen + ffigen). I found no source evidence comparing them.
- No XPC-based core/shell split was found in source. Tailscale's comments mention XPC between its closed-source macOS GUI and the NEPacketTunnelProvider, but that code is not in the repo.

## Pattern 2: headless daemon + clients over a local API

### Takeaway
This is the dominant pattern among the highest-star apps: Ollama, Tailscale, Syncthing, ActivityWatch, Screenpipe and Immich. One long-lived process owns the state (DB, models, capture) and exposes HTTP over loopback or a unix socket. The GUI, CLI, MCP server, plugins and mobile apps are all clients of that API. Localhost auth is handled in code with three layers: Host/Origin checks against DNS rebinding, a per-install bearer token, and sometimes peer-credential or "same-user proof" files.

### Cited Findings
- **Ollama**: the tray app does not run models itself. It starts `ollama serve` as a child process and restarts it in a loop. `Run()` waits `restartDelay = time.Second`, starts the command, writes a pidfile, and on exit code 1 "could be a port conflict, try to kill any existing ollama processes" (`reapServers`). At startup `cleanup()` kills a stale pid from the pidfile, and `stop()` escalates from graceful terminate to Kill after 5s. — [app/server/server.go](https://github.com/ollama/ollama/blob/HEAD/app/server/server.go)
- Ollama then runs each model in a further child process (`exec.Command(exe, params...)` in `llm/llama_server.go`). The scheduler expires and unloads idle runners and has an "OOM retry path: load() crashed post-spawn". A model crash does not take down the API server. — [llm/llama_server.go](https://github.com/ollama/ollama/blob/HEAD/llm/llama_server.go), [server/sched.go](https://github.com/ollama/ollama/blob/HEAD/server/sched.go)
- Ollama's localhost protection: when bound to loopback, `allowedHostsMiddleware` rejects requests whose Host header is not loopback, private, the machine hostname, or `*.localhost/.local/.internal`. This is DNS-rebinding defence. CORS origins are an allowlist (`OLLAMA_ORIGINS`). — [server/routes.go](https://github.com/ollama/ollama/blob/HEAD/server/routes.go), [envconfig/config.go](https://github.com/ollama/ollama/blob/HEAD/envconfig/config.go)
- **Tailscale**: `safesocket` "creates either a Unix socket, if possible, or otherwise a localhost TCP connection." On macOS the App Store and standalone GUIs talk to tailscaled via XPC. A downloaded CLI "must source the credentials from a 'sameuserproof' file", which tailscaled writes into `/Library/Tailscale` along with the port and token. — [safesocket/safesocket.go](https://github.com/tailscale/tailscale/blob/HEAD/safesocket/safesocket.go), [safesocket/safesocket_darwin.go](https://github.com/tailscale/tailscale/blob/HEAD/safesocket/safesocket_darwin.go)
- Tailscale's LocalAPI handler rejects any request that has a `Referer` or `Origin` header or an invalid Host, so browsers cannot reach it. It sets `Content-Security-Policy: default-src 'none'`, enforces an optional Basic-auth password with `subtle.ConstantTimeCompare`, and wraps each call in `CheckDeadlocks()`. — [ipn/localapi/localapi.go](https://github.com/tailscale/tailscale/blob/HEAD/ipn/localapi/localapi.go)
- Tailscale pushes state to clients with a streaming endpoint (`watch-ipn-bus`) instead of polling. A typed Go client library (`client/local`, `WatchIPNBus`) is shared by the CLI and the systray. — [client/local/local.go](https://github.com/tailscale/tailscale/blob/HEAD/client/local/local.go), [client/systray](https://github.com/tailscale/tailscale/tree/HEAD/client/systray)
- **Syncthing**: a REST API with `X-API-Key` plus CSRF protection wrapped around `/rest` (`api_csrf.go`, `api_auth.go`, `tokenmanager.go`). — [lib/api/api.go](https://github.com/syncthing/syncthing/blob/HEAD/lib/api/api.go)
- **Screenpipe**: the Tauri app hosts the engine in-process (`server_core.rs`: "Long-lived server core: DB, HTTP server, pipes, secrets. Started once on app launch"). Capture is a separate start/stoppable `CaptureSession`, so "the server stays alive across capture cycles". — [server_core.rs](https://github.com/screenpipe/screenpipe/blob/HEAD/apps/screenpipe-app-tauri/src-tauri/src/server_core.rs), [capture_session.rs](https://github.com/screenpipe/screenpipe/blob/HEAD/apps/screenpipe-app-tauri/src-tauri/src/capture_session.rs)
- The same engine also ships as a standalone headless binary (`crates/screenpipe-engine/src/bin/screenpipe-engine.rs`) and a tray-only low-resource mode (`headless.rs`). — [screenpipe-engine bin](https://github.com/screenpipe/screenpipe/tree/HEAD/crates/screenpipe-engine/src/bin), [headless.rs](https://github.com/screenpipe/screenpipe/blob/HEAD/apps/screenpipe-app-tauri/src-tauri/src/headless.rs)
- Screenpipe's API auth: non-localhost requests need `Authorization: Bearer <api_key>`. WebSocket upgrades accept the Cookie `screenpipe_auth`, a Bearer header, or `?token=`. The error tells users to "Get the key with `screenpipe auth token`, or set the `SCREENPIPE_API_KEY` env var". — [crates/screenpipe-engine/src/server.rs](https://github.com/screenpipe/screenpipe/blob/HEAD/crates/screenpipe-engine/src/server.rs)
- Screenpipe's MCP server is a separate thin TypeScript package that calls the HTTP API (`SCREENPIPE_API_URL`). Its tools include `search-content`, `list-meetings`, `activity-summary`, `search-elements`, `frame-context`, `export-video`, `health-check`, `list-monitors`. — [packages/screenpipe-mcp/src/index.ts](https://github.com/screenpipe/screenpipe/blob/HEAD/packages/screenpipe-mcp/src/index.ts), [api-base.ts](https://github.com/screenpipe/screenpipe/blob/HEAD/packages/screenpipe-mcp/src/api-base.ts)
- **ActivityWatch**: the server listens on port 5600 (5666 in testing) per `config.rs`. Watchers are separate processes that send `client.heartbeat(...)` through `aw_client`. Heartbeats merge events within a "pulsetime" window, which the code scales with poll time "so OS scheduling jitter doesn't break heartbeat chains". — [aw-server/src/config.rs](https://github.com/ActivityWatch/aw-server-rust/blob/HEAD/aw-server/src/config.rs), [aw_watcher_window/main.py](https://github.com/ActivityWatch/aw-watcher-window/blob/HEAD/aw_watcher_window/main.py)
- **Immich**: one OpenAPI spec (`open-api/immich-openapi-specs.json`) generates the clients for web, CLI and the Flutter app (`openapi: path: generated/openapi` in `mobile/pubspec.yaml`). ML runs as a separate Python service that unloads models after `model_ttl` seconds idle. — [open-api](https://github.com/immich-app/immich/tree/HEAD/open-api), [mobile/pubspec.yaml](https://github.com/immich-app/immich/blob/HEAD/mobile/pubspec.yaml), [machine-learning/immich_ml/main.py](https://github.com/immich-app/immich/blob/HEAD/machine-learning/immich_ml/main.py)
- Hammerspoon's CLI talks to the app over a `CFMessagePortCreateLocal` port, which is a macOS-native local IPC alternative to HTTP. — [extensions/ipc](https://github.com/Hammerspoon/hammerspoon/tree/HEAD/extensions/ipc)

### Inferences
- An MCP server maps naturally onto this pattern. Screenpipe's MCP package is just another HTTP client, so the MCP surface, CLI, UI and future phone sync all reuse one API.
- Recommended localhost hardening, combined from the code above:
  - bind to 127.0.0.1 or a unix socket in Application Support;
  - reject requests with a foreign Host header or any Origin/Referer (Tailscale, Ollama);
  - require a per-install bearer token stored in a 0600 file or the Keychain (Screenpipe, Syncthing);
  - give plugins scoped tokens (see Pattern 3).
- "In-process engine inside the GUI app" (Screenpipe) and "GUI supervises a child daemon" (Ollama) are both proven. The child-daemon variant gives crash isolation. The in-process variant is simpler and keeps TCC attribution under one app identity.

### Gaps
- Tailscale's macOS GUI is closed source, so its XPC/SMAppService code could not be inspected.
- No repo uses gRPC locally. All use HTTP/JSON (plus WebSocket or streaming) or native IPC.

## Pattern 3: plugins and extensions, and how they are sandboxed

### Takeaway
Three approaches are in use:
- WASM sandboxes with interrupts (Zed via wasmtime, Immich via Extism);
- OS-level sandboxes for agent-run commands (Zed: macOS Seatbelt / Linux bubblewrap);
- "Plugins are subprocess agents that call the local API with scoped tokens" (Screenpipe pipes).

Screenpipe's own spec documents many reliability gaps in its subprocess approach.

### Cited Findings
- Zed runs extensions in wasmtime with WASI and `config.epoch_interruption(true)`. A dedicated thread calls `engine.increment_epoch()`, so a runaway extension can be preempted. — [crates/extension_host/src/wasm_host.rs](https://github.com/zed-industries/zed/blob/HEAD/crates/extension_host/src/wasm_host.rs)
- Zed's `sandbox` crate: "Cross-platform sandboxing for commands run on behalf of the agent... macOS uses Seatbelt (`sandbox-exec`), Linux uses Bubblewrap (`bwrap`)... Restricted-network policies are enforced by an in-process HTTP/HTTPS proxy... callers only describe intent via `SandboxPolicy`." — [crates/sandbox/src/sandbox.rs](https://github.com/zed-industries/zed/blob/HEAD/crates/sandbox/src/sandbox.rs)
- Zed runs MCP ("context servers") as stdio subprocesses (`context_server/src/transport/stdio_transport.rs`). — [crates/context_server](https://github.com/zed-industries/zed/tree/HEAD/crates/context_server)
- Immich's plugin SDK uses `@extism/js-pdk` (JS compiled to WASM), and the server embeds `@extism/extism`. — [packages/plugin-sdk/package.json](https://github.com/immich-app/immich/blob/HEAD/packages/plugin-sdk/package.json), [server/package.json](https://github.com/immich-app/immich/blob/HEAD/server/package.json)
- Screenpipe pipes are a `pipe.md` file (config + prompt) run by a "Pi agent subprocess" that queries the API at localhost:3030. The project's own spec lists problems:
  - "A global `Semaphore::new(1)` serializes all pipe execution";
  - "The Pi agent subprocess uses `wait_with_output()` with **no timeout**";
  - PIDs are not recorded;
  - store.bin is read "with no locking";
  - and more ("Every one of these can fail independently, mid-execution").
  The banner says the spec is "Drifting", last verified 2026-05-22. — [docs/PIPE_EXECUTION_SPEC.md](https://github.com/screenpipe/screenpipe/blob/HEAD/docs/PIPE_EXECUTION_SPEC.md)
- Screenpipe pipe permissions: "Every pipe request carries a `Bearer sp_pipe_*` token... evaluates: deny → allow → default allowlist → reject. This is a backstop layer — the primary enforcement happens in the Pi extension." — [pipe_permissions_middleware.rs](https://github.com/screenpipe/screenpipe/blob/HEAD/crates/screenpipe-engine/src/pipe_permissions_middleware.rs)
- Hammerspoon exposes about 91 native extension modules to user Lua scripts with no sandbox: full trust, powerful, user-authored. — [extensions/](https://github.com/Hammerspoon/hammerspoon/tree/HEAD/extensions)

### Inferences
- For an app whose "plugins" are mostly external AI agents, MCP plus scoped API tokens (Screenpipe's model) is enough to start with. Per-plugin tokens with endpoint allowlists are worth copying.
- Run any untrusted code (agent-generated scripts) in a Seatbelt or WASM sandbox, as Zed does.
- Lessons from Screenpipe's spec, if subprocess plugins are added: timeouts, PID tracking, durable run queues, and snapshotting config at enqueue time.

### Gaps
- Raycast's extension runtime is closed source and was not examined.

## Reliability techniques actually in code

### Takeaway
Reliable apps put these concerns in dedicated, tested modules:
- process supervision with restart-loop limits;
- out-of-process crash capture;
- polled plus event-driven permission (TCC) monitoring;
- versioned SQLite migrations with a single writer;
- signature-checked updates that account for TCC;
- battery/thermal-aware throttling.

Screenpipe, the closest analogue to the target app, has the most of this code, and much of it exists because of macOS edge cases.

### Cited Findings
- **Supervision with loop limits (Syncthing)**: the monitor process re-execs the binary as a child (`exec.Command(binary, args[1:]...)`, marked with `STMONITORED=`). It keeps `restartCounts = 4` timestamps and gives up if they fall within `restartLoopThreshold = 60 * time.Second` ("Too many restarts; not retrying further"). It writes rotated logs and captures panics for upload (`panicUploadMaxWait`, `crash_reporting.go`). — [cmd/syncthing/monitor.go](https://github.com/syncthing/syncthing/blob/HEAD/cmd/syncthing/monitor.go)
- **Supervision (Ollama)**: restart loop, pidfile, stale-process reap, graceful-then-kill shutdown; see Pattern 2. Logs rotate via `app/logrotate`. — [app/server/server.go](https://github.com/ollama/ollama/blob/HEAD/app/server/server.go)
- **Crash isolation (Zed)**: "Install crash signal handlers and spawn the crash-handler subprocess" (re-execs `current_exe()`, minidumper over a socket, `CRASH_HANDLER_PING_TIMEOUT` 60s). On macOS the panic hook calls `exit(1)` to "prevent the macOS crash dialog". Zed also has a `hang_telemetry` crate that turns GPUI main-thread hang incidents into telemetry. — [crates/crashes/src/crashes.rs](https://github.com/zed-industries/zed/blob/HEAD/crates/crashes/src/crashes.rs), [crates/hang_telemetry](https://github.com/zed-industries/zed/tree/HEAD/crates/hang_telemetry)
- Screenpipe uses `tauri-plugin-sentry` and has `app_panic.rs` and `crash_log.rs`. Hammerspoon bundles `sentry-cocoa`. — [src-tauri/Cargo.toml](https://github.com/screenpipe/screenpipe/blob/HEAD/apps/screenpipe-app-tauri/src-tauri/Cargo.toml), [Hammerspoon Podfile](https://github.com/Hammerspoon/hammerspoon/blob/HEAD/Podfile)
- **Login items**:
  - Ollama uses `SMAppService agentServiceWithPlistName:@"com.ollama.ollama.plist"` (a plist inside `Contents/Library/LaunchAgents`) and respects `SMAppServiceStatusRequiresApproval` ("User has disabled our login behavior explicitly so leave it as is"). — [app/cmd/app/app_darwin.m](https://github.com/ollama/ollama/blob/HEAD/app/cmd/app/app_darwin.m)
  - Maccy and Ice use `sindresorhus/LaunchAtLogin-Modern` (an SMAppService wrapper). Screenpipe uses `tauri-plugin-autostart`. — [Maccy project](https://github.com/p0deje/Maccy), [Ice project](https://github.com/jordanbaird/Ice)
- **TCC permission monitoring (Screenpipe)**: `permission_monitor.rs` is the "single source of truth for permission events". It polls every 5s, and "On macOS the Screen Recording result comes directly from TCC rather than SkyLight's process-local preflight cache". It also takes eager reports from capture: when "`SCStream` errors with `PermissionDenied`. Fires within ~100ms". Mic revocation shows up only via polling because "the stream just goes silent". — [crates/screenpipe-engine/src/permission_monitor.rs](https://github.com/screenpipe/screenpipe/blob/HEAD/crates/screenpipe-engine/src/permission_monitor.rs)
- `permissions.rs` warns that `CGPreflightScreenCaptureAccess` can return a cached result and that `AXIsProcessTrusted` "will not see a grant made *after* the process started". So it separates passive polling from live checks and has `restart_after_screen_recording_permission`. — [src-tauri/src/permissions.rs](https://github.com/screenpipe/screenpipe/blob/HEAD/apps/screenpipe-app-tauri/src-tauri/src/permissions.rs)
- Ice polls permissions with `Timer.publish(every: 1, ...)`. — [Ice/Permissions/Permission.swift](https://github.com/jordanbaird/Ice/blob/HEAD/Ice/Permissions/Permission.swift)
- **Auto-update and TCC (critical gotcha)**: Screenpipe found that Tauri's updater "renames the *running* app bundle into a temp dir... so macOS TCC no longer attributes it to the app the user granted Screen Recording to, and ScreenCaptureKit starts returning -3801". The fix is to download and stage in the background, then install only at quit/relaunch. — [src-tauri/src/staged_update.rs](https://github.com/screenpipe/screenpipe/blob/HEAD/apps/screenpipe-app-tauri/src-tauri/src/staged_update.rs)
- Sparkle is the updater for Ghostty, Maccy and Ice. Ollama has its own updater that verifies the code signature of the extracted bundle (`verifyExtractedBundle` → "signature verification failed") and stages for `DoUpgradeAtStartup`. — [app/updater/updater_darwin.go](https://github.com/ollama/ollama/blob/HEAD/app/updater/updater_darwin.go)
- **SQLite**:
  - Screenpipe has 119 timestamped SQL migration files (`crates/screenpipe-db/src/migrations`). A write-coalescing queue batches writes under one `BEGIN IMMEDIATE` ("reduces per-write overhead from ~5ms... amortized over the entire batch"), has a sleep/wake pause, and keeps a 4096-entry channel "without backpressure reaching capture threads". AGENTS.md mandates "no second DB writer". — [write_queue.rs](https://github.com/screenpipe/screenpipe/blob/HEAD/crates/screenpipe-db/src/write_queue.rs), [AGENTS.md](https://github.com/screenpipe/screenpipe/blob/HEAD/AGENTS.md)
  - Screenpipe has a recovery contract: on `SQLITE_IOERR/CORRUPT/FULL/NOTADB`, close the writer, stop capture, verify via an independent connection, then resume or quarantine. This is in dedicated crates `screenpipe-sqlite-coordinator` and `screenpipe-sqlite-recovery`, plus `failpoint_vfs.rs` for fault-injection tests. — [docs/SQLITE_RECOVERY.md](https://github.com/screenpipe/screenpipe/blob/HEAD/docs/SQLITE_RECOVERY.md)
  - Ollama's app store uses `currentSchemaVersion = 19` with stepwise `migrateV1ToV2`… functions and has migration tests. — [app/store/database.go](https://github.com/ollama/ollama/blob/HEAD/app/store/database.go)
  - ActivityWatch probes `PRAGMA user_version` read-only against a `MIN_READ_COMPAT_DB_VERSION..=NEWEST_DB_VERSION` range before opening. — [aw-datastore/src/worker.rs](https://github.com/ActivityWatch/aw-server-rust/blob/HEAD/aw-datastore/src/worker.rs)
  - Zed's `sqlez` stores migration text per domain and panics on startup if a recorded migration's text no longer matches. — [crates/sqlez/src/migrations.rs](https://github.com/zed-industries/zed/blob/HEAD/crates/sqlez/src/migrations.rs)
- **Battery/thermal throttling (Screenpipe)**: "polls battery/thermal state, selects a power profile (Performance / Balanced / Saver), and broadcasts parameter changes to vision and audio subsystems via a `tokio::sync::watch` channel". On macOS it uses `pmset -g batt` + `NSProcessInfo` thermal/low-power state. It also has `sleep_monitor.rs`, `disk_pressure.rs`, `resource_monitor.rs`, `process_priority.rs`, and jemalloc "to reduce RSS bloat from fragmentation". — [crates/screenpipe-engine/src/power](https://github.com/screenpipe/screenpipe/tree/HEAD/crates/screenpipe-engine/src/power), [screenpipe-engine/Cargo.toml](https://github.com/screenpipe/screenpipe/blob/HEAD/crates/screenpipe-engine/Cargo.toml)
- **Capture-first invariant (Screenpipe)**: "Recording is the critical path. Never sacrifice an authorized recording to archival, compression, indexing... When processing cannot keep up, retain the recording and defer that work." — [AGENTS.md](https://github.com/screenpipe/screenpipe/blob/HEAD/AGENTS.md)
- **Single instance (Screenpipe)**: `tauri-plugin-single-instance` with deep-link. Maccy detects clipboard changes by polling `NSPasteboard.changeCount`. — [src-tauri/Cargo.toml](https://github.com/screenpipe/screenpipe/blob/HEAD/apps/screenpipe-app-tauri/src-tauri/Cargo.toml), [Maccy/Clipboard.swift](https://github.com/p0deje/Maccy/blob/HEAD/Maccy/Clipboard.swift)

### Inferences
- If you build in Swift, also stage updates (Sparkle installs on quit by default) and keep a stable signing identity and bundle path, or you will hit the same TCC attribution loss Screenpipe documented.
- These modules are worth copying early:
  - a permission monitor that combines polling with error-driven reports;
  - a single SQLite writer with batched transactions;
  - a power-profile broadcaster;
  - a "capture never blocks on processing" invariant.

### Gaps
- No source-level measurement of crash rates per technique. Effectiveness is inferred from each project's maturity.

## Language/runtime choices and how they affect bugginess, size, startup and memory

### Takeaway
The code shows the trade-offs:
- Swift-only menu bar apps (Maccy, Ice) are small and lean on a few well-known packages (Sparkle, KeyboardShortcuts, Defaults, LaunchAtLogin).
- Rust/Zig cores give portability and memory control, at the cost of a boundary layer.
- Webview apps (Tauri) hit input, perf and TCC-update issues on macOS that pushed Screenpipe partly back to Swift.

I found no verified numeric binary-size, startup or memory comparisons in the sources examined.

### Cited Findings
- Maccy's dependencies: Sparkle, KeyboardShortcuts, LaunchAtLogin-Modern, Defaults, Settings, fuse-swift (fuzzy search), swift-log, Sauce. It uses SwiftData models (`HistoryItem.swift`). — [Maccy](https://github.com/p0deje/Maccy)
- Ice's dependencies: Sparkle, LaunchAtLogin-Modern, AXSwift, CompactSlider, plus `Bridging` and `Swizzling` folders for private APIs. — [Ice/Ice](https://github.com/jordanbaird/Ice/tree/HEAD/Ice)
- Screenpipe workspace: about 490k lines across roughly 27 crates. AGENTS.md says root `cargo test` "never compiles" `src-tauri`, and native builds must use a "machine-wide native build queue" because of compile cost. — [AGENTS.md](https://github.com/screenpipe/screenpipe/blob/HEAD/AGENTS.md)
- Screenpipe's Tauri app pulls in about 15+ Tauri plugins (updater, autostart, single-instance, global-shortcut, deep-link, sentry, store, shell, permission-flow...) and still ships Swift code for the timeline, notification panel, shortcut reminder and LiveText. — [src-tauri/Cargo.toml](https://github.com/screenpipe/screenpipe/blob/HEAD/apps/screenpipe-app-tauri/src-tauri/Cargo.toml), [src-tauri/swift](https://github.com/screenpipe/screenpipe/tree/HEAD/apps/screenpipe-app-tauri/src-tauri/swift)
- Ollama's desktop app is Go + native Cocoa (`app_darwin.m`, `menu.h`) + a React UI in a webview (`app/ui`, `app/webview`). — [app/](https://github.com/ollama/ollama/tree/HEAD/app)
- Zed wrote its own GPU UI framework (`gpui`, `gpui_macos`, `gpui_ios`, `gpui_wgpu`...), which takes a large team. — [crates/](https://github.com/zed-industries/zed/tree/HEAD/crates)
- ActivityWatch's Python watchers needed a workaround because PyInstaller multiprocessing re-exec "kills the child — and eventually the parent, which stops sending heartbeats". This is runtime-packaging bugginess. — [aw_watcher_window/main.py](https://github.com/ActivityWatch/aw-watcher-window/blob/HEAD/aw_watcher_window/main.py)

### Inferences
- Swift-only gives the best macOS integration (TCC, ScreenCaptureKit, Vision OCR, AppIntents, NSPanel search) with the smallest surface for packaging bugs. Its weaknesses are Android reuse and Linux/Windows.
- A Rust core is justified mainly if Android/desktop reuse of capture or indexing logic is a real goal. Phone companions mostly need the sync/API layer, not the capture core, and Immich shows companions can be plain API clients with OpenAPI codegen.
- Avoid Python packaging (PyInstaller) for always-on daemons.

### Gaps
- No measured binary size, startup or RSS data in the repos; these would need building or external benchmarks, which were out of scope.

## Best fit for a solo builder using AI coding tools (iOS/Android companions later, MCP/agent-friendly)

### Takeaway
Supported by the patterns above:
- **Pattern 2 at the boundary**: one core process owning capture, the SQLite single writer, search and local models, exposing a token-protected, Host/Origin-checked localhost HTTP API defined by an OpenAPI/JSON schema.
- **Native Swift shell** for the menu bar and search panel, which on macOS can live in the same app bundle as the core.
- **MCP server as a thin client** of the same API.

Use FFI (Pattern 1) only if a cross-platform core is truly needed later.

### Cited Findings
- Screenpipe, the closest analogue, converged on this shape: engine + HTTP API + MCP-as-HTTP-client, with a native Swift UI for the heavy timeline fed by REST/WebSocket. — [docs/NATIVE_TIMELINE.md](https://github.com/screenpipe/screenpipe/blob/HEAD/docs/NATIVE_TIMELINE.md), [packages/screenpipe-mcp](https://github.com/screenpipe/screenpipe/tree/HEAD/packages/screenpipe-mcp)
- AI-agent-friendly repo conventions are visible in the code:
  - Screenpipe's AGENTS.md: short; points to docs; scoped test commands; "Recording is the critical path"; doc-freshness markers `doc-verified: <sha>` checked in CI.
  - Ollama and Ghostty also ship AGENTS.md/CLAUDE.md.
  - Ghostty's macOS AGENTS.md prescribes the exact build/test script.
  - [screenpipe AGENTS.md](https://github.com/screenpipe/screenpipe/blob/HEAD/AGENTS.md), [ghostty macos/AGENTS.md](https://github.com/ghostty-org/ghostty/blob/HEAD/macos/AGENTS.md), [ollama CLAUDE.md](https://github.com/ollama/ollama/blob/HEAD/CLAUDE.md)
- Immich shows companion apps built entirely against one generated OpenAPI client, with a small Rust native core only where needed. — [open-api](https://github.com/immich-app/immich/tree/HEAD/open-api), [native/README.md](https://github.com/immich-app/immich/blob/HEAD/native/README.md)
- Ghostty shows native-shell OS integrations (App Intents/Shortcuts, AppleScript) that also make an app scriptable by agents. — [macos/Sources/Features](https://github.com/ghostty-org/ghostty/tree/HEAD/macos/Sources/Features)

### Inferences
- One reasonable layout (inference, not a proven blueprint):
  - Swift app containing:
    - a `Core` module (capture via ScreenCaptureKit, OCR via Vision, SQLite + FTS5 single writer, embeddings, power manager, permission monitor);
    - a loopback HTTP server (or unix socket) with bearer token + Host/Origin checks;
    - a SwiftUI/AppKit menu bar + NSPanel search UI that calls Core directly in-process;
    - a separate small MCP stdio binary (or HTTP MCP endpoint) that calls the local API.
  - Local models in a child process (Ollama's pattern) for crash and memory isolation.
  - Login via SMAppService; updates via Sparkle with install-on-quit.
  - Phones later talk to a sync/API layer, not to FFI.
- Why this fits a solo builder with Claude Code: one language and toolchain for the macOS app, so there is no FFI glue to keep in sync. The API contract is plain text that AI tools read and test easily. MCP, CLI and phones reuse one surface.
- Move to a Rust core with generated bindings (libsignal/Immich style) only if the capture or indexing engine must run on Windows, Linux or Android.
- Risks to plan for, from the cited code: TCC attribution loss on update; stale `CGPreflightScreenCaptureAccess`/`AXIsProcessTrusted` results; SQLite contention or corruption; runaway plugin or agent subprocesses (no timeouts); battery and thermal load from continuous capture.

### Gaps
- No repo found that is a Swift-only screen-capture + MCP app of comparable scale, so the recommended layout is a synthesis, not something observed working end to end.
- uniffi/swift-bridge evaluation, XPC service designs and numeric performance comparisons remain unverified from source.

### Blocked sources
- GitHub REST API via `gh api repos/...` returned HTTP 403 ("GitHub access to this repository is not enabled for this session"). Star counts were taken from the GitHub MCP repository search instead.
- `mediar-ai/screenpipe` now redirects to `screenpipe/screenpipe`, which is under a commercial license (LICENSE.md). It is read here for patterns only.
- ActivityWatch meta-repo submodules (aw-qt process manager, aw-tauri) were not cloned (shallow clone without submodules), so aw-qt watcher supervision was not inspected. The standalone aw-server-rust and aw-watcher-window repos were read instead.
- The Tailscale macOS GUI and the Raycast extension runtime are closed source.
- Tauri-based apps other than Screenpipe were not cloned. ActivityWatch's aw-tauri submodule was unavailable.
