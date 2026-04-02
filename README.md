
# 🎓 Plateforme KIMVIEware

Système de test automatisé utilisant l'exécution symbolique et les algorithmes génétiques pour microservices multi-langages.

## 🚀 Fonctionnalités
- **Phase 0 (Validator)** : Validation d'archives et détection de langage.
- **Phase 1 (Extractor)** : Extraction de trajectoires symboliques (Python, Java, C).
- **Phase 2 (SGATS)** : Réduction intelligente des cas de test par similarité.
- **Phase 3 (EvoPath)** : Optimisation génétique multi-objectifs.
- **Phase 4 (Executor)** : Génération de tests PyTest et Mutation Testing.

## 🔗 Tests d'Intégration Multi-Langages
KIMVIware permet de tester l'interopérabilité entre plusieurs services (Python, Java, C).

### Lancement Automatique
Pour lancer une suite complète de microservices et exécuter les tests d'intégration :
```bash
python3 run_complete_integration.py
```

### Récupération des Résultats
Après l'exécution, un rapport détaillé est généré ici :
- `integration_report.json` : Statut structuré de l'interopérabilité.
- `KIMVIWARE_TEST_REPORT.json` : Résultats globaux du pipeline.

## 🛠️ Installation
1. Activez l'environnement virtuel : `source venv_kimvieware/bin/activate`
2. Installez les dépendances : `pip install -r requirements.txt`
3. Assurez-vous que Docker est installé pour les tests d'intégration.

---
*Projet de thèse - NDEMAFO*
# kimviware
# kimviware
