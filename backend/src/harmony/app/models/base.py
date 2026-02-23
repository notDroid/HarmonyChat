from sqlalchemy.orm import DeclarativeBase

class SerializerMixin:
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Base(DeclarativeBase, SerializerMixin):
    pass