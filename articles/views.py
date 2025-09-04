from django.http.response import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Article
from .serializers import ArticleCreateSerializer, ArticleShortSerializer, ArticleDetailSerializer, \
    ArticleDetailNoCreatedSerializer
from authhub.authentication import MongoUserJWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg import openapi


class ArticlesAutoSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        return ['Articles']


class ArticleListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [MongoUserJWTAuthentication]
    swagger_schema = ArticlesAutoSchema

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, description="Search term for title or content",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('tag', openapi.IN_QUERY, description="Filter by tag", type=openapi.TYPE_STRING)
    ])
    def get(self, request):
        query = Article.objects
        search = request.query_params.get('search')
        tag = request.query_params.get('tag')
        if search or tag:
            if search:
                query = query.filter(
                    __raw__={'$or': [
                        {'title': {'$regex': search, '$options': 'i'}},
                        {'content': {'$regex': search, '$options': 'i'}}
                    ]}
                )
            if tag:
                query = query.filter(tags=tag)
            articles = query.all()
            data = [ArticleShortSerializer(a).data for a in articles]
            return Response(data)
        else:
            articles = query.all()
            data = [ArticleDetailSerializer(a).data for a in articles]
            return Response(data)

    @swagger_auto_schema(request_body=ArticleCreateSerializer)
    def post(self, request):
        serializer = ArticleCreateSerializer(data=request.data)
        if serializer.is_valid():
            article = Article(
                title=serializer.validated_data['title'],
                content=serializer.validated_data['content'],
                tags=serializer.validated_data.get('tags', []),
                author=request.user.id
            )
            article.save()
            return Response(
                ArticleDetailSerializer(article).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ArticleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [MongoUserJWTAuthentication]
    swagger_schema = ArticlesAutoSchema

    def get(self, request, id):
        article = Article.objects(id=id).first()
        if not article:
            return Response({"error": "Not found"}, status=404)
        return Response(ArticleDetailNoCreatedSerializer(article).data)

    @swagger_auto_schema(request_body=ArticleCreateSerializer)
    def put(self, request, id):
        article = Article.objects(id=id).first()
        if not article:
            return Response({"error": "Not found"}, status=404)
        if str(article.author) != str(request.user.id):
            return Response({"error": "Forbidden. You are not the author of this article"}, status=403)
        serializer = ArticleCreateSerializer(data=request.data)
        if serializer.is_valid():
            article.title = serializer.validated_data['title']
            article.content = serializer.validated_data['content']
            article.save()
            return Response(ArticleDetailSerializer(article).data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        article = Article.objects(id=id).first()
        if not article:
            return Response({"error": "Not found"}, status=404)
        if str(article.author) != str(request.user.id):
            return Response({"error": "Forbidden. You are not the author of this article"}, status=403)
        article.delete()
        return Response(status=204)


class ArticleAnalyzeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [MongoUserJWTAuthentication]
    swagger_schema = ArticlesAutoSchema

    def post(self, request, id):
        article = Article.objects(id=id).first()
        if not article:
            return Response("{error: Not found}", status=404)
        if str(article.author) != str(request.user.id):
            return Response({"error": "Forbidden. You are not the author of this article"}, status=403)
        from .tasks import analyze_article
        analyze_article.delay(str(article.id))
        return Response(
            {"message": "Analysis started. Check back later for results."},
            status=202
        )

class HealthCheckAPIView(APIView):
    permission_classes = []
    authentication_classes = []

    @swagger_auto_schema(
        operation_description="Health check endpoint",
        responses={200: 'OK'}
    )
    def get(self, request):
        return Response({"status": "ok"})
