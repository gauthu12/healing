
from apscheduler.schedulers.background import BackgroundScheduler

def health_check():
    print("Running background health check (mock)...")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(health_check, 'interval', seconds=60)
    scheduler.start()
