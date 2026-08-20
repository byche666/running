# Ameliorations envisagees

Liste des pistes d'evolution pour ce projet.

## Ajout de plusieurs entrainements d'un coup

Permettre de decrire un bloc de plusieurs seances (ex: un plan de la semaine
ou du mois) en une seule fois, plutot qu'une seance a la fois. A voir :

- format d'entree pour plusieurs seances (une liste de JSON, un fichier par
  seance, ou un seul fichier avec plusieurs entrees nommees)
- creation en boucle via l'API Garmin plutot qu'un seul appel
- gestion des erreurs partielles (certaines seances passent, d'autres non)
- programmation optionnelle de chaque seance a une date donnee
  (`--schedule`) pour construire un calendrier d'entrainement complet

## Adaptation au velo

Le skill `garmin-workout-push` ne gere aujourd'hui que le sport Running.
Etendre le support au velo impliquerait :

- utiliser `CyclingWorkout` (deja present dans la librairie `garminconnect`)
  au lieu de `RunningWorkout`
- adapter les cibles d'allure (min/km) en cibles de vitesse (km/h) et/ou
  de puissance (watts, zones de puissance)
- revoir le vocabulaire des blocs (echauffement, bloc principal, recuperation
  restent valables, mais les unites de duree/distance/cible changent)
- generaliser le script pour choisir le sport en parametre plutot que de le
  coder en dur

## Creation d'une interface pour ameliorer l'ergonomie du skill

Aujourd'hui l'utilisation passe par la conversation avec Claude et l'execution
de scripts en ligne de commande (JSON manuel, `python3 push_workout.py ...`).
Une interface reduirait la friction et les erreurs de saisie. Pistes :

- une page web simple (formulaire) pour construire une seance visuellement
  (blocs, allures, repetitions) sans ecrire de JSON a la main
- un apercu de la seance avant envoi (recapitulatif duree/distance/allures,
  eventuellement un graphique du profil d'allure)
- une liste des seances deja envoyees/programmees, avec possibilite de les
  modifier ou de les supprimer directement depuis l'interface
- gestion des identifiants Garmin (email/mot de passe/MFA) via un formulaire
  plutot qu'un prompt terminal ou des variables d'environnement
