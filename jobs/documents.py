# documents.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from jobs.models import Jobs

@registry.register_document
class JobDocument(Document):
    post_text = fields.TextField()   # Full-text search in post_text only

    class Index:
        name = 'jobs'                # Name of the Elasticsearch index

    class Django:
        model = Jobs
        fields = ['id']              # Include only fields needed for Elasticsearch

