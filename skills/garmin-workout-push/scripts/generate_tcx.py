#!/usr/bin/env python3
"""
generate_tcx.py

Genere un fichier .tcx (Garmin Training Center XML) pour une seance de course
a pied structuree, a partir d'une description JSON.

Usage:
    python3 generate_tcx.py workout.json output.tcx

Format du JSON d'entree :
{
  "name": "Nom de la seance",
  "steps": [
    {
      "type": "step",
      "name": "Echauffement",
      "intensity": "Warmup",          // Warmup | Active | Resting | Cooldown
      "duration": {"type": "time", "seconds": 900}
                  // ou {"type": "distance", "meters": 1000}
                  // ou {"type": "open"}   (pas de duree fixe, bouton "lap")
      "target": {"type": "pace", "low": "4:25", "high": "4:15"}
                  // pace en min:sec par km. low = allure la plus lente,
                  // high = allure la plus rapide (l'ordre n'importe pas,
                  // le script trie automatiquement).
                  // ou {"type": "hr", "low": 140, "high": 155} (bpm)
                  // ou {"type": "none"}  (pas de cible)
    },
    {
      "type": "repeat",
      "repetitions": 5,
      "children": [ {...step...}, {...step...} ]
    }
  ]
}

Seul le sport "Running" est gere par ce skill.
"""

import sys
import json
import xml.dom.minidom as minidom
from xml.sax.saxutils import escape

STEP_COUNTER = 0


def next_id():
    global STEP_COUNTER
    STEP_COUNTER += 1
    return STEP_COUNTER


def pace_to_mps(pace_str):
    """Convertit une allure 'mm:ss' (par km) en metres/seconde."""
    parts = pace_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Format d'allure invalide: '{pace_str}' (attendu 'mm:ss')")
    minutes, seconds = int(parts[0]), int(parts[1])
    total_seconds = minutes * 60 + seconds
    if total_seconds <= 0:
        raise ValueError(f"Allure invalide: '{pace_str}'")
    return round(1000.0 / total_seconds, 4)


def build_target_xml(target):
    if target is None or target.get("type") == "none":
        return "<Target xsi:type=\"None_t\"/>"

    ttype = target["type"]
    if ttype == "pace":
        low_mps = pace_to_mps(target["low"])
        high_mps = pace_to_mps(target["high"])
        # Vitesse basse = allure la PLUS LENTE => la plus petite valeur m/s
        lo, hi = sorted([low_mps, high_mps])
        return (
            "<Target xsi:type=\"Speed_t\">"
            "<SpeedZone xsi:type=\"CustomSpeedZone_t\">"
            f"<LowInMetersPerSecond>{lo}</LowInMetersPerSecond>"
            f"<HighInMetersPerSecond>{hi}</HighInMetersPerSecond>"
            "</SpeedZone>"
            "</Target>"
        )
    elif ttype == "hr":
        lo, hi = sorted([int(target["low"]), int(target["high"])])
        return (
            "<Target xsi:type=\"HeartRate_t\">"
            "<HeartRateZone xsi:type=\"CustomHeartRateZone_t\">"
            f"<Low><Value>{lo}</Value></Low>"
            f"<High><Value>{hi}</Value></High>"
            "</HeartRateZone>"
            "</Target>"
        )
    else:
        raise ValueError(f"Type de cible non supporte: '{ttype}'")


def build_duration_xml(duration):
    dtype = duration.get("type", "open")
    if dtype == "time":
        return f'<Duration xsi:type="Time_t"><Seconds>{int(duration["seconds"])}</Seconds></Duration>'
    elif dtype == "distance":
        return f'<Duration xsi:type="Distance_t"><Meters>{int(duration["meters"])}</Meters></Duration>'
    elif dtype == "open":
        return '<Duration xsi:type="UserInitiated_t"/>'
    else:
        raise ValueError(f"Type de duree non supporte: '{dtype}'")


def build_step_xml(step):
    step_id = next_id()
    name = escape(step.get("name", ""))
    intensity = step.get("intensity", "Active")
    if intensity not in ("Warmup", "Active", "Resting", "Cooldown"):
        raise ValueError(f"Intensite invalide: '{intensity}'")

    duration_xml = build_duration_xml(step.get("duration", {"type": "open"}))
    target_xml = build_target_xml(step.get("target"))

    return (
        '<Step xsi:type="Step_t">'
        f"<StepId>{step_id}</StepId>"
        f"<Name>{name}</Name>"
        f"{duration_xml}"
        f"<Intensity>{intensity}</Intensity>"
        f"{target_xml}"
        "</Step>"
    )


def build_repeat_xml(step):
    step_id = next_id()
    repetitions = int(step["repetitions"])
    children_xml = "".join(build_node_xml(child) for child in step["children"])
    return (
        '<Step xsi:type="Repeat_t">'
        f"<StepId>{step_id}</StepId>"
        f"<Repetitions>{repetitions}</Repetitions>"
        f"{children_xml}"
        "</Step>"
    )


def build_node_xml(node):
    ntype = node.get("type")
    if ntype == "step":
        return build_step_xml(node)
    elif ntype == "repeat":
        # Dans le schema TCX, les enfants d'un Repeat_t sont balises <Child>
        step_id = next_id()
        repetitions = int(node["repetitions"])
        children_xml = "".join(
            f"<Child>{build_node_xml(child)}</Child>" for child in node["children"]
        )
        return (
            '<Step xsi:type="Repeat_t">'
            f"<StepId>{step_id}</StepId>"
            f"<Repetitions>{repetitions}</Repetitions>"
            f"{children_xml}"
            "</Step>"
        )
    else:
        raise ValueError(f"Type de noeud non supporte: '{ntype}'")


def generate_tcx(workout):
    global STEP_COUNTER
    STEP_COUNTER = 0

    name = escape(workout.get("name", "Seance"))
    steps_xml = "".join(build_node_xml(step) for step in workout["steps"])

    tcx = f"""<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd">
  <Workouts>
    <Workout Sport="Running">
      <Name>{name}</Name>
      {steps_xml}
    </Workout>
  </Workouts>
</TrainingCenterDatabase>"""
    return tcx


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 generate_tcx.py workout.json output.tcx", file=sys.stderr)
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    with open(input_path, "r", encoding="utf-8") as f:
        workout = json.load(f)

    tcx = generate_tcx(workout)

    # Valide que le XML est bien forme avant d'ecrire le fichier final
    minidom.parseString(tcx)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tcx)

    print(f"Fichier TCX genere: {output_path}")


if __name__ == "__main__":
    main()
