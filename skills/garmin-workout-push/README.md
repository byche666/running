# garmin-workout-push

Skill [Claude Code](https://claude.com/claude-code) qui crée des séances de course à pied
structurées (échauffement / bloc principal / répétitions / retour au calme, allures ou
zones de FC cibles) et les envoie **directement dans ton compte Garmin Connect**, prêtes
à être synchronisées sur ta montre — sans passer par l'éditeur web de Garmin.

Utilise l'API non-officielle [`garminconnect`](https://github.com/cyberjunky/python-garminconnect)
(le même mécanisme que l'app Garmin Connect elle-même), avec **tes propres identifiants**.

Voir [`EXAMPLE.md`](./EXAMPLE.md) pour un exemple réel complet (prompt exact envoyé à
Claude, JSON généré, et résultat obtenu côté Garmin Connect).

## Ce que ça fait

- Tu décris une séance en langage naturel à Claude ("échauffement 15min à 4:20/km,
  5x1km à 3:38-3:42/km avec 1min30 de récup trot, retour au calme 3km").
- Claude traduit ça en JSON structuré et exécute `scripts/push_workout.py`.
- La séance apparaît dans ta bibliothèque d'entraînements Garmin Connect, avec un lien
  direct (`https://connect.garmin.com/modern/workout/<id>`), et peut être programmée
  sur une date précise avec `--schedule`.
- Seul le sport **Running** est géré.

Une alternative hors-ligne (`scripts/generate_tcx.py`) génère un simple fichier `.tcx`
si tu n'as pas d'accès réseau — mais ce fichier ne peut **pas** être importé comme séance
future via l'interface web de Garmin Connect (import réservé aux activités déjà
enregistrées / parcours). Le push API est donc la méthode à privilégier.

## Prérequis

- [Claude Code](https://claude.com/claude-code) installé (ou un environnement capable
  d'exécuter du Python avec accès réseau sortant — le skill ne fonctionne pas dans un
  environnement sandboxé sans internet, ex. claude.ai sans accès réseau).
- Python 3.
- Un compte Garmin Connect.

## Installation

1. **Cloner ce repo**, puis copier ce dossier dans le répertoire de skills de Claude
   Code, globalement ou par projet :

   ```bash
   git clone https://github.com/byche666/running.git
   cd running

   # Skill global (disponible dans tous les projets)
   mkdir -p ~/.claude/skills
   cp -R skills/garmin-workout-push ~/.claude/skills/

   # OU skill local à un projet
   mkdir -p .claude/skills
   cp -R skills/garmin-workout-push .claude/skills/
   ```

2. **Installer les dépendances Python** :

   ```bash
   pip install --upgrade "garminconnect[workout]" curl_cffi
   ```

3. Relancer Claude Code (ou démarrer une nouvelle session) pour que le skill soit
   détecté.

## Utilisation

Dans Claude Code, décris simplement ta séance et demande de l'envoyer sur Garmin :

> Envoie cette séance sur mon Garmin : échauffement 15min à 4:20/km, 5x1km à
> 3:38-3:42/km avec 1min30 de récup trot, retour au calme 3km

> Crée ma séance de demain sur Garmin Connect : footing 1h en endurance fondamentale,
> allure 4:15-4:30/km

Claude traduit la description en JSON (voir le schéma dans `SKILL.md` et dans le
docstring de `scripts/push_workout.py`), l'écrit dans un fichier temporaire, puis
exécute :

```bash
python3 scripts/push_workout.py workout.json
# ou, pour programmer directement la séance à une date donnée :
python3 scripts/push_workout.py workout.json --schedule 2026-08-20
```

### Authentification

Au premier lancement, le script demande interactivement ton email et mot de passe
Garmin Connect (et un code MFA si tu en as configuré un). Tu peux aussi définir les
variables d'environnement `GARMIN_EMAIL` et `GARMIN_PASSWORD` pour éviter la saisie
manuelle.

Les tokens de session sont ensuite mis en cache dans `~/.garminconnect` : les lancements
suivants n'auront normalement pas besoin de redemander les identifiants (sauf expiration
rare du token de rafraîchissement).

⚠️ Ne partage jamais ton mot de passe Garmin en clair dans une conversation avec Claude
— saisis-le uniquement dans le prompt interactif du terminal.

### Utilisation en ligne de commande (sans Claude)

Tu peux aussi appeler les scripts directement avec un JSON écrit à la main :

```json
{
  "name": "Footing endurance",
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

```bash
python3 scripts/push_workout.py workout.json --schedule 2026-08-20
```

Schéma complet (répétitions, cibles FC, récupération, étapes libres "open") documenté
dans `SKILL.md`.

## Points d'attention

- Ne modifie pas manuellement les allures/durées non précisées : le skill ne doit
  jamais inventer une valeur non fournie.
- Après un push réussi, évite de rouvrir/ré-enregistrer la séance dans l'éditeur web
  Garmin Connect avant de l'avoir vérifiée sur la montre : l'éditeur web peut mal
  afficher la cible d'allure ("Pas de cible" alors qu'elle est bien présente côté API),
  et une sauvegarde depuis cet état pourrait l'écraser pour de vrai.
- Ceci utilise une API non-officielle de Garmin Connect (bibliothèque `garminconnect`) :
  utilisation à tes risques, avec tes propres identifiants.

### Dépannage

- `AttributeError` sur `TargetType.SPEED` / `TargetType.HEART_RATE` (ou l'inverse,
  `TargetType.SPEED_ZONE` / `TargetType.HEART_RATE_ZONE`) : les noms des membres de
  l'enum `TargetType` de la librairie `garminconnect` ont changé selon les versions.
  Vérifie les noms réellement disponibles dans ton environnement avant de modifier
  `scripts/push_workout.py` :

  ```bash
  python3 -c "from garminconnect.workout import TargetType; print([x for x in dir(TargetType) if not x.startswith('_')])"
  ```

  La version de `scripts/push_workout.py` dans ce repo utilise `SPEED_ZONE` /
  `HEART_RATE_ZONE`, validée avec succès sur le push réel documenté dans
  [`EXAMPLE.md`](./EXAMPLE.md).

## Fichiers

| Fichier                     | Rôle                                                              |
|------------------------------|--------------------------------------------------------------------|
| `SKILL.md`                  | Définition du skill (déclencheurs, règles de conversion, exemples) |
| `scripts/push_workout.py`   | Envoie la séance directement sur Garmin Connect via l'API          |
| `scripts/generate_tcx.py`   | Génère un `.tcx` téléchargeable (alternative hors-ligne)           |
| `EXAMPLE.md`                 | Exemple réel : prompt, JSON généré, résultat sur Garmin Connect    |
