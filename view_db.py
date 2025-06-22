from db.database import SessionLocal
from models import Employee, Screenshot

def view_database():
    session = SessionLocal()
    table = Screenshot
    table2 = Employee
    try:
        # Получаем все записи
        images = session.query(table).all()
        mages = session.query(table2).all()
        
        print("\n=== Содержимое базы данных ===")
        print(f"Всего записей: {len(images)}\n")
        
        for img in images:
            print(img.id, img.insider_id)

        for user in mages:
            print(user.id, user.insider_id )
            
    except Exception as e:
        print(f"Ошибка при чтении базы данных: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    view_database() 