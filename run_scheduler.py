import schedule
import time
import subprocess

def run_audit():
    subprocess.call(["python", "audit_cryptos.py"])

schedule.every(10).minutes.do(run_audit)

print("Le scheduler est lancé. Exécution de l'audit toutes les 10 minutes.")
while True:
    schedule.run_pending()
    time.sleep(1)
