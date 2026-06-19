# Architecture

> Vue technique de la plateforme de facturation électronique Chorus Pro / PISTE.
> *Technical overview of the Chorus Pro / PISTE e-invoicing platform.*

## Vue d'ensemble

L'application est une **SPA React** servie par nginx, adossée à une **API FastAPI** qui orchestre l'authentification, l'extraction PDF, la communication avec Chorus Pro et l'accès à PostgreSQL.

```text
┌─────────────────────────────────────────────────────────────┐
│  Navigateur — React SPA (TypeScript, Vite, shadcn/ui)         │
│  • formulaires (React Hook Form + Zod)                        │
│  • data fetching/cache (TanStack Query)                       │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTPS  (jamais de secret Chorus côté client)
        ┌───────▼────────┐
        │     nginx      │  reverse proxy + assets statiques
        └───────┬────────┘
                │ /api/*
        ┌───────▼─────────────────────────────────────────────┐
        │  FastAPI (Python 3.12)                                │
        │  ┌───────────────┐  ┌────────────────┐               │
        │  │ Auth JWT       │  │ Extraction PDF │               │
        │  └───────────────┘  └────────────────┘               │
        │  ┌──────────────────────────────────────────────┐    │
        │  │ RoutingService → InvoiceProvider              │    │
        │  │   • ChorusProProvider  → PISTE OAuth2 + UBL    │────┼──► Chorus Pro / PISTE
        │  │   • FuturePDPProvider  (B2B, à venir)          │    │
        │  │   • MockProvider       (tests)                 │    │
        │  └──────────────────────────────────────────────┘    │
        │  ┌───────────────┐                                    │
        │  │ API DB /api/db │ ──► PostgreSQL                     │
        │  └───────────────┘                                    │
        └───────────────────────────────────────────────────────┘

Conteneurs : nginx · api (FastAPI) · migrate (Alembic) · postgres
```

## Principe de sécurité fondamental

Le navigateur **ne détient et n'envoie jamais** les secrets Chorus/PISTE. Le flux d'authentification OAuth2 vers PISTE s'exécute **entièrement côté serveur** : le frontend déclenche une action, le backend récupère un token OAuth2 avec les identifiants techniques (stockés hors du dépôt, en variables d'environnement), puis appelle Chorus Pro. Les variables exposées au bundle (`VITE_*`) ne contiennent jamais de secret.

## Le *provider pattern*

Le cœur extensible du backend est l'abstraction du **canal de soumission** d'une facture.

- `InvoiceProvider` (un `Protocol` Python) définit le contrat : `validate_payload`, `submit_invoice`, `get_status`, `cancel_invoice`.
- `ChorusProProvider` implémente ce contrat pour le secteur public (Chorus Pro via PISTE).
- `FuturePDPProvider` est un emplacement réservé pour les futures **Plateformes de Dématérialisation Partenaires** (facturation B2B privée).
- `MockProvider` permet de tester la chaîne sans appel réseau.
- `RoutingService` sélectionne le bon fournisseur selon le **canal** de la facture (`PUBLIC_SECTOR`, `B2B_PRIVATE`, …) ou un fournisseur explicite.

Conséquence : ajouter un nouveau canal de facturation = écrire une classe qui respecte le `Protocol`, sans toucher au reste de l'application.

## Pipeline de traitement d'une facture

1. **Réception / préparation** — la facture est synchronisée depuis Chorus ou préparée à partir d'un PDF (extraction texte + champs).
2. **Normalisation** — nettoyage des SIRET, destinataires, services, montants (`Decimal`), TVA.
3. **Validation** — Zod côté frontend, puis validation métier côté backend (`validation_service`, `validate_payload`).
4. **Construction du payload** — assemblage du payload Chorus puis génération du **flux UBL** (`chorus_ubl_generator`).
5. **Soumission** — upload du PDF puis dépôt via les API Chorus Pro (authentification OAuth2 côté serveur).
6. **Suivi** — la réponse Chorus est mappée vers un **statut interne** stable (`statuses.py`) et affichée à l'utilisateur ; les rejets sont analysés et expliqués.

## Modèle de statuts

Chorus Pro expose des statuts hétérogènes selon les endpoints. Le module `statuses.py` définit un jeu de **statuts internes** (`InvoicePilotStatus`) et une fonction de mapping `chorus_status_to_invoicepilot(...)` qui isole l'application des variations externes — l'UI et les règles métier ne dépendent que du modèle interne.

## Gestion des erreurs

Les exceptions techniques (`ChorusApiError`, erreurs OAuth, validation) sont :
1. capturées au niveau du provider,
2. enrichies (`ProviderError` : message utilisateur + détails techniques + trace des appels API),
3. traduites en **messages métier actionnables** (`errors.py`) — par exemple, une erreur sur `codeDestinataire` devient *« Le destinataire public n'est pas correctement identifié. Vérifiez le SIRET ou le service exécutant. »*

## Données & persistance

PostgreSQL stocke les référentiels (annuaire des structures publiques), les factures, les jobs de synchronisation et l'audit des appels. Les migrations sont gérées par **Alembic** et appliquées au démarrage par un conteneur dédié. Une synchronisation périodique (cron) maintient les référentiels à jour.

## Stack de déploiement

`docker-compose` orchestre quatre services : **nginx** (proxy + assets), **api** (FastAPI), **migrate** (Alembic au démarrage) et **postgres** (avec volume persistant). nginx termine le trafic et proxifie `/api/*` vers FastAPI, ce qui garantit que le frontend et l'API partagent la même origine et que les secrets restent côté serveur.
