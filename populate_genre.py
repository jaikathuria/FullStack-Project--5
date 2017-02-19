from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, User, Genre, Songs

engine = create_engine('postgresql://catalog:feef55cd@localhost/catalog')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

genres = ['Folk', 'Patriotic', 'Ghazal', 'Classical', 'Western', 'Filmi']

for name in genres:
    genreList = session.query(Genre).filter_by(name = name).one_or_none()
    if not genreList:
        genre = Genre(name = name)
        session.add(genre)
        session.commit()
        print name + " Added to Database!"
    else:
        print name + " Already in Database!"
