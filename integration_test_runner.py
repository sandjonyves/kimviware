
import requests
import time
import json
import sys

def run_integration_test():
    print("\n" + "="*60)
    print("🚀 TEST D'INTÉGRATION RÉEL MULTI-LANGAGES (Py, Java, C)")
    print("="*60)

    # Configuration des ports
    PYTHON_PORT = 8000
    JAVA_PORT = 8081
    C_PORT = 8082

    user_data = {
        "username": "integration_user_" + str(int(time.time()))[-4:],
        "email": "integration@test.com",
        "password": "Password123!",
        "full_name": "Integration Tester"
    }

    results = []

    # 1. Inscription sur le service Python (FastAPI)
    print(f"\n1️⃣ Inscription sur Python (Port {PYTHON_PORT})...")
    try:
        url = f"http://localhost:{PYTHON_PORT}/auth/register"
        resp = requests.post(url, json=user_data, timeout=5)
        if resp.status_code in [200, 201]:
            print(f"   ✅ Succès : Utilisateur {user_data['username']} créé.")
            results.append({"step": "Register Python", "status": "SUCCESS"})
        else:
            print(f"   ⚠️  Erreur {resp.status_code} : {resp.text}")
            results.append({"step": "Register Python", "status": "FAILED"})
    except Exception as e:
        print(f"   ❌ Erreur de connexion : {e}")
        results.append({"step": "Register Python", "status": "ERROR"})

    # 2. Connexion sur le service Java (Wrapper)
    print(f"\n2️⃣ Connexion sur Java (Port {JAVA_PORT})...")
    try:
        url = f"http://localhost:{JAVA_PORT}/auth/login"
        login_data = {"username": user_data["username"], "password": user_data["password"]}
        resp = requests.post(url, json=login_data, timeout=5)
        if resp.status_code == 200:
            print(f"   ✅ Succès : Le service Java a validé le compte créé par Python !")
            results.append({"step": "Login Java", "status": "SUCCESS"})
        else:
            print(f"   ❌ Échec {resp.status_code} : {resp.text}")
            results.append({"step": "Login Java", "status": "FAILED"})
    except Exception as e:
        print(f"   ❌ Erreur de connexion : {e}")
        results.append({"step": "Login Java", "status": "ERROR"})

    # 3. Validation de session sur le service C (Wrapper)
    print(f"\n3️⃣ Validation sur le service C (Port {C_PORT})...")
    try:
        url = f"http://localhost:{C_PORT}/auth/session"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            print(f"   ✅ Succès : {resp.json().get('status')} - Le service C est interopérable.")
            results.append({"step": "Session C", "status": "SUCCESS"})
        else:
            print(f"   ❌ Échec {resp.status_code}")
            results.append({"step": "Session C", "status": "FAILED"})
    except Exception as e:
        print(f"   ❌ Erreur de connexion : {e}")
        results.append({"step": "Session C", "status": "ERROR"})

    # Génération du rapport final
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": "PASSED" if all(r["status"] == "SUCCESS" for r in results) else "FAILED",
        "results": results,
        "interoperability_score": sum(1 for r in results if r["status"] == "SUCCESS") / len(results) * 100
    }

    with open("integration_report.json", "w") as f:
        json.dump(report, f, indent=4)

    print("\n" + "="*60)
    print(f"📊 RÉSULTAT GLOBAL : {report['overall_status']}")
    print(f"📈 SCORE D'INTEROPÉRABILITÉ : {report['interoperability_score']}%")
    print("="*60)

if __name__ == "__main__":
    run_integration_test()
