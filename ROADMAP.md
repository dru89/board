# Roadmap

Future work, roughly in order, with the intended approach for each. Primary
inspiration: [Timeframe](https://hawksley.org/2026/02/17/timeframe.html)
(Joel Hawksley's family e-paper dashboard) — the target aesthetic is
"framed art that happens to be a display", not "gadget on the wall".

## Housing (next up)

Shadow box as the first prototype:
- Mat board with a window cut for the active display area — hides the
  panel's silver bezel and FPC ribbon; single biggest looks upgrade.
- Consider omitting the glass (glare kills the paper illusion); non-glare
  picture glass if structure demands it.
- Panel mounted to rigid backing; gentle FPC bend — the ribbon is the most
  fragile part.
- Right-angle USB-C out a bottom pilot hole with strain relief. This is
  wall-powered by design; battery operation is off the table at
  minute-resolution refresh.
- Drill the front LED pilot holes and top button carveouts NOW even if
  unpopulated — retrofitting a hung box is the bad version of that job.
- A picture light above the frame (see the Timeframe nook photo) does more
  aesthetic work than any software change.
- Later: 3D-printed frame (PETG if sunlight), screwless/magnet back since
  OTA means the box only opens for hardware.

## Buttons (ideas parked until the housing exists)

Wire 2–3 momentary tactile switches (real click — mushy buttons + 2s e-ink
response feels broken) to spare GPIOs; assign meaning in config later.
Leading candidates:
- Second screen (e.g. 5-day forecast / full-week agenda) that auto-reverts
  after a couple of minutes.
- Acknowledge/snooze the current alert pill.
- Force full refresh.

Principle (from Timeframe): the display shows status, it does not control
the house. Buttons stay display-scoped.

## LEDs

Off 99% of the time. A single soft indicator for genuinely urgent states
(alarm triggered, door open late at night), through light pipes rather than
bare LEDs, with a time-based cutoff. WS2812 strip = one data pin in ESPHome.

## Bigger panel for a prominent wall spot

Ladder: 13.3" Waveshare (1600×1200, ~$300, stays on the ESPHome stack) as
the middle rung; Boox Mira Pro 25.3" (~$2k, HDMI, host-rendered) as the
endgame. Hawksley rejected the 32" tier for contrast. The HA-side pipeline
(eink_* helpers/automations) carries over to either unchanged.

Big-panel layout should adopt what the 7.5" is too small for:
- Portrait orientation (agendas are lists; lists are tall).
- Top status strip: blank when the house is healthy, one big item when not
  ("Washer", "Front unlocked").
- Hourly weather woven into the agenda as timeline rows ("12p — 87°",
  "9–11p — Rain").
- Minute-scale rain histogram (Now/20m/40m) — needs minutely data, which
  means hitting OWM One Call directly rather than the HA integration.

## Personal desk display (spare devkit #2 of 3)

Drew-only stats, same architecture (HA helpers feed a dumb renderer):
- Claude usage: `ccusage` output → HA command-line sensor.
- Up-next queues: Plex/Trakt/Steam integrations in HA.

## Data/feature ideas not yet scheduled

- Working-location fidelity: statuses come from the personal
  `calendar.work_status` calendar (all-day keyword events), NOT the real
  work calendar (Outlook-mirrored, messy, low fidelity — deliberately
  avoided).
- Battery alert could grow a second named entry if the single
  worst-offender + count pattern proves insufficient.
