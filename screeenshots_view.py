from insider_service import InsiderService
from db.database import SessionLocal, init_db
from config import TEMP_DIR
from models import Screenshot
import os

session = SessionLocal()
insieder_service = InsiderService(session)

session.query(Screenshot).delete()
session.commit()


print(session.query(Screenshot).all())


temp_path = os.path.join(TEMP_DIR, f"chlen.jpg")

screen = insieder_service.download_screenshot('7338557546942169088', temp_path)

