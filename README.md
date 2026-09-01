# Running

This repository contains a Claude Code skill for creating structured running workouts and sending them directly to Garmin Connect.

This skill is intended to work in VS Code, including the VS Code environment where the skill can be used alongside GitHub Copilot or other supported tooling.

## What is in this repo

- [skills/garmin-workout-push](skills/garmin-workout-push) — the main skill package
- [skills/garmin-workout-push/SKILL.md](skills/garmin-workout-push/SKILL.md) — skill definition, conversion rules, and guardrails
- [skills/garmin-workout-push/README.md](skills/garmin-workout-push/README.md) — installation and usage guide
- [skills/garmin-workout-push/EXAMPLE.md](skills/garmin-workout-push/EXAMPLE.md) — example prompt, generated JSON, and Garmin result
- [skills/garmin-workout-push/scripts/push_workout.py](skills/garmin-workout-push/scripts/push_workout.py) — pushes workouts to Garmin Connect
- [skills/garmin-workout-push/scripts/generate_tcx.py](skills/garmin-workout-push/scripts/generate_tcx.py) — offline fallback to generate a `.tcx` file

## Main use case

The skill is designed for running sessions such as:

- interval workouts
- specific-pace sessions
- easy endurance runs
- warm-up / main block / cool-down sessions
- pace or heart-rate zone sessions

You can describe a workout in natural language, for example:

> 15 min warm-up at 4:20/km, 5x1km at 3:38-3:42/km with 1:30 jog recovery, 3km cooldown

and the skill will translate it into structured workout JSON before pushing it to Garmin Connect.

## Important rule for warm-up and cool-down

A normal running workout usually starts with a warm-up and ends with a cool-down.

However, the skill should not invent those blocks when:

- the user explicitly says the workout has no warm-up or cool-down
- it is a test session
- it is a special workout or VMA block
- the structure is intentionally different

If the user does not specify warm-up or cool-down, first check the repo-local preference file `.garmin-workout-preferences.json`. If a default is already saved there, reuse it instead of asking again. Otherwise, ask for confirmation or offer the standard options instead of guessing.

## Persistent default preference

The repo stores a default warm-up/cool-down choice in `.garmin-workout-preferences.json` so the skill does not ask the same question every time for normal running sessions.

Example:

```json
{
  "default_add_warmup_cooldown": true,
  "default_warmup_minutes": 10,
  "default_cooldown_minutes": 5
}
```

If the user says they want warm-up/cool-down added by default, update this file. If they prefer the main block only or want to choose each time, set the value to `false`.

## Quick start

1. Open the skill folder:

   ```bash
   cd running/skills/garmin-workout-push
   ```

2. Install the Python dependencies:

   ```bash
   pip install --upgrade "garminconnect[workout]" curl_cffi
   ```

3. Use the skill in Claude Code, or run the script directly with a JSON workout file.

4. If you do not have internet access, generate a `.tcx` file instead of pushing through the API.

## Recommended reading order

- Start with [skills/garmin-workout-push/README.md](skills/garmin-workout-push/README.md)
- Then read [skills/garmin-workout-push/SKILL.md](skills/garmin-workout-push/SKILL.md) for the technical rules
- Then review [skills/garmin-workout-push/EXAMPLE.md](skills/garmin-workout-push/EXAMPLE.md) for a real-world example

## Notes

- This uses Garmin Connect's unofficial API, so use it with your own account and credentials.
- The connection is made with your own Garmin login through the same app-compatible workflow, and your password is only entered in the local terminal prompt; it is not exposed in the chat itself.
- The API push is the preferred method because it creates the workout directly in Garmin Connect's library.
- A `.tcx` export is only an offline fallback and cannot replace the API workflow for future workouts in Garmin Connect.
