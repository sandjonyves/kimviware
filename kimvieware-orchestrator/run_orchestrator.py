#!/usr/bin/env python3
"""
KIMVIEware Orchestrator - Main Server
Port 8080 - Full browser interface
"""
import sys
from pathlib import Path

ORCH_ROOT = Path(__file__).resolve().parent
KIMVIWARE_ROOT = ORCH_ROOT.parent

# kimvieware_orchestrator + kimvieware_shared (mode développement sans pip -e)
sys.path.insert(0, str(KIMVIWARE_ROOT / "kimvieware-shared" / "src"))
sys.path.insert(0, str(ORCH_ROOT / "src"))

from kimvieware_orchestrator.main import app

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════════════════════════╗
    ║                  🚀 KIMVIEware Orchestrator Server                            ║
    ║                     Version 4.0.0 - Dashboard Pro                             ║
    ╚════════════════════════════════════════════════════════════════════════════════╝

    🌐 Démarrage du serveur...
    📍 Adresse: http://localhost:8080

    Onglets disponibles:
      🔵 Soumettre     - Télécharger et analyser un SUT
      📋 Emplois       - Voir tous les emplois en temps réel
      ⚙️ Services      - Vérifier l'état des microservices
      📈 Statistiques  - Voir les statistiques complètes

    API legacy: http://localhost:8080/api/*
    API v1:     http://localhost:8080/api/v1/*

    Appuyez sur Ctrl+C pour arrêter le serveur
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        reload=False,
    )
