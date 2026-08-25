import os
import sys
import pandas as pd

# Add Backend folder to Python path
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)

from app.database.connection import SessionLocal
from app.database.models import Teacher, Lecture


def ingest_excel(file_path):

    # Read Excel file
    df = pd.read_excel(file_path)

    print("Excel file loaded successfully!")
    print("Columns found:")
    print(df.columns.tolist())

    # Connect to database
    db = SessionLocal()

    try:
        # Create sample teacher
        teacher = Teacher(
            name="Demo Teacher"
        )

        db.add(teacher)
        db.commit()
        db.refresh(teacher)

        print(f"Teacher created: {teacher.name}")

        # Create lecture
        lecture = Lecture(
            title="Imported Lecture",
            teacher_id=teacher.id
        )

        db.add(lecture)
        db.commit()
        db.refresh(lecture)

        print(f"Lecture created: {lecture.title}")

        print("Excel → Database ingestion completed successfully!")

    except Exception as e:
        print("Error:", e)
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":

    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "tcherly_data.xlsx"
    )

    ingest_excel(file_path)