# garmin-workout-push

[Claude Code](https://claude.com/claude-code) skill that creates structured running
workouts (warmup / main set / repetitions / cooldown, target paces or heart-rate
zones) and sends them **directly to your Garmin Connect account**, ready to sync
to your watch — no need to go through the Garmin web editor.

Uses the unofficial [`garminconnect`](https://github.com/cyberjunky/python-garminconnect)
API (the same mechanism the Garmin Connect app itself uses), with **your own
credentials**.

See [`EXAMPLE.md`](./EXAMPLE.md) for a complete real-world example (the exact
prompt sent to Claude, the generated JSON, and the result on Garmin Connect).

## What it does

- You describe a session to Claude in natural language ("15min warmup at
  4:20/km, 5x1km at 3:38-3:42/km with 1min30 jog recovery, 3km cooldown").
- Claude translates it into structured JSON and runs `scripts/push_workout.py`.
- The session shows up in your Garmin Connect workout library, with a direct
  link (`https://connect.garmin.com/modern/workout/<id>`), and can be
  scheduled on a specific date with `--schedule`.
- Only the **Running** sport is supported.

### Warm-up / cool-down default

For a normal running session, the standard layout is usually:

1. warm-up at the start
2. main block in the middle
3. cool-down at the end

If the user does not specify warm-up/cool-down, you may suggest adding them in
this standard order. But do not invent them for specialized workouts, test
sessions, or any workout where the user clearly does not want them.

An offline fallback (`scripts/generate_tcx.py`) generates a plain `.tcx` file
if you don't have network access — but this file **cannot** be imported as a
future session through the Garmin Connect web interface (file import there is
reserved for already-recorded activities / courses). The API push is
therefore the preferred method.

## Requirements

- [Claude Code](https://claude.com/claude-code) installed (or any environment
  able to run Python with outbound network access — the skill does not work in
  a sandboxed environment without internet, e.g. claude.ai without network
  access).
- Python 3.
- A Garmin Connect account.

## Installation

1. **Clone this repo**, then copy this folder into Claude Code's skills
   directory, either globally or per project:

   ```bash
   git clone https://github.com/byche666/running.git
   cd running

   # Global skill (available in every project)
   mkdir -p ~/.claude/skills
   cp -R skills/garmin-workout-push ~/.claude/skills/

   # OR project-local skill
   mkdir -p .claude/skills
   cp -R skills/garmin-workout-push .claude/skills/
   ```

2. **Install the Python dependencies**:

   ```bash
   pip install --upgrade "garminconnect[workout]" curl_cffi
   ```

3. Restart Claude Code (or start a new session) so the skill gets detected.

## Usage

In Claude Code, just describe your session and ask to send it to Garmin:

> Push this session to my Garmin: 15min warmup at 4:20/km, 5x1km at
> 3:38-3:42/km with 1min30 jog recovery, 3km cooldown

> Create tomorrow's session on Garmin Connect: 1h easy run at 4:15-4:30/km

Claude translates the description into JSON (see the schema in `SKILL.md` and
in the `scripts/push_workout.py` docstring), writes it to a temporary file,
then runs:

```bash
python3 scripts/push_workout.py workout.json
# or, to schedule the session directly on a given date:
python3 scripts/push_workout.py workout.json --schedule 2026-08-20
```

### Authentication

On first run, the script interactively asks for your Garmin Connect email and
password (and an MFA code if you have one configured). You can also set the
`GARMIN_EMAIL` and `GARMIN_PASSWORD` environment variables to avoid typing
them manually.

Session tokens are then cached in `~/.garminconnect`: subsequent runs
normally won't need to ask for credentials again (except on the rare
occasion the refresh token expires).

⚠️ Never share your Garmin password in plain text in a conversation with
Claude — type it only into the terminal's interactive prompt.

### Command-line usage (without Claude)

You can also call the scripts directly with a hand-written JSON file:

```json
{
  "name": "Easy run",
  "steps": [
    {
      "type": "step",
      "name": "Easy endurance run",
      "intensity": "Active",
      "duration": {"type": "time", "seconds": 3600},
      "target": {"type": "pace", "low": "4:30", "high": "4:15"}
    }
  ]
}
```

```bash
python3 scripts/push_workout.py workout.json --schedule 2026-08-20
```

Full schema (repetitions, heart-rate targets, recovery, open-ended "open"
steps) documented in `SKILL.md`.

## Points to watch out for

- Don't manually fill in paces/durations that weren't specified: the skill
  should never invent a value that wasn't provided.
- After a successful push, avoid reopening/resaving the session in the
  Garmin Connect web editor before checking it on the watch: the web editor
  can misdisplay the pace target ("No target" even though it's actually set
  on the API side), and saving from that state could genuinely overwrite it.
- This uses an unofficial Garmin Connect API (the `garminconnect` library):
  use at your own risk, with your own credentials.

### Troubleshooting

- `AttributeError` on `TargetType.SPEED` / `TargetType.HEART_RATE` (or the
  other way around, `TargetType.SPEED_ZONE` / `TargetType.HEART_RATE_ZONE`):
  the member names of the `garminconnect` library's `TargetType` enum have
  changed across versions. Check the names actually available in your
  environment before editing `scripts/push_workout.py`:

  ```bash
  python3 -c "from garminconnect.workout import TargetType; print([x for x in dir(TargetType) if not x.startswith('_')])"
  ```

  The version of `scripts/push_workout.py` in this repo uses `SPEED` /
  `HEART_RATE`, matching the `garminconnect` version this skill was tested
  and validated against.

## Files

| File                         | Role                                                                |
|------------------------------|----------------------------------------------------------------------|
| `SKILL.md`                  | Skill definition (triggers, conversion rules, examples)            |
| `scripts/push_workout.py`   | Sends the session directly to Garmin Connect via the API           |
| `scripts/generate_tcx.py`   | Generates a downloadable `.tcx` file (offline alternative)          |
| `EXAMPLE.md`                 | Real example: prompt, generated JSON, result on Garmin Connect     |
