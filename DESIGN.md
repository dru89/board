# Design decisions

The "why" behind choices that aren't obvious from the code. If you're a
future session (human or agent) picking this project up: read this and
ROADMAP.md before proposing changes.

## Architecture: HA computes, the device renders

ESPHome can't call HA services that return responses (`calendar.get_events`,
`weather.get_forecasts`), so anything derived from those is computed by HA
automations and staged into `input_text`/`input_number` helpers (`eink_*`
namespace) that the device imports as plain sensors. This split has three
deliberate benefits:

- All behavior thresholds are HA helpers — tunable from the "eInk Board"
  dashboard with zero reflashes.
- The device lambda stays a dumb renderer; logic bugs are fixable in the HA
  UI in seconds.
- A future bigger panel (see ROADMAP) reuses the entire HA pipeline
  regardless of rendering stack.

Data contracts between HA and device:

- `eink_event_1..7`: `YYYY-MM-DD|label|badge|title` (label is a display
  string: a time, "All day", "thru THU", or "ends 8 AM").
- `eink_day_status`: `YYYY-MM-DD|S|P;...` — 4 days; status letter
  (O/H/T/V/S/-) then on-call letter (P/S/-).
- `eink_battery_worst`: display-ready string ("Garage lock 2%") or empty.

## Refresh strategy (7.50inv2p driver)

- Minute-tick partial refresh (~2s) via `time.on_time`; full refresh every
  30th update (`full_update_every: 30`) to clear ghosting.
- **Forcing a full refresh must reset the driver's `at_update_` counter**
  (via the `ForceFull` subclass shim in the `full_refresh` script). Do NOT
  use `set_full_update_every(1)`: that branch of the driver writes the
  inverted buffer and expects the data-polarity register as `initialize()`
  left it (CDI 0x10), but every normal render sets 0xA9 — the result is a
  fully inverted frame until the next partial. Found the hard way.
- Boot splash renders via full refresh: after any reboot the panel's own RAM
  may hold a stale frame, and partials diff against panel RAM.
- On HA reconnect: quick partial (fast feedback), then a full refresh 20s
  later once sensor states have settled. Never full-refresh a half-populated
  frame — early sparse renders are what ghost.
- Never draw a fallback icon for data that simply hasn't arrived yet — blank
  ghosts invisibly, icons don't.

## Display semantics

- **Clock**: 12h, no AM/PM. Roboto digits are equal-width; "11:00 PM"
  side-by-side needs 327px in a 296px column. Chosen over shrinking the
  clock or condensed fonts (options A–D evaluated 2026-07-14; Drew picked
  "no AM/PM"). The mockup's sample time is pinned to "11:00" so layout
  changes are always eyeballed against the worst case.
- **Rain**: max precipitation probability over the next 12 hourly buckets,
  counting only buckets passing BOTH thresholds (probability ≥
  `eink_thresh_rain_pct`, amount ≥ `eink_thresh_rain_amt` in/hr). Rationale:
  PoP alone overweights trace rain ("25%, 0.1 inches ≈ no rain at all" —
  Drew). `~3 PM` = the first qualifying bucket's start hour; OWM buckets are
  hour-wide, so minutes would be fake precision. A trace-only day shows
  "Rain 0%" by design. When timing is shown, "mph" is dropped from the wind
  to keep the line inside the column.
- **Multi-day events**: ongoing events clamp to TODAY (so they show once,
  daily). Label "thru THU" uses an effective end of `end - 9h` for timed
  events (ending ≤9am doesn't claim that day) and `end - 1 day` for all-day
  events (calendar end dates are exclusive). An in-progress event ending
  later today shows "ends 8 PM".
- **On-call**: a day is marked if the shift overlaps 9am–9pm local. Title
  containing "secondary" → plain pager icon; anything else → primary →
  inverted chip. Primary beats secondary on handoff days. Back-to-back
  rotations (8am→8am) resolve to exactly one icon per day.
- **Day status**: from all-day events on `calendar.work_status`, keyword
  match with priority Sick > Vacation > Travel > WFH > Office (sick is
  last-minute; vacation/travel are non-standard — Drew's ordering). Icons:
  briefcase/laptop/airplane/palm-tree/medical-bag. Day headers for today+2
  always render (empty day = free day, and gives status icons an anchor).
- **Status bar**: `eink_status_priority` is one list controlling display
  order AND drop order (least important last; dropped first when alert
  pills need room; removing a token hides the item). Alert states render as
  inverted pills and are never dropped. Battery pill shows worst offender
  by name + `+N` (a named battery gets acted on; "check HA" gets ignored).
- **Dedupe**: same normalized title + same start on 2+ calendars → one row,
  F badge.
- **Trash/recycling**: pure on-device date math (no HA entity): badge Mon
  noon → Tue noon; recycling parity anchored to 2026-07-14 (a recycling
  pickup) via days-from-civil / 7 / mod 2.
- **Philosophy** (borrowed from hawksley.org's Timeframe): calm by default,
  blank means healthy, inverted means "needs you". The display shows
  status; it does not control anything.

## Hardware notes

- ESP32 devkit (esp32dev), Waveshare 7.5" V2 panel, ESPHome with esp-idf.
- Panel supports `7.50inv2p` (manufactured post-Sept-2023); busy pin
  inverted per that model's requirement.
- PWR pin GPIO21 driven high at boot before display init.
- mDNS doesn't resolve from the dev desktop; OTA by IP (see README).
- HA entity `esphome-web-079390` at another IP is a DIFFERENT ESP32-C3
  device — do not flash it.
