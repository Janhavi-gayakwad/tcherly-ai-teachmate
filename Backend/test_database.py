from app.database.connection import Base, engine
from app.database import models

Base.metadata.create_all(bind=engine)

print("Database created successfully!")
print("All tables created successfully!")