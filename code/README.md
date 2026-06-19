# Code — extrait curé / curated extract

Ces fichiers sont un **extrait représentatif** du projet, choisi pour illustrer l'architecture et la qualité du code. Ce n'est **pas** l'application complète ni un projet exécutable en l'état : les imports vers des modules non inclus (clients HTTP, configuration, accès DB) sont volontairement absents pour ne pas exposer de logique propriétaire ou de configuration.

*These files are a representative extract, selected to illustrate architecture and code quality. This is not the full, runnable application — imports of modules left out (HTTP clients, config, DB access) are intentionally absent so no proprietary logic or configuration is exposed.*

## À lire en priorité / Start here

| Fichier | Ce qu'il montre |
| --- | --- |
| [`backend/providers/base.py`](backend/providers/base.py) | Le contrat `InvoiceProvider` (Protocol) et les types de domaine — le cœur du *provider pattern*. |
| [`backend/providers/chorus_pro.py`](backend/providers/chorus_pro.py) | Implémentation Chorus Pro : validation, soumission, mapping de réponse, gestion d'erreur. |
| [`backend/invoicepilot/routing_service.py`](backend/invoicepilot/routing_service.py) | Sélection du fournisseur selon le canal de facturation. |
| [`backend/invoicepilot/statuses.py`](backend/invoicepilot/statuses.py) | Modèle de statuts interne + mapping depuis les statuts Chorus. |
| [`backend/chorus_ubl_generator.py`](backend/chorus_ubl_generator.py) | Génération du flux XML/UBL conforme. |
| [`backend/errors.py`](backend/errors.py) | Traduction des erreurs techniques en messages métier actionnables. |
| [`frontend/lib/chorus/buildSubmissionPayload.ts`](frontend/lib/chorus/buildSubmissionPayload.ts) | Construction typée du payload de soumission côté frontend. |
| [`frontend/types/chorus.ts`](frontend/types/chorus.ts) | Modèle de types TypeScript du domaine Chorus. |
| [`frontend/components/flux/`](frontend/components/flux/) | Composants UI du pipeline de facturation. |
