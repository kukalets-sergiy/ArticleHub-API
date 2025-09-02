from mongoengine import Document, fields
import datetime


class Article(Document):
    title = fields.StringField(required=True)
    content = fields.StringField(required=True)
    tags = fields.ListField(fields.StringField(), default=[])
    author = fields.ObjectIdField(required=True)
    analysis = fields.DictField(default={})
    created_at = fields.DateTimeField(default=datetime.datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "article"
    }
