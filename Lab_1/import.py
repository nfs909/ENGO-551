import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import pandas as pd


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#Imported to pandas data frame
data = pd.read_csv('books.csv', header = 0)

print(data)

#Send to server
data.to_sql('books', engine)

