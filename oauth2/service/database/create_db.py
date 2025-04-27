import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from service.database.models import get_table_definitions

Base = declarative_base()

def init_db(db_path="service/oauth_provider.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    with engine.connect() as connection:
        for table_name, table_def in get_table_definitions().items():
            connection.execute(text(table_def))
            print(f"Created table: {table_name}")

    return sessionmaker(bind=engine)()