---
name: garmin-workout-push
description: >
  Creates a structured running workout and sends it DIRECTLY to the user's
  Garmin Connect account via the API (script push_workout.py), available
  immediately in the training library and syncable to the watch. Use this skill
  whenever the user describes a running workout (intervals, specific pace,
  endurance, warm-up / main block / cool-down, "5x1km", pace or HR zones) and
  wants it created on Garmin, even without explicitly saying "API",
  "script", or "push" — e.g. "send this session to my Garmin",
  "create my workout for tomorrow on Garmin Connect". Requires network access
  and Python (Claude Code, local terminal) -- it does not work in a sandboxed
  environment without internet. It can also generate a downloadable .tcx as an
  alternative (less practical: not importable as a future workout in Garmin
  Connect).
---

# Garmin Workout Push

Creates structured running workouts and sends them **directly to the user's
Garmin Connect account** via the unofficial `garminconnect` API (a method that
has been validated and tested in real conditions). This is the preferred
approach: unlike importing a TCX/FIT file (not supported by the Garmin Connect
web interface for future workouts), the API push creates the workout directly
in the training library, ready to be sent to the watch.

Only the **Running** sport is supported by this skill.

**Mandatory prerequisites**: an environment with outbound network access and
Python (Claude Code locally, terminal). It does not work in a sandboxed
environment without internet access (for example, claude.ai without network
access). If the current environment does not have network access, warn the user
and, if relevant, offer to generate a `.tcx` file instead via
`scripts/generate_tcx.py` (see section "Alternative without network access").

## Workflow (main method: API push)

1. **Check dependencies**: ensure the library is installed.
   ```bash
   pip install --upgrade "garminconnect[workout]" curl_cffi
   ```

2. **Ask once for the default preference**: at the start of the first relevant
   interaction, ask the user whether they want a standard warm-up and/or
   cool-down added by default for future normal running sessions. Save the
   choice in `.garmin-workout-preferences.json` in the repo root. If the user
   says yes, store `"default_add_warmup_cooldown": true` and suggested time
   values; if they say no, store `false` and do not add them automatically.

3. **Check the persistent preference file**: before asking a workout-specific
   question, read `.garmin-workout-preferences.json`. If
   `default_add_warmup_cooldown` is `true`, use that default automatically and
   do not ask again unless the user overrides it. If the file is missing or the
   value is `false`, ask the user whether to include a standard warm-up and/or
   cool-down for this session.

4. **Understand the workout** described in natural language and translate it to
   JSON according to the schema below (same for TCX and API push, to stay
   consistent).

5. **Write this JSON to a temporary file** (for example, `/tmp/workout.json` or
   `workout.json` in the working directory).

4. **Run the push script**:
   ```bash
   python3 scripts/push_workout.py workout.json
   ```
   Optionally add `--schedule YYYY-MM-DD` to schedule the workout for a specific
   date directly.

   On the first run, the script asks for the Garmin Connect email and password
   (and an MFA code if configured) interactively, unless the
   `GARMIN_EMAIL` and `GARMIN_PASSWORD` environment variables are already set.
   Session tokens are then cached in `~/.garminconnect`: subsequent runs usually
   will not need to ask again for credentials, except when the refresh token has
   expired (rare).

5. **Confirm with the user**: the script prints a direct link to the workout in
   Garmin Connect (`https://connect.garmin.com/modern/workout/<id>`). Share that
   link and summarize in one or two sentences the structure of the workout sent
   (time/distances, target paces) for a quick verification.

## Conversion rules (natural language -> JSON)

See the complete schema and examples in `scripts/push_workout.py`
(header docstring). Key reminders:

- **Warm-up / cool-down**: `intensity: "Warmup"` / `"Cooldown"`.
  Duration in time (`{"type": "time", "seconds": ...}`) or distance
  (`{"type": "distance", "meters": ...}`) depending on what the user gives.

- **Standard running workout structure**: for a normal running session, the
  expected order is generally: `Warmup` at the start, main block, then
  `Cooldown` at the end. If the user does not specify warm-up/cool-down, the
  skill should check `.garmin-workout-preferences.json` first. If
  `default_add_warmup_cooldown` is set to `true`, it can apply the stored
  default without re-asking. Otherwise, it must ask whether they want those
  blocks added before creating the workout. It may propose adding them in the
  standard way, but it must never invent them without confirmation if the
  session is a test, VMA block, or a specialized workout that does not need
  them. If in doubt, ask for clarification or offer options such as: "Add a
  10-15 min warm-up and 5-10 min cool-down", "Only include the main block",
  or "Use my own warm-up/cool-down values".

- **Persistent default preference**: store the user's choice in
  `.garmin-workout-preferences.json` using a boolean such as
  `"default_add_warmup_cooldown": true` and optional minute values for the
  default warm-up and cooldown. The skill should reuse this file across runs so
  it does not ask the same question repeatedly unless the user changes the
  preference.

- **Repetitions** ("5x1km", "10 x 400m") -> node `{"type": "repeat",
  "repetitions": N, "children": [...]}`.

- **Paces** in "mm:ss/km" -> `{"type": "pace", "low": "...", "high": "..."}`.
  The order of low/high does not matter (it is sorted automatically). If only a
  single pace is given without a range, create a small symmetric range of +/-3
  to 5 seconds/km and state this in the final summary to the user.

- **Heart rate** -> `{"type": "hr", "low": bpm, "high": bpm}`.

- **Recovery** ("2 min recovery", "easy jog recovery") -> `intensity: "Resting"`,
  usually with a time duration. If the recovery pace is not specified, use a
  broad and easy default range (for example, 6:00-7:00/km) and mention it.

- **No target given** for a block -> `{"type": "none"}`. Never invent a pace
  that was not mentioned by the user.

- **Unspecified duration/distance** ("run until you are ready") ->
  `{"type": "open"}` (step validated manually on the watch).

## Complete example

User input:
> "Warm-up 15 min at 4:20, 5x1km at 3:38-3:42/km with 1 min 30 sec easy jog
> recovery, cool-down 3km"

```json
{
  "name": "Specific pace workout",
  "steps": [
    {"type": "step", "name": "Warm-up", "intensity": "Warmup",
     "duration": {"type": "time", "seconds": 900},
     "target": {"type": "pace", "low": "4:25", "high": "4:15"}},
    {"type": "repeat", "repetitions": 5, "children": [
      {"type": "step", "name": "1 km specific pace", "intensity": "Active",
       "duration": {"type": "distance", "meters": 1000},
       "target": {"type": "pace", "low": "3:42", "high": "3:38"}},
      {"type": "step", "name": "Easy jog recovery", "intensity": "Resting",
       "duration": {"type": "time", "seconds": 90},
       "target": {"type": "pace", "low": "7:00", "high": "6:00"}}
    ]},
    {"type": "step", "name": "Cool-down", "intensity": "Cooldown",
     "duration": {"type": "distance", "meters": 3000},
     "target": {"type": "pace", "low": "5:30", "high": "5:00"}}
  ]
}
```

## Alternative without network access

If the execution environment does not have internet access (making it impossible
install packages or call the Garmin API), use `scripts/generate_tcx.py` instead
to produce a downloadable `.tcx` file. Clearly warn the user that this file
cannot be imported as a future workout via the Garmin Connect web interface
(file import is reserved for already-recorded activities and routes); only a
manual copy as `.FIT` to the watch via USB, or manual entry in the Garmin Connect
workout creator, works with a simple file.

## Cautions

- Never invent values (pace, distance, duration, HR) that are not provided or
  inferable from context: ask for clarification instead of guessing.
- After a successful push, do not reopen/re-save the workout in the Garmin
  Connect web editor before verifying it on the watch: the web editor can
  misdisplay/misinterpret the pace target ("No target" even though the values
  are present), and saving from that state could overwrite the real target. The
  data stored through the API is reliable; only the web editor display can be
  misleading.
- If `client.login()` fails repeatedly (MFA, expired password, locked account),
  never explicitly ask for the password in plain text in the conversation: the
  user must enter it themselves in the interactive terminal prompt.
