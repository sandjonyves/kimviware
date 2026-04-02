
import pymongo
import pika
import sys

def reset():
    print("🧹 Nettoyage complet du système KIMVIWARE...")

    # 1. MongoDB
    try:
        # Ajout de l'authentification admin:kimvie2025
        client = pymongo.MongoClient("mongodb://admin:kimvie2025@localhost:27017/")
        db = client["kimvieware"]
        # Supprime tous les jobs et les statistiques
        db.jobs.delete_many({})
        print("✅ MongoDB : Tous les jobs ont été supprimés.")
    except Exception as e:
        print(f"❌ Erreur MongoDB : {e}")

    # 2. RabbitMQ (Vider toutes les files)
    try:
        credentials = pika.PlainCredentials('admin', 'kimvie2025')
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost', 
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        ))
        channel = connection.channel()
        
        queues = [
            'submission.new', 
            'validation.completed', 
            'extraction.completed', 
            'reduction.completed', 
            'optimization.completed', 
            'execution.completed', 
            'phase.updates'
        ]
        
        for q in queues:
            try:
                channel.queue_purge(queue=q)
                print(f"✅ RabbitMQ : File '{q}' vidée.")
            except Exception as e:
                print(f"⚠️  RabbitMQ : Impossible de vider '{q}' (peut-être inexistante)")
                
        connection.close()
    except Exception as e:
        print(f"❌ Erreur RabbitMQ : {e}")

    print("\n✨ Nettoyage terminé. Votre machine est maintenant prête !")

if __name__ == "__main__":
    reset()
