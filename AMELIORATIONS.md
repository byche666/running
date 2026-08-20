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
