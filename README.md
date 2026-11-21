# DS1 — Sujet 13 : Architecture hexagonale (Ports & Adapters) et Clean Architecture avec Django

Prototype d'un système de **demande de prêt** dont les règles métier vivent dans un cœur Python pur,
indépendant de Django. Django, la base de données et le service de scoring sont des **adaptateurs**
qui se branchent sur des **ports** définis par le cœur.

> Groupe G8 — BIS2 — ISG Tunis — cours SOA, prof. Chaouki Bayoudhi.

## Ce que démontre le projet

| Objectif | Preuve dans le dépôt |
|---|---|
| Le métier ne dépend d'aucun framework | `lint-imports` : le contrat *Core must not depend on Django* est respecté |
| Les dépendances pointent vers l'intérieur | contrat *Layered architecture* (`loans` → `loan_adapters` → `application` → `domain`) |
| Des tests rapides, sans base de données ni Django | `tests/core/` : 83 tests ; `python scripts/check_core_speed.py` exige 50+ tests en moins de 0,2 s et vérifie que `django` n'est jamais importé |
| Les adaptateurs sont interchangeables | `tests/adapters/test_repository_contract.py` et `tests/scenarios/` : mêmes tests contre mémoire **et** Django ORM |
| Une même logique, plusieurs « portes d'entrée » | pages HTML (`loans/views.py`), API JSON (`loans/api.py`) **et** commande CLI (`evaluate_loan`) appellent le même cas d'usage |
| Un assistant IA encadré par des règles déterministes | `GenerateCreditMemo` : le mémo proposé est validé par `validate_memo` ; sinon repli sur un gabarit (assistant **simulé**, aucun vrai LLM) |
| Dégradation maîtrisée d'un service externe | panne du scoring → `À examiner`, jamais d'acceptation automatique |

## Architecture

```
loan_core/                  CŒUR : Python pur, aucun import django
  domain/                   entités, objets-valeurs, règles, validation du mémo (models, rules, memo, errors)
  application/              ports (Protocol : dépôt, scoring, mémo, horloge), cas d'usage, erreurs
loan_adapters/              adaptateurs purs : mémoire, scoring simulé, rédacteur de mémo simulé, horloge
loans/                      app Django : modèle ORM, dépôt Django, vues HTML, API JSON,
                            commande CLI, composition root (composition.py)
config/                     réglages et URLs Django
tests/                      core/ · adapters/ · scenarios/ · web/ · architecture/
scripts/                    benchmark.py · demo_violation.py · check_core_speed.py
docs/                       ARCHITECTURE.md (schémas Mermaid + questions d'oral) · screenshots/
.importlinter               contrats d'architecture
```

Détails, schémas et questions d'oral : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Règles métier implémentées

Mensualité à annuités constantes (taux annuel fixe de 9 %, paramétrable dans `LoanPolicy`).

| Condition | Décision |
|---|---|
| Mensualité > 40 % du revenu, **ou** score < 500 | Refusé |
| Score entre 500 et 649, **ou** endettement entre 33 % et 40 %, **ou** score indisponible | À examiner |
| Sinon | Accepté |

Bornes de validation : montant ≤ 500 000 TND, durée de 6 à 84 mois, revenu > 0.

> **Le score de crédit est simulé** (`SimulatedCreditBureau` : hash déterministe de la référence client).
> Aucune vraie centrale de crédit n'est appelée. Les références clients et les noms de démonstration sont fictifs.

## Prérequis

- Windows, Python 3.12 ou 3.13 (testé avec Python 3.13 sous Linux) — Django 5.2 LTS.
- Aucune base de données à installer : SQLite est intégrée.
- Docker Desktop (optionnel) : voir la section « Avec Docker ».

## Installation (Windows, invite de commandes)

```bat
cd ds1-hexagonal-django
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Puis ouvrir <http://127.0.0.1:8000/>. En PowerShell, activer l'environnement avec `.venv\Scripts\Activate.ps1`
(si l'exécution de scripts est bloquée : `Set-ExecutionPolicy -Scope Process RemoteSigned`).

`seed_demo` insère 6 demandes d'exemple (acceptées, refusées, à examiner) via le cas d'usage.

## Avec Docker (optionnel)

Utile si Python ne s'installe pas ou si Windows bloque des bibliothèques. Docker Desktop doit être démarré.

```bat
docker-check.bat                                   :: toutes les vérifications dans Docker
docker compose up --build                          :: lance le site sur http://localhost:8000/
docker compose run --rm web python manage.py seed_demo   :: 6 demandes d'exemple (une seule fois)
docker compose down                                :: arrêt (la base est conservée dans un volume)
```

La vérification de vitesse du cœur exige 0,2 s par défaut (valeur de la fiche du sujet). Sur un PC plus lent, on peut assouplir la limite avec une variable, sans modifier le code :

```bat
set CORE_MAX_SECONDS=0.5     :: invite de commandes (cmd)
docker-check.bat
```

Sous PowerShell : `$env:CORE_MAX_SECONDS="0.5"`, puis `docker-check.bat`. Les durées dépendent de la machine : voir `docs/RESULTATS.md`.

## Vérifications

```bat
lint-imports            :: contrats d'architecture (3 attendus : KEPT)
pytest                  :: 152 tests (comptage au moment de la rédaction)
python scripts\check_core_speed.py   :: cœur : 50+ tests, < 0,2 s, sans Django
check.bat               :: tout ce qui précède, plus python manage.py check
```

Sous Linux/macOS : `source .venv/bin/activate`, puis les mêmes commandes.

### Démonstrations pour l'oral

```bat
python scripts\demo_violation.py   :: ajoute "import django" au domaine -> import-linter échoue, puis nettoie
python scripts\benchmark.py 500    :: même cœur, adaptateur mémoire contre Django ORM
pytest tests\core -p no:django    :: tests métier, sans base de données et sans charger Django
python manage.py evaluate_loan --name Test --reference CLI-5 --amount 20000 --months 60 --income 2000   :: 3e porte d'entrée (CLI)
```

Le benchmark mesure le cas d'usage seul **et** la suite de scénarios (`-k fake_repo` contre `-k orm_repo`). Les temps dépendent de votre machine : **relancez-le et citez vos propres mesures**. Dans la CI GitHub, la limite de 0,2 s est assouplie à 0,5 s (runners partagés) ; en local elle reste 0,2 s.

## API JSON

| Méthode | URL | Rôle | Codes |
|---|---|---|---|
| POST | `/api/applications/` | Évaluer et enregistrer une demande | 201, 400 |
| GET | `/api/applications/` | Lister les demandes récentes | 200 |
| GET | `/api/applications/<id>/` | Détail d'une demande | 200, 404 |

```bat
curl -X POST http://127.0.0.1:8000/api/applications/ -H "Content-Type: application/json" ^
  -d "{\"applicant_name\":\"Test API\",\"applicant_reference\":\"CLI-9\",\"amount\":15000,\"duration_months\":36,\"monthly_income\":2500}"
```

L'endpoint POST est exempté de CSRF car c'est une API de démonstration sans authentification ; une API réelle
utiliserait un jeton (JWT, par exemple).

## Configuration

| Variable d'environnement | Rôle | Défaut |
|---|---|---|
| `LOANS_CREDIT_SCORE_PROVIDER` | `simulated`, `unavailable` (panne simulée) ou `fixed:700` | `simulated` |
| `LOANS_MEMO_PROVIDER` | `rule_based`, `faulty` (hallucination simulée, écartée par la validation) ou `unavailable` | `rule_based` |
| `DJANGO_SECRET_KEY` | clé secrète (à définir hors développement) | clé de développement non sécurisée |
| `DJANGO_DEBUG` | `1` ou `0` | `1` |
| `DJANGO_ALLOWED_HOSTS` | hôtes autorisés, séparés par des virgules | `localhost,127.0.0.1,testserver` |
| `DJANGO_DB_NAME` | chemin du fichier SQLite | `db.sqlite3` |

Démo de la panne du scoring (cmd) : `set LOANS_CREDIT_SCORE_PROVIDER=unavailable`, puis relancer le serveur et soumettre une
demande : elle passe en « À examiner » avec le message « Score de crédit indisponible ».

## Captures d'écran

`docs/screenshots/` contient les captures de la démonstration (interface, API, `docker-check.bat`, `pytest`,
`lint-imports`, `demo_violation.py`, `benchmark.py`, scoring en panne, CI GitHub).
Les mesures et leurs conditions (machine, limite de vitesse utilisée) sont dans `docs/RESULTATS.md`.

## Limites connues

- Scoring **simulé** et assistant de mémo **simulé** (aucun vrai LLM) ; pas de vraie intégration bancaire.
- Le patron Unit-of-Work est présenté en théorie uniquement, non implémenté.
- Pas d'authentification ni de rôles : hors du périmètre du sujet.
- La mensualité utilise un taux fixe unique ; pas de barème par profil.
- Les messages de décision sont produits par le domaine en texte neutre (points décimaux), l'interface Django affiche les nombres au format français.
- L'architecture hexagonale ajoute des fichiers et de l'abstraction : surdimensionnée pour un simple CRUD, utile quand le métier est riche.

## Références

- Alistair Cockburn, *Hexagonal architecture* (2005) — <https://alistair.cockburn.us/hexagonal-architecture/>
- Robert C. Martin, *The Clean Architecture* (2012) — <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>
- Harry Percival & Bob Gregory, *Architecture Patterns with Python* (« Cosmic Python ») — <https://www.cosmicpython.com/>
- Documentation Django — <https://docs.djangoproject.com/en/5.2/>
- Documentation import-linter — <https://import-linter.readthedocs.io/>
- Documentation pytest-django — <https://pytest-django.readthedocs.io/>
- Python, `typing.Protocol` — <https://docs.python.org/3/library/typing.html#typing.Protocol>
