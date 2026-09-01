# Exemple réel

Séquence réellement utilisée le 19/08/2026 dans Claude Code pour créer et programmer
une séance sur Garmin Connect.

## 1. Prompt (dans Claude Code)

> ajoute cette séance pour demain
>
> Séance 2 — Footing : 1h en endurance fondamentale, allure 4:15-4:30/km, conversationnel

Puis, dans le même fil :

> ajoute aussi dans Garmin connect

> Par défaut, ajoute un échauffement en début de séance et un retour au calme en fin de séance si ce n'est pas précisé autrement.

## 2. JSON généré par Claude

```json
{
  "name": "Seance 2 - Footing",
  "steps": [
    {
      "type": "step",
      "name": "Footing endurance fondamentale",
      "intensity": "Active",
      "duration": {"type": "time", "seconds": 3600},
      "target": {"type": "pace", "low": "4:30", "high": "4:15"}
    }
  ]
}
```

## 3. Commande exécutée

```bash
python3 scripts/push_workout.py workout.json --schedule 2026-08-20
```

## 4. Sortie du script

```
Connecte via les tokens en cache.
Envoi de la seance 'Seance 2 - Footing' vers Garmin Connect...
Seance creee. workoutId = 1670075826
Lien: https://connect.garmin.com/modern/workout/1670075826
Seance programmee le 2026-08-20.
```

## 5. Résultat côté Garmin Connect

- Séance visible dans **Entraînement → Bibliothèque d'entraînements**, nommée
  "Seance 2 - Footing".
- Programmée le **20/08/2026** (visible dans le calendrier d'entraînement Garmin
  Connect).
- Lien direct : https://connect.garmin.com/modern/workout/1670075826
- Synchronisable sur la montre au prochain sync Garmin Connect ↔ montre.
- Cible d'allure : zone de vitesse correspondant à 4:15-4:30/km.
