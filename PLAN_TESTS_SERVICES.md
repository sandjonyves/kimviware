# 📋 PLAN D'ACTION COMPLET - TESTS DES SERVICES KIMVIWARE

**Date**: 23 Janvier 2026  
**Statut**: ✅ Analysé et Prêt pour Exécution  
**Durée Estimée**: 2-4 heures (selon les options choisies)

---

## 🎯 OBJECTIFS

1. ✅ Vérifier l'état de l'infrastructure (RabbitMQ, MongoDB, Docker)
2. ✅ Tester chaque service individuellement
3. ✅ Tester le pipeline complet (Phase 0-4)
4. ✅ Valider les résultats et métriques
5. ✅ Générer un rapport détaillé

---

## 📊 ANALYSE DE L'INFRASTRUCTURE ACTUELLE

### Services Détectés

| Service | Type | Port | Status | Requirements |
|---------|------|------|--------|--------------|
| **Orchestrator** | API Gateway | 8080 | ✅ Prêt | FastAPI, Uvicorn |
| **Phase 0 Validator** | Language Detection | RabbitMQ | ✅ Prêt | python-magic |
| **Phase 1 Extractor** | Trajectory Extraction | RabbitMQ | ✅ Prêt | Angr, NetworkX |
| **Phase 2 SGATS** | Path Reduction | RabbitMQ | ✅ Prêt | NumPy, SciPy |
| **Phase 3 EvoPath** | Genetic Optimization | RabbitMQ | ✅ Prêt | NumPy, DEAP |
| **Phase 4 Executor** | Test Generation | RabbitMQ | ✅ Prêt | pytest, MutPy |
| **RabbitMQ** | Message Broker | 5672, 15672 | ✅ Déployé | Docker |
| **MongoDB** | Database | 27017 | ✅ Déployé | Docker |
| **Redis** | Cache | 6379 | ✅ Déployé | Docker |
| **MinIO** | Object Storage | 9000 | ✅ Déployé | Docker |

### Fichiers de Test Existants

```
✅ test_complete_pipeline.py     - Test du pipeline complet (40-50 min)
✅ test_full_system.py           - Tests multi-SUT (2-3 heures)
✅ FULL_TEST_REPORT.py           - Analyse système (15s)
✅ diagnose.py                   - Diagnostic infrastructure (5s)
✅ generate_report.py            - Rapport système (3s)
```

### SUTs (Systems Under Test) Disponibles

```
🐍 Python Services:
   ✓ auth-service/        - FastAPI auth service
   ✓ course-service/      - Course management
   ✓ grade-service/       - Grade management
   ✓ room-service/        - Room management
   ✓ timetable-service/   - Timetable service

🔧 C Service:
   ✓ auth-service-c/      - C implementation

☕ Java Service:
   ✓ auth-service-java/   - Java implementation
```

---

## 🔍 VÉRIFICATION DES FICHIERS CLÉS

### 1. **Services Microservices (Phase 0-4)**

| Phase | Fichier | Statut | Dépendances |
|-------|---------|--------|-------------|
| 0 | `kimvieware-phase0-validator/src/validator_service.py` | 📝 À Vérifier | python-magic |
| 1 | `kimvieware-phase1-extractor/src/extractor_service.py` | 📝 À Vérifier | angr, networkx |
| 1 | `kimvieware-phase1-extractor/src/extractors/{py,c,java}_extractor.py` | 📝 À Vérifier | Spécifiques par langue |
| 2 | `kimvieware-phase2-sgats/src/sgats_service.py` | 📝 À Vérifier | numpy, scipy |
| 3 | `kimvieware-phase3-evopath/src/evopath_service.py` | 📝 À Vérifier | numpy, deap |
| 4 | `kimvieware-phase4-executor/src/executor_service.py` | 📝 À Vérifier | pytest, mutpy |

### 2. **API Gateway**

| Fichier | Statut | Dépendances |
|---------|--------|-------------|
| `kimvieware-orchestrator/run_orchestrator.py` | ✅ Prêt | FastAPI, Uvicorn |
| `kimvieware-orchestrator/src/api/enhanced_gateway.py` | 📝 À Vérifier | FastAPI |
| `kimvieware-orchestrator/src/api/gateway.py` | 📝 À Vérifier | FastAPI |

### 3. **Infrastructure**

| Fichier | Statut | Contenu |
|---------|--------|---------|
| `kimvieware-infrastructure/docker-compose.yml` | ✅ Prêt | 8 services Docker |
| `kimvieware-infrastructure/mongodb/init-mongo.js` | ✅ Prêt | Initialisation DB |
| `kimvieware-infrastructure/rabbitmq/rabbitmq.conf` | ✅ Prêt | Config RabbitMQ |

### 4. **Modèles Partagés**

| Fichier | Statut | Contenu |
|---------|--------|---------|
| `kimvieware-shared/src/models/job_message.py` | ✅ Prêt | Message models |
| `kimvieware-shared/src/models/trajectory.py` | ✅ Prêt | Trajectory models |
| `kimvieware-shared/src/models/sut_info.py` | ✅ Prêt | SUT info models |

---

## 📋 PLAN D'ACTION DÉTAILLÉ

### **ÉTAPE 1: VÉRIFICATION PRÉALABLE (5-10 min)**

#### 1.1 Vérifier les dépendances
```bash
# Pour chaque phase
for phase in phase0 phase1 phase2 phase3 phase4; do
  echo "Checking $phase..."
  cd kimvieware-$phase-*
  pip list | grep -E 'angr|numpy|scipy|deap|pytest|mutpy|magic'
done

# Vérifier aussi l'orchestrator
cd kimvieware-orchestrator
pip list | grep -E 'fastapi|uvicorn'
```

#### 1.2 Vérifier l'infrastructure
```bash
# Tester les connexions
python diagnose.py
```

**Checklist**:
- [ ] Docker installé et en cours d'exécution
- [ ] RabbitMQ accessible (5672)
- [ ] MongoDB accessible (27017)
- [ ] Redis accessible (6379)
- [ ] MinIO accessible (9000)

---

### **ÉTAPE 2: TESTS UNITAIRES (20-30 min)**

#### 2.1 Phase 0 - Validator

**Fichier à tester**: `kimvieware-phase0-validator/src/validator_service.py`

```bash
cd kimvieware-phase0-validator
pytest tests/ -v --cov=src
```

**Points de test**:
- [ ] Détection Python
- [ ] Détection C
- [ ] Détection Java
- [ ] Validation de structure
- [ ] Extraction de métadonnées

#### 2.2 Phase 1 - Extractor

**Fichier à tester**: `kimvieware-phase1-extractor/src/extractor_service.py`

```bash
cd kimvieware-phase1-extractor
pytest tests/ -v --cov=src
```

**Points de test**:
- [ ] Python extraction
- [ ] C extraction
- [ ] Java extraction
- [ ] Génération CFG
- [ ] Collection de trajectoires

#### 2.3 Phase 2 - SGATS

**Fichier à tester**: `kimvieware-phase2-sgats/src/sgats_service.py`

```bash
cd kimvieware-phase2-sgats
pytest tests/ -v --cov=src
```

**Points de test**:
- [ ] Clustering trajectoires
- [ ] Calcul similarité Jaccard
- [ ] Sélection représentative
- [ ] Vérification couverture

#### 2.4 Phase 3 - EvoPath

**Fichier à tester**: `kimvieware-phase3-evopath/src/evopath_service.py`

```bash
cd kimvieware-phase3-evopath
pytest tests/ -v --cov=src
```

**Points de test**:
- [ ] Initialisation population
- [ ] Évaluation fitness
- [ ] Croisement (crossover)
- [ ] Mutation
- [ ] Sélection

#### 2.5 Phase 4 - Executor

**Fichier à tester**: `kimvieware-phase4-executor/src/executor_service.py`

```bash
cd kimvieware-phase4-executor
pytest tests/ -v --cov=src
```

**Points de test**:
- [ ] Génération tests
- [ ] Résolution Z3
- [ ] Mutation testing
- [ ] Calcul score

---

### **ÉTAPE 3: TESTS D'INTÉGRATION (30-40 min)**

#### 3.1 Test du Pipeline Complet

```bash
# Depuis la racine du projet
python test_complete_pipeline.py
```

**Étapes exécutées**:
- [ ] Phase 0: Validation auth-service
- [ ] Phase 1: Extraction (140 trajectoires attendues)
- [ ] Phase 2: Réduction SGATS (80-90%)
- [ ] Phase 3: Optimisation EvoPath (33-50%)
- [ ] Phase 4: Génération & Mutation (score >90%)

**Résultats attendus**:
```json
{
  "job_id": "uuid",
  "sut_name": "auth-service",
  "status": "completed",
  "metrics": {
    "phase0": {"language": "python", "files": "N"},
    "phase1": {"trajectories": 140},
    "phase2": {"reduced": 21, "reduction": "85%"},
    "phase3": {"optimized": 15, "reduction": "28%"},
    "phase4": {"tests": 15, "mutation_score": "93.1%"}
  }
}
```

#### 3.2 Test Multi-SUT

```bash
# Test sur plusieurs services
python test_full_system.py
```

**Services à tester** (séquentiellement):
- [ ] auth-service (Python)
- [ ] course-service (Python)
- [ ] grade-service (Python)
- [ ] room-service (Python)
- [ ] timetable-service (Python)
- [ ] auth-service-c (C)
- [ ] auth-service-java (Java)

**Durée estimée**: 2-3 heures

---

### **ÉTAPE 4: TESTS DE L'API GATEWAY (15-20 min)**

#### 4.1 Démarrer le serveur

```bash
cd kimvieware-orchestrator
python run_orchestrator.py
```

#### 4.2 Tester les endpoints

```bash
# Soumettre un SUT
curl -X POST http://localhost:8080/api/submit \
  -F "file=@auth-service.zip"

# Lister les jobs
curl http://localhost:8080/api/jobs

# Récupérer un job spécifique
curl http://localhost:8080/api/job/{job_id}

# Obtenir les statistiques
curl http://localhost:8080/api/stats
```

#### 4.3 Tester le Dashboard

```bash
# Accéder au dashboard
open http://localhost:8080
```

**Fonctionnalités à tester**:
- [ ] Soumettre un SUT via formulaire
- [ ] Voir la liste des jobs
- [ ] Voir le détail d'un job
- [ ] Voir les statistiques en temps réel
- [ ] WebSocket updates

---

### **ÉTAPE 5: TESTS DE PERFORMANCE (20-30 min)**

#### 5.1 Métriques de Temps

```bash
# Avec timestamps
python -c "
import time
import subprocess

tests = {
    'Phase 0': 'python -c \"...\"',
    'Phase 1': 'python -c \"...\"',
    'Phase 2': 'python -c \"...\"',
    'Phase 3': 'python -c \"...\"',
    'Phase 4': 'python -c \"...\"'
}

for name, cmd in tests.items():
    start = time.time()
    subprocess.run(cmd, shell=True)
    duration = time.time() - start
    print(f'{name}: {duration:.2f}s')
"
```

#### 5.2 Utilisation des Ressources

```bash
# Monitor pendant le test
docker stats --no-stream
```

**Métriques à suivre**:
- [ ] CPU usage par phase
- [ ] Mémoire RAM
- [ ] I/O Disk
- [ ] Bande passante réseau

---

### **ÉTAPE 6: VALIDATION DES RÉSULTATS (10-15 min)**

#### 6.1 Générer le Rapport

```bash
python FULL_TEST_REPORT.py
```

#### 6.2 Analyser les Résultats

Vérifier dans `KIMVIWARE_TEST_REPORT.json`:
- [ ] `phase0.status == "completed"`
- [ ] `phase1.trajectories >= 140`
- [ ] `phase2.reduction_rate >= 0.80`
- [ ] `phase3.reduction_rate >= 0.33`
- [ ] `phase4.mutation_score >= 0.90`

#### 6.3 Vérifier les Logs

```bash
# Logs orchestrator
tail -f ~/.kimvieware/logs/orchestrator.log

# Logs Docker
docker logs kimvieware_rabbitmq -f
docker logs kimvieware_mongodb -f
```

---

## 🚀 PLAN D'EXÉCUTION RECOMMANDÉ

### **Option A: Test Rapide (15 min)**
```
1. Diagnostic infrastructure     (diagnose.py)          ✓ 5 min
2. Rapport système              (generate_report.py)    ✓ 3 min
3. Rapport complet              (FULL_TEST_REPORT.py)   ✓ 7 min
→ Parfait pour vérifier l'état sans exécuter de tests réels
```

### **Option B: Test Standard (1-2 heures)** ⭐ RECOMMANDÉ
```
1. Vérification préalable        (Étape 1)               ✓ 10 min
2. Tests unitaires              (Étape 2)               ✓ 30 min
3. Test du pipeline             (test_complete_pipeline) ✓ 50 min
4. Validation des résultats     (Étape 6)               ✓ 10 min
→ Couvre tous les services avec rapport complet
```

### **Option C: Test Complet (2-3 heures)**
```
1. Vérification préalable        (Étape 1)               ✓ 10 min
2. Tests unitaires              (Étape 2)               ✓ 30 min
3. Tests d'intégration          (Étape 3)               ✓ 90 min
4. Tests API Gateway            (Étape 4)               ✓ 20 min
5. Validation des résultats     (Étape 6)               ✓ 15 min
→ Test exhaustif de tous les composants
```

### **Option D: Test de Performance (3-4 heures)**
```
1. Vérification préalable        (Étape 1)               ✓ 10 min
2. Tests unitaires              (Étape 2)               ✓ 30 min
3. Tests d'intégration          (Étape 3)               ✓ 90 min
4. Tests API Gateway            (Étape 4)               ✓ 20 min
5. Tests de performance         (Étape 5)               ✓ 30 min
6. Validation des résultats     (Étape 6)               ✓ 15 min
→ Analysis complète incluant performance et scaling
```

---

## 📝 CHECKLIST DE DÉMARRAGE

```bash
# ✅ PRÉ-REQUIS
[ ] Docker en cours d'exécution
[ ] docker-compose up -d (infrastructure déployée)
[ ] Python 3.9+ installé
[ ] Tous les venv configurés

# ✅ VÉRIFICATION
[ ] diagnose.py exécuté avec succès
[ ] Tous les ports accessibles
[ ] Tous les services sains

# ✅ EXÉCUTION
[ ] Sélectionner l'option (A/B/C/D)
[ ] Lancer les tests
[ ] Monitorer les logs
[ ] Analyser les résultats

# ✅ RAPPORT
[ ] Résultats générés
[ ] Métriques valides
[ ] Documentation mise à jour
```

---

## 📊 MÉTRIQUES ATTENDUES

| Métrique | Attendu | Acceptable | Critique |
|----------|---------|-----------|----------|
| Phase 0 Duration | <5s | <10s | >15s ❌ |
| Phase 1 Duration | 10-30s | <60s | >120s ❌ |
| Phase 2 Reduction | 80-90% | >70% | <50% ❌ |
| Phase 3 Reduction | 33-50% | >20% | <10% ❌ |
| Phase 4 Mutation | >90% | >85% | <80% ❌ |
| Coverage | 95%+ | 90%+ | <85% ❌ |
| API Response | <500ms | <1000ms | >2000ms ❌ |
| Memory Usage | <2GB | <4GB | >8GB ❌ |

---

## 🔧 COMMANDES RAPIDES

```bash
# Démarrer l'infrastructure
cd kimvieware-infrastructure
docker-compose up -d

# Tester rapidement
cd ..
python diagnose.py

# Test complet (40-50 min)
python test_complete_pipeline.py

# Voir les résultats
cat KIMVIWARE_TEST_REPORT.json | python -m json.tool

# Nettoyer
docker-compose down -v
```

---

## 📞 DÉPANNAGE

### Problème: `[server exited unexpectedly]`
```bash
# Redémarrer la session tmux
tmux kill-session -t kimviware
python start_orchestration.sh
```

### Problème: RabbitMQ inaccessible
```bash
# Vérifier l'état
docker ps | grep rabbitmq

# Redémarrer si nécessaire
docker restart kimvieware_rabbitmq
```

### Problème: MongoDB inaccessible
```bash
# Vérifier l'état
docker ps | grep mongodb

# Vérifier la connexion
mongosh "mongodb://admin:kimvie2025@localhost:27017/"
```

### Problème: Dépendances manquantes
```bash
# Pour chaque phase
cd kimvieware-phase-X-*
pip install -r requirements.txt -e ../kimvieware-shared
```

---

## ✅ PROCHAINES ÉTAPES

Après ce plan:
1. [ ] Documenter les résultats
2. [ ] Identifier les problèmes éventuels
3. [ ] Optimiser les performances
4. [ ] Mettre à jour la documentation
5. [ ] Créer des rapports réguliers

---

**Créé le**: 23 Janvier 2026  
**Auteur**: Plan d'Action Automatisé  
**Version**: 1.0

