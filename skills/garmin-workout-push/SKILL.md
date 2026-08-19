---
name: garmin-workout-push
description: >
  Cree une seance de course a pied structuree et l'envoie DIRECTEMENT sur le
  compte Garmin Connect de l'utilisateur via l'API (script push_workout.py),
  disponible immediatement dans la bibliotheque d'entrainements et
  synchronisable sur la montre. Utilise ce skill des que l'utilisateur
  decrit une seance de course a pied (fractionne, allure specifique,
  endurance, echauffement / bloc principal / retour au calme, "5x1km", zones
  d'allure ou de FC) et veut la creer sur Garmin, meme sans dire "API",
  "script" ou "push" — ex: "envoie cette seance sur mon Garmin", "cree ma
  seance de demain sur Garmin Connect". Necessite un acces reseau et Python
  (Claude Code, terminal local) -- ne fonctionne pas en environnement
  sandboxe sans internet. Peut aussi generer un .tcx telechargeable en
  alternative (moins pratique : non importable comme seance future sur
  Garmin Connect).
---

# Garmin Workout Push

Cree des seances de course a pied structurees et les envoie **directement dans
le compte Garmin Connect** de l'utilisateur via l'API non-officielle
`garminconnect` (methode validee et testee en conditions reelles). C'est la
methode preferee : contrairement a un import de fichier TCX/FIT (non supporte
par l'interface web de Garmin Connect pour les seances futures), le push API
cree la seance directement dans la bibliotheque d'entrainements, prete a etre
envoyee sur la montre.

Seul le sport **Running** est gere par ce skill.

**Prerequis obligatoire** : un environnement avec acces reseau sortant et
Python (Claude Code en local, terminal). Ne fonctionne pas dans un
environnement sandboxe sans acces internet (ex: claude.ai sans acces reseau).
Si l'environnement actuel n'a pas d'acces reseau, prevenir l'utilisateur et,
si pertinent, proposer de generer un fichier `.tcx` a la place via
`scripts/generate_tcx.py` (voir section "Alternative sans acces reseau").

## Workflow (methode principale : push API)

1. **Verifier les dependances** : s'assurer que la librairie est installee.
   ```bash
   pip install --upgrade "garminconnect[workout]" curl_cffi
   ```

2. **Comprendre la seance** decrite en langage naturel et la traduire en JSON
   selon le schema ci-dessous (identique pour TCX et push API, pour rester
   coherent).

3. **Ecrire ce JSON dans un fichier temporaire** (ex: `/tmp/workout.json` ou
   `workout.json` dans le repertoire de travail).

4. **Executer le script de push** :
   ```bash
   python3 scripts/push_workout.py workout.json
   ```
   Optionnellement, ajouter `--schedule YYYY-MM-DD` pour programmer la seance
   a une date precise directement.

   Au premier lancement, le script demande l'email et le mot de passe Garmin
   Connect (et un code MFA si configure) de maniere interactive, sauf si les
   variables d'environnement `GARMIN_EMAIL` et `GARMIN_PASSWORD` sont deja
   definies. Les tokens de session sont ensuite mis en cache dans
   `~/.garminconnect` : les lancements suivants n'auront normalement pas
   besoin de redemander les identifiants (sauf expiration du token de
   rafraichissement, rare).

5. **Confirmer a l'utilisateur** : le script affiche un lien direct vers la
   seance sur Garmin Connect (`https://connect.garmin.com/modern/workout/<id>`).
   Partager ce lien et resumer en une ou deux phrases la structure de la
   seance envoyee (temps/distances, allures cibles) pour verification rapide.

## Regles de conversion (langage naturel -> JSON)

Voir le schema complet et des exemples dans `scripts/push_workout.py`
(docstring en tete de fichier). Rappel des points cles :

- **Echauffement / retour au calme** : `intensity: "Warmup"` / `"Cooldown"`.
  Duree en temps (`{"type": "time", "seconds": ...}`) ou distance
  (`{"type": "distance", "meters": ...}`) selon ce que l'utilisateur donne.

- **Repetitions** ("5x1km", "10 fois 400m") -> noeud `{"type": "repeat",
  "repetitions": N, "children": [...]}`.

- **Allures** en "mm:ss/km" -> `{"type": "pace", "low": "...", "high": "..."}`.
  L'ordre low/high n'importe pas (trie automatiquement). Si une seule allure
  est donnee sans fourchette, creer une petite fourchette symetrique de +/-3
  a 5 secondes/km, et le signaler dans le resume final a l'utilisateur.

- **Frequence cardiaque** -> `{"type": "hr", "low": bpm, "high": bpm}`.

- **Recuperation** ("2min recup", "recup trot") -> `intensity: "Resting"`,
  duree en temps le plus souvent. Si l'allure de recup n'est pas precisee,
  utiliser une fourchette large/lente par defaut (ex: 6:00-7:00/km) et le
  signaler.

- **Pas de cible donnee** pour un bloc -> `{"type": "none"}`. Ne jamais
  inventer une allure precise non mentionnee par l'utilisateur.

- **Duree/distance non fixee** ("cours jusqu'a ce que tu sois pret") ->
  `{"type": "open"}` (etape validee manuellement sur la montre).

## Exemple complet

Entree utilisateur :
> "Echauffement 15min a 4:20, 5x1km a 3:38-3:42/km avec 1min30 recup trot,
> retour au calme 3km"

```json
{
  "name": "Seance allure specifique",
  "steps": [
    {"type": "step", "name": "Echauffement", "intensity": "Warmup",
     "duration": {"type": "time", "seconds": 900},
     "target": {"type": "pace", "low": "4:25", "high": "4:15"}},
    {"type": "repeat", "repetitions": 5, "children": [
      {"type": "step", "name": "1 km allure specifique", "intensity": "Active",
       "duration": {"type": "distance", "meters": 1000},
       "target": {"type": "pace", "low": "3:42", "high": "3:38"}},
      {"type": "step", "name": "Recuperation trot", "intensity": "Resting",
       "duration": {"type": "time", "seconds": 90},
       "target": {"type": "pace", "low": "7:00", "high": "6:00"}}
    ]},
    {"type": "step", "name": "Retour au calme", "intensity": "Cooldown",
     "duration": {"type": "distance", "meters": 3000},
     "target": {"type": "pace", "low": "5:30", "high": "5:00"}}
  ]
}
```

## Alternative sans acces reseau

Si l'environnement d'execution n'a pas d'acces internet (impossible
d'installer des paquets ou d'appeler l'API Garmin), utiliser
`scripts/generate_tcx.py` a la place pour produire un fichier `.tcx`
telechargeable. Prevenir clairement l'utilisateur que ce fichier ne pourra
**pas** etre importe comme seance future via l'interface web de Garmin
Connect (l'import de fichiers y est reserve aux activites deja enregistrees
et aux parcours) ; seule une copie manuelle en `.FIT` sur la montre par USB,
ou une saisie manuelle dans le createur de seances Garmin Connect,
fonctionnent avec un simple fichier.

## Points d'attention

- Ne jamais inventer de valeurs (allure, distance, duree, FC) non fournies ou
  deductibles du contexte : demander une clarification plutot que deviner.
- Apres un push reussi, ne pas rouvrir/re-sauvegarder la seance dans
  l'editeur web Garmin Connect avant verification sur la montre : l'editeur
  web peut mal afficher/interpreter la cible d'allure ("Pas de cible" alors
  que les valeurs sont bien presentes) et une sauvegarde depuis cet etat
  pourrait ecraser la cible reelle. Les donnees stockees via l'API sont
  fiables ; c'est uniquement l'affichage de l'editeur web qui peut induire en
  erreur.
- Si `client.login()` echoue de maniere repetee (MFA, mot de passe expire,
  compte verrouille), ne jamais demander explicitement le mot de passe en
  clair dans la conversation : l'utilisateur doit le saisir lui-meme dans le
  prompt interactif du terminal.
