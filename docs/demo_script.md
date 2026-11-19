# Scénario de démo — DS1 G8, sujet 13 (architecture hexagonale avec Django)

Toutes les commandes se lancent dans `cmd`, dans le dossier du projet (celui qui contient `manage.py`), Docker Desktop démarré.

Légende : **Testé** = lancé et vu fonctionner sur le PC de Zakaria. **À tester** = pas encore lancé tel quel : à faire une fois avant la démo.

## Préparation (avant de commencer)

| Action | Commande | Statut |
|---|---|---|
| Arrêter une ancienne instance | `docker compose down` | Testé |
| Lancer le site | `docker compose up --build` | Testé |
| Charger 6 demandes d'exemple (une seule fois, puis dans un 2e terminal) | `docker compose run --rm web python manage.py seed_demo` | Testé |

Ne relancez pas `seed_demo` : il crée des doublons. La base est conservée dans un volume Docker ; `docker compose down -v` la supprime (dans ce cas, relancer `seed_demo`).

Ouvrir http://localhost:8000/

## Scénario

| # | Ce que je montre | Action | Ce qu'on doit voir | Statut |
|---|---|---|---|---|
| 1 | L'application | Page d'accueil, puis « Historique » | Les 6 demandes d'exemple | Testé |
| 2 | Demande acceptée | Référence `CLI-1001`, 20000 TND, 60 mois, revenu 2000 | « Accepté », score 772, mensualité 415,167 TND, endettement 20,8 %, mémo validé | Testé |
| 3 | Demande refusée | Référence `CLI-1005`, 15000, 36 mois, revenu 900 | « Refusé », endettement 53,0 % (maximum 40 %) | Testé |
| 4 | Demande à examiner | Référence `CLI-9`, 15000, 36 mois, revenu 2500 | « À examiner », score 576 inférieur à 650 | Testé |
| 5 | Même cas d'usage par l'API | Voir la commande ci-dessous (serveur en marche) | Réponse JSON, `HTTP/1.1 201 Created` (utiliser `curl -i`) | Testé |
| 6 | Même cas d'usage par la CLI | Voir la commande ci-dessous | Accepté attendu (mêmes données que l'étape 2) ; 3e porte d'entrée | Commande testée avec `CLI-5` (refusé, score 312) ; à retester avec `CLI-1001` |
| 7 | Panne du scoring | Voir ci-dessous | `CLI-1001` passe « À examiner », score « indisponible » | Testé |
| 8 | Assistant IA fautif | Voir ci-dessous | Brouillon écarté, mémo de référence, problèmes détectés | Testé |
| 9 | Violation d'architecture | `docker compose run --rm web python scripts/demo_violation.py` | Contrat « Core must not depend on Django » BROKEN, puis tout redevient KEPT | Testé |
| 10 | Benchmark | `docker compose run --rm web python scripts/benchmark.py 500` | Mémoire 6,7 ms contre ORM 297,6 ms (x44,2) ; scénarios 0,15 s contre 0,26 s (x1,7) | Testé |
| 11 | Toutes les vérifications | `docker-check.bat` | 3 contrats respectés, 152 tests, cœur 0,1 s sans Django | Testé |
| 12 | Modification en direct | Voir ci-dessous | Un test du cœur casse et dit pourquoi | Testé |

Les chiffres des lignes 9 à 11 sont des mesures du PC de Zakaria, dans Docker ; ils dépendent de la machine.

## Commandes des lignes 5 à 8 et 12

**5. API** (le site tourne sur le port 8000 ; autre `cmd`). Résultat observé : `201 Created`, décision `MANUAL_REVIEW`, score 576.

```bat
curl -i -X POST http://localhost:8000/api/applications/ -H "Content-Type: application/json" ^
  -d "{\"applicant_name\":\"Test API\",\"applicant_reference\":\"CLI-9\",\"amount\":15000,\"duration_months\":36,\"monthly_income\":2500}"
```

**6. CLI** (testé avec `CLI-5` : « REJECTED », score 312 inférieur au minimum 500 ; avec `CLI-1001` on attend « APPROVED », à vérifier) :

```bat
docker compose run --rm web python manage.py evaluate_loan --name Test --reference CLI-1001 --amount 20000 --months 60 --income 2000
```

**7. Panne du scoring** (arrêter le site avec Ctrl+C, puis) :

```bat
docker compose run --rm --service-ports -e LOANS_CREDIT_SCORE_PROVIDER=unavailable web
```

Formulaire : `CLI-1001`, 20000, 60, 2000. Arrêter avec Ctrl+C.

**8. Assistant fautif** :

```bat
docker compose run --rm --service-ports -e LOANS_MEMO_PROVIDER=faulty web
```

Formulaire : `CLI-1001`, 20000, 60, 2000. Arrêter avec Ctrl+C.

**12. Modification en direct** : dans `loan_core\domain\rules.py`, remplacer `approval_score: int = 650` par `approval_score: int = 700`, puis lancer les tests du cœur en montant le dossier dans le conteneur (sinon le conteneur utilise l'ancienne copie du code) :

```bat
docker compose run --rm -v "%cd%":/app web python -m pytest tests/core -p no:django -q
```

Résultat observé dans Docker : un seul test échoue, `tests/core/test_rules_boundaries.py::test_score_boundaries[650-APPROVED]`, car un score de 650 passe « À examiner » avec le nouveau seuil. Remettre ensuite 650.

## Ce qu'il faut dire à chaque étape (une phrase)

1. Le cœur métier ne connaît pas Django ; Django se branche dessus.
2. Les règles sont dans le domaine : ici, tout va bien, la demande est acceptée.
3. Même cœur, autre décision : refus, avec les raisons.
4. Le score est simulé ; un score moyen donne un examen manuel.
5 et 6. Trois portes d'entrée (web, API, CLI), un seul cas d'usage.
7. Une panne du scoring ne produit jamais une acceptation automatique.
8. L'assistant IA est simulé et encadré : son brouillon est vérifié par des règles du domaine.
9. L'architecture est protégée par import-linter : le cœur ne peut pas importer Django.
10. Mêmes règles, deux adaptateurs (mémoire et Django ORM) : le cœur ne change pas.
12. Un test du cœur détecte tout de suite un changement de règle, sans base de données.

## En cas de problème

- Port 8000 occupé : `docker compose down`, puis relancer.
- Docker indisponible : montrer la vidéo de secours `video_secours.mp4`.
