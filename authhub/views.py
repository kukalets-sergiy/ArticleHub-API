from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .authentication import get_tokens_for_mongo_user, MongoUserJWTAuthentication
from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from django.contrib.auth.hashers import make_password, check_password
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.inspectors import SwaggerAutoSchema
import logging
from authhub.tasks import send_welcome_email

logger = logging.getLogger(__name__)


class AuthAutoSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        return ['Auth']


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    swagger_schema = AuthAutoSchema

    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            name = serializer.validated_data['name']
            password = serializer.validated_data['password']
            if User.objects(email=email).first():
                return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)
            user = User(
                email=email,
                name=name,
                password=make_password(password)
            )
            user.save()
            logging.info(f"New user registered: {user.email}")
            send_welcome_email.delay(str(user.id), user.email, user.name)
            return Response(
                {
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.name
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    swagger_schema = AuthAutoSchema

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = User.objects(email=email).first()
            if not user or not check_password(password, user.password):
                return Response({'error': 'Invalid credentials'}, status=401)
            tokens = get_tokens_for_mongo_user(user)
            return Response(tokens, status=200)
        return Response(serializer.errors, status=400)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    authentication_classes = [MongoUserJWTAuthentication]
    swagger_schema = AuthAutoSchema

    def get(self, request):
        user = request.user
        if not user:
            return Response({"error": "User not found"}, status=404)
        return Response(UserSerializer(user).data, status=200)
