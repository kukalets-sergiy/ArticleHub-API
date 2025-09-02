from mongoengine import Document, fields


class User(Document):
    email = fields.EmailField(required=True, unique=True)
    password = fields.StringField(required=True)
    name = fields.StringField(required=True)

    @property
    def is_authenticated(self):
        return True
