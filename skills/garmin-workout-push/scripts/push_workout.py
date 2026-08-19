#!/usr/bin/env python3
"""
push_workout.py

Construit une seance de course a pied structuree a partir d'un JSON (meme
format que pour la generation TCX) et la POUSSE DIRECTEMENT dans ton compte
Garmin Connect via l'API (garminconnect + garth). Contourne le probleme de
l'import TCX/FIT non supporte par l'interface web de Garmin Connect.

Installation :
    pip install --upgrade "garminconnect[workout]" curl_cffi

Authentification :
    Variables d'environnement GARMIN_EMAIL et GARMIN_PASSWORD, ou saisie
    interactive si absentes. Les tokens sont mis en cache dans
    ~/.garminconnect apres la premiere connexion (pas besoin de MFA a
    chaque lancement).

Usage :
    python3 push_workout.py workout.json
    python3 push_workout.py workout.json --schedule 2026-08-25

Format du JSON d'entree : identique a celui du generateur TCX (voir
generate_tcx.py). Rappel :
{
  "name": "Nom de la seance",
  "steps": [
    {"type": "step", "name": "...", "intensity": "Warmup|Active|Resting|Cooldown",
     "duration": {"type": "time", "seconds": 900}
                 // ou {"type": "distance", "meters": 1000}
                 // ou {"type": "open"},
     "target": {"type": "pace", "low": "4:25", "high": "4:15"}
               // ou {"type": "hr", "low": 140, "high": 155}
               // ou {"type": "none"}},
    {"type": "repeat", "repetitions": 5, "children": [ {...}, {...} ]}
  ]
}
"""

import sys
import os
import json
import argparse
import getpass

from garminconnect import Garmin
from garminconnect.workout import (
    RunningWorkout,
    WorkoutSegment,
    ExecutableStep,
    RepeatGroup,
    SportType,
    StepType,
    ConditionType,
    TargetType,
    create_repeat_group,
)

TOKEN_STORE = os.path.expanduser("~/.garminconnect")

INTENSITY_TO_STEP_TYPE = {
    "Warmup": (StepType.WARMUP, "warmup"),
    "Active": (StepType.INTERVAL, "interval"),
    "Resting": (StepType.RECOVERY, "recovery"),
    "Cooldown": (StepType.COOLDOWN, "cooldown"),
}

STEP_ORDER = 0


def next_order():
    global STEP_ORDER
    STEP_ORDER += 1
    return STEP_ORDER


def pace_to_mps(pace_str):
    """Convertit une allure 'mm:ss' (par km) en metres/seconde."""
    minutes, seconds = pace_str.strip().split(":")
    total_seconds = int(minutes) * 60 + int(seconds)
    return round(1000.0 / total_seconds, 4)


def build_target(target):
    """Retourne (targetType_dict, target_value_one, target_value_two)."""
    if target is None or target.get("type") == "none":
        return {
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": TargetType.NO_TARGET,
        }, None, None

    ttype = target["type"]
    if ttype == "pace":
        lo, hi = sorted([pace_to_mps(target["low"]), pace_to_mps(target["high"])])
        return {
            "workoutTargetTypeId": TargetType.SPEED_ZONE,
            "workoutTargetTypeKey": "speed.zone",
            "displayOrder": TargetType.SPEED_ZONE,
        }, lo, hi
    elif ttype == "hr":
        lo, hi = sorted([int(target["low"]), int(target["high"])])
        return {
            "workoutTargetTypeId": TargetType.HEART_RATE_ZONE,
            "workoutTargetTypeKey": "heart.rate.zone",
            "displayOrder": TargetType.HEART_RATE_ZONE,
        }, float(lo), float(hi)
    else:
        raise ValueError(f"Type de cible non supporte: '{ttype}'")


def build_end_condition(duration):
    dtype = duration.get("type", "open")
    if dtype == "time":
        cond = {
            "conditionTypeId": ConditionType.TIME,
            "conditionTypeKey": "time",
            "displayOrder": ConditionType.TIME,
            "displayable": True,
        }
        return cond, float(duration["seconds"])
    elif dtype == "distance":
        cond = {
            "conditionTypeId": ConditionType.DISTANCE,
            "conditionTypeKey": "distance",
            "displayOrder": ConditionType.DISTANCE,
            "displayable": True,
        }
        return cond, float(duration["meters"])
    elif dtype == "open":
        cond = {
            "conditionTypeId": ConditionType.LAP_BUTTON,
            "conditionTypeKey": "lap.button",
            "displayOrder": ConditionType.LAP_BUTTON,
            "displayable": True,
        }
        return cond, None
    else:
        raise ValueError(f"Type de duree non supporte: '{dtype}'")


def build_step(node):
    if node["type"] == "repeat":
        order = next_order()
        children = [build_step(child) for child in node["children"]]
        return create_repeat_group(
            iterations=int(node["repetitions"]),
            workout_steps=children,
            step_order=order,
        )
    elif node["type"] == "step":
        order = next_order()
        intensity = node.get("intensity", "Active")
        step_type_id, step_type_key = INTENSITY_TO_STEP_TYPE[intensity]
        end_condition, end_condition_value = build_end_condition(
            node.get("duration", {"type": "open"})
        )
        target_type, target_low, target_high = build_target(node.get("target"))

        kwargs = dict(
            stepOrder=order,
            stepType={
                "stepTypeId": step_type_id,
                "stepTypeKey": step_type_key,
                "displayOrder": step_type_id,
            },
            endCondition=end_condition,
            endConditionValue=end_condition_value,
            targetType=target_type,
        )
        if target_low is not None:
            kwargs["targetValueOne"] = target_low
            kwargs["targetValueTwo"] = target_high

        return ExecutableStep(**kwargs)
    else:
        raise ValueError(f"Type de noeud non supporte: '{node['type']}'")


def estimate_duration_seconds(steps_json):
    """Estimation grossiere de la duree totale, utilisee uniquement pour le
    champ obligatoire estimatedDurationInSecs (Garmin peut la recalculer)."""
    DEFAULT_PACE_MPS = 1000.0 / 330  # ~5:30/km par defaut si aucune cible

    def step_seconds(node):
        if node["type"] == "repeat":
            return int(node["repetitions"]) * sum(
                step_seconds(c) for c in node["children"]
            )
        duration = node.get("duration", {"type": "open"})
        if duration.get("type") == "time":
            return duration["seconds"]
        elif duration.get("type") == "distance":
            target = node.get("target")
            if target and target.get("type") == "pace":
                lo = pace_to_mps(target["low"])
                hi = pace_to_mps(target["high"])
                speed = (lo + hi) / 2
            else:
                speed = DEFAULT_PACE_MPS
            return duration["meters"] / speed
        else:
            return 0

    return int(sum(step_seconds(s) for s in steps_json))


def build_workout(workout_json):
    global STEP_ORDER
    STEP_ORDER = 0

    steps = [build_step(s) for s in workout_json["steps"]]
    segment = WorkoutSegment(
        segmentOrder=1,
        sportType={
            "sportTypeId": SportType.RUNNING,
            "sportTypeKey": "running",
            "displayOrder": SportType.RUNNING,
        },
        workoutSteps=steps,
    )
    return RunningWorkout(
        workoutName=workout_json.get("name", "Seance"),
        sportType={
            "sportTypeId": SportType.RUNNING,
            "sportTypeKey": "running",
            "displayOrder": SportType.RUNNING,
        },
        estimatedDurationInSecs=estimate_duration_seconds(workout_json["steps"]),
        workoutSegments=[segment],
    )


def login():
    try:
        client = Garmin()
        client.login(TOKEN_STORE)
        print("Connecte via les tokens en cache.")
        return client
    except Exception:
        pass

    email = os.getenv("GARMIN_EMAIL") or input("Email Garmin Connect: ")
    password = os.getenv("GARMIN_PASSWORD") or getpass.getpass("Mot de passe: ")

    client = Garmin(
        email,
        password,
        prompt_mfa=lambda: input("Code MFA (si demande): "),
    )
    client.login(TOKEN_STORE)
    print("Connexion reussie, tokens sauvegardes dans", TOKEN_STORE)
    return client


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workout_json", help="Chemin vers le fichier JSON de la seance")
    parser.add_argument("--schedule", help="Date au format YYYY-MM-DD pour programmer la seance", default=None)
    args = parser.parse_args()

    with open(args.workout_json, "r", encoding="utf-8") as f:
        workout_json = json.load(f)

    workout = build_workout(workout_json)

    client = login()

    print(f"Envoi de la seance '{workout.workoutName}' vers Garmin Connect...")
    result = client.upload_running_workout(workout)
    workout_id = result.get("workoutId") or result.get("workoutID") or result.get("id")
    print(f"Seance creee. workoutId = {workout_id}")
    if workout_id:
        print(f"Lien: https://connect.garmin.com/modern/workout/{workout_id}")

    if args.schedule and workout_id:
        client.schedule_workout(workout_id, args.schedule)
        print(f"Seance programmee le {args.schedule}.")


if __name__ == "__main__":
    main()
