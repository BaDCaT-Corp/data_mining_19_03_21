from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import models

table_mapper = {
    "post_data": models.Post,
    "author_data": models.Author
}

class Database:

    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def get_or_create(self, session, model, filter, **data):
        db_instance = session.query(model).filter_by(**filter).first()
        if not db_instance:
            db_instance = model(**data)
        else:
            print(2)
        return db_instance

    def create_post(self, data):
        session = self.maker()
        post = None
        for key, model in table_mapper.items():
            instance = self.get_or_create(session, model, {'url': data[key]['url']}, **data[key])
            if isinstance(instance, models.Post):
                post = instance
            elif isinstance(instance, models.Author):
                post.author = instance

        post.tags.extend([
            self.get_or_create(session, models.Tag, {'url': tag_data["url"]}, **tag_data)
            for tag_data in data["tags_data"]
        ])

        try:
            session.add(post)
            session.commit()
        except Exception:
            session.rollbask()
        finally:
            session.close()

        print(1)