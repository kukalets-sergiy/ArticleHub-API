from django.urls import path
from articles.views import ArticleListCreateView, ArticleDetailView, ArticleAnalyzeView, HealthCheckAPIView

app_name = 'articles'

urlpatterns = [
    path('', ArticleListCreateView.as_view(), name='article-list-create'),
    path('<str:id>/', ArticleDetailView.as_view(), name='article-detail'),
    path('<str:id>/analyze/', ArticleAnalyzeView.as_view(), name='article-analyze'),
]
