from sqlmodel import create_engine

DATABASE_URL = "sqlite:///watchwhatwhere.db"
engine = create_engine(DATABASE_URL, echo=False)
