# Printer control, observation and safety (Klipper/Moonraker-class printers)

Applies to networked printers with an HTTP API (Klipper with Moonraker is the example here). Endpoint names, fields and firmware behaviour vary by printer and version; read the live system and the firmware's own documentation. Never put real addresses, credentials or fleet inventories in a skill or report; use `<printer-host>` placeholders and the operator's configured service.

## 1. Idle check and authorisation for setup-type changes

Before any change to a printer or firmware setting, a scan, homing, calibration or mesh test, a remote screen, SSH or video toggle, or a restart of any service:

1. Read the live state (`print_stats` via the object query endpoint) and require a non-printing state.
2. Confirm the operator authorised **this** change (not merely monitoring).
3. Change one thing at a time, read back through the API, and test the real service rather than trusting a success message.
4. After a restart-causing change require the controller healthy (`klippy_state=ready` and the expected components in the server info) before the next step.
5. State the service impact first. Treat every settings toggle that restarts a service as a mutation.

## 2. Active and paused jobs

- During a print, investigation is **read-only**: HTTP GET, file range downloads, log reads. No restart of Klipper, Moonraker, camera or printer, no firmware work, no Z-offset changes in response to higher-layer scraping, no editing the live file.
- A **paused** job is still a job. The same prohibition applies.
- The one supported exception is an **explicitly authorised paused-job recovery**, run strictly under a scoped procedure for that printer and fault (paused state, named target, its gates and post-checks, such as `snapmaker-u1-operations.md` section 3). It does not make a generic resume, remap or tool change acceptable. If any gate is uncertain use the supported manual fallback (for example load filament in the original tool and resume from the touchscreen).
- Setup-type idle checks (section 1) do not apply to that authorised recovery, and the recovery does not licence setup changes.

## 3. Remote control is control

Enabling touch injection, a remote screen, SSH, RTSP or any write endpoint needs the operator's authorisation. Prefer the firmware's native, authenticated route over adding another service (for example another VNC stack); keep it inside the existing private-network and TLS boundary; never expose SSH or a framebuffer listener to the WAN; do not weaken the existing login flow; do not enable wildcard CORS. For explicitly authorised LAN-only SSH enable the documented setting, then make a non-authenticated TCP and host-key probe; the SSH scope does not enable any VPN or cloud provider as a side effect. Do not attempt credentialed logins, and retrieve any default credentials only from the matching firmware-tag documentation. An open port is not a verified video stream: for RTSP require an `OPTIONS` and `DESCRIBE` success.

When verifying a web route that serves an image (for example a framebuffer snapshot), use a **GET**, not only HEAD, then confirm MIME type and a non-zero payload.

## 4. Active-print remote observation (evidence ladder)

Keep all probes read-only.

1. **Reachability** (ICMP or TCP and the web UI) establishes network access only.
2. **Controller health:** server info with Klippy connected and ready, no failed components; observe and report any controller warnings as well as the ready and failed components.
3. **Job health:** object query for `print_stats`, `toolhead`, the active extruder and `heater_bed`. `state=printing`, no error, advancing layer or print duration across **two samples**, and temperatures tracking targets are telemetry evidence of a live healthy job, not visual proof of adhesion or geometry.
4. **Visual evidence:** only a current webcam frame or stream supports claims about adhesion, spaghetti, collisions or quality. Read the webcam list first, request only the declared snapshot or stream route and restart nothing. An empty list or a proxy error means the live camera path is unavailable. Timelapse or archive files establish only their own capture time and must never be presented as a current view.
5. **Shell access:** a stock printer may expose the web UI without SSH. Test port 22 with a bounded TCP connection; a closed port means no shell route was demonstrated. Do not infer SSH from a slicer connecting.

A dark live snapshot is not a clear-bed check. Do not infer a clean bed from telemetry; use a current camera frame or the operator's confirmation immediately before homing or probing.

## 5. Physical motion tests

Only after explicit authorisation to move the printer, a current clear-bed check and a fresh standby confirmation. A request that stays open while the printer executes can time out on the client: do **not** repeat it; inspect the live toolhead, idle state and command store (and a completion marker you appended) first. Park and lift safely afterwards and verify the printer reports ready.

## 6. Logs, configuration and secrets

- Read only what you need; do not dump settings endpoints that carry credentials (read only the relevant section).
- Redact hosts, passwords, tokens and API keys, including camelCase variants, before writing any shareable log, settings or bundle.
- Encrypted support exports: preserve originals and compress nothing further; they do not recompress.

## 7. Release monitoring

A quiet release watcher should be script-only (no model), accept only non-draft, non-prerelease tags at or above the approved base, compare full semantic versions plus build numbers (not a regex tied to one patch line), print nothing while absent, remember the last notified tag, tolerate transient network errors silently, and still be followed by a changelog and known-bug review before anyone recommends a flash. A saved review date is not active watching; set up monitoring only when the operator asks and verify the mechanism works.
