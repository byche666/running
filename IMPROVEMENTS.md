# Planned improvements

List of ideas for evolving this project.

## Adding several workouts at once

Allow describing a batch of several sessions (e.g. a week's or a month's
training plan) in a single request, instead of one workout at a time. Things
to figure out:

- input format for multiple sessions (a list of JSON objects, one file per
  session, or a single file with several named entries)
- creating them in a loop via the Garmin API instead of a single call
- handling partial failures (some sessions succeed, others don't)
- optional scheduling of each session on a given date (`--schedule`) to
  build a full training calendar

## Cycling support

The `garmin-workout-push` skill currently only handles the Running sport.
Extending it to cycling would involve:

- using `CyclingWorkout` (already available in the `garminconnect` library)
  instead of `RunningWorkout`
- converting pace targets (min/km) into speed targets (km/h) and/or power
  targets (watts, power zones)
- reviewing the block vocabulary (warmup, main set, recovery still apply,
  but the duration/distance/target units change)
- generalizing the script to pick the sport as a parameter instead of
  hardcoding it

## Building an interface to improve the skill's ergonomics

Today the workflow goes through a conversation with Claude and running
command-line scripts (manual JSON, `python3 push_workout.py ...`). An
interface would reduce friction and input errors. Ideas:

- a simple web page (form) to build a session visually (blocks, paces,
  repetitions) without hand-writing JSON
- a preview of the session before sending (duration/distance/pace summary,
  possibly a pace-profile chart)
- a list of already sent/scheduled sessions, with the ability to edit or
  delete them directly from the interface
- managing Garmin credentials (email/password/MFA) through a form instead
  of a terminal prompt or environment variables

## VMA-based automatic pace calculation

Let the user set their VMA (maximal aerobic speed) as a fixed parameter so
the tool can automatically derive the target pace(s) for a session instead
of requiring paces to be typed out by hand every time. Ideas:

- store the VMA somewhere reusable across sessions (env var, config file, or
  passed as a CLI/skill parameter) instead of asking for it in each prompt
- support describing a block by percentage of VMA ("90% VMA", "105% VMA")
  and convert that into a `mm:ss/km` pace range
- keep manually specified paces as an override: VMA-based calculation should
  only kick in when no explicit pace is given for a block
- clarify rounding/tolerance rules (e.g. +/-3 to 5 sec/km band) consistently
  with the existing pace-target conversion rules
