# Exercice — Cache Redis pour les tâches (fastapi-redis-cache)

## Objectif
Mettre en place un cache Redis pour les endpoints de récupération des tâches afin d'améliorer les performances. Le cache doit être utilisé à la première récupération et être invalidé à chaque modification pertinente de la base de données.

## Contraintes
- Utiliser `fastapi-redis-cache` (ou une solution équivalente compatible FastAPI).
- Cibler au minimum les endpoints de lecture : `GET /tasks` et `GET /tasks/{id}`.
- Le cache doit être invalidé lors des opérations suivantes :
	- Création, modification ou suppression d'une `task`.
	- Modifications sur `employee` qui impactent les tâches (le cas échéant).
- TTL (durée de vie) du cache configurable (par défaut suggéré : 300 secondes).

## Tâches à réaliser
1. Installer et configurer Redis et `fastapi-redis-cache` dans l'application.
2. Initialiser la connexion Redis au démarrage de l'app.
3. Ajouter la mise en cache pour `GET /tasks` et `GET /tasks/{id}`.
4. Implémenter l'invalidation du cache sur les routes `POST`, `PUT`, `DELETE` liées à `task` et sur les changements d'`employee` pertinents.
5. Ajouter des tests ou un script de vérification pour montrer que :
	 - Après la première requête, les suivantes sont servies depuis le cache.
	 - Après une modification, le cache est invalidé et les données retournées sont à jour.

## Critères d'acceptation
- Les endpoints de lecture utilisent le cache après la première requête.
- Après création/modification/suppression, une nouvelle requête retourne l'état à jour (le cache a été invalidé).
- Le TTL est pris en compte et configurable.

## Indications d'implémentation (suggestions)
- Initialiser la connexion Redis dans le startup de FastAPI.
- Pour `GET /tasks`, utiliser un décorateur ou wrapper de cache (selon la lib) et stocker la clé par endpoint + paramètres de filtre/pagination.
- Lors des mutations (`POST/PUT/DELETE`), appeler l'invalidation/effacement des clés concernées (pattern par collection ou clés explicites).
- Documenter la configuration (URL Redis, TTL) dans les variables d'environnement.

## Vérification manuelle rapide
1. Démarrer Redis et l'application.
2. Appeler `GET /tasks` → réponse initiale générée depuis la base.
3. Appeler `GET /tasks` à nouveau → réponse servie depuis le cache (latence réduite).
4. Créer/modifier/supprimer une tâche.
5. Appeler `GET /tasks` → nouvelle réponse reflétant la modification.
