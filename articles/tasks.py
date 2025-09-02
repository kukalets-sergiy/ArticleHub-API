from .models import Article
from celery import shared_task
import logging


@shared_task
def analyze_article(article_id):
    article = Article.objects(id=article_id).first()
    if not article:
        return None
    word_count = len(article.content.split())
    unique_tags = len(set(article.tags))

    article.analysis = {
        "word_count": word_count,
        "unique_tags": unique_tags
    }
    article.save()
    return article.analysis


@shared_task
def daily_article_stats():
    """Count articles and log the result."""
    count = Article.objects.count()
    msg = f"Total articles in DB: {count}"
    logging.info(msg)
    with open("/code/logs/article_stats.log", "a") as f:
        f.write(msg + "\n")
