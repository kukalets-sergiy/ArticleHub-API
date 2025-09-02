from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


class MongoUserJWTAuthentication(JWTAuthentication):
    """
    Custom authentication backend for MongoEngine User.
    Finds User by email in JWT payload and attaches it to request.user.
    """
    def get_user(self, validated_token):
        email = validated_token.get('email', None)
        if not email:
            return None
        user = User.objects(email=email).first()
        return user

def get_tokens_for_mongo_user(user):
    """Function to generate JWT tokens for a MongoDB user."""
    refresh = RefreshToken()        # Create a new refresh token
    refresh['email'] = user.email
    refresh['user_id'] = str(user.id)
    access = refresh.access_token   # Create access token from refresh token
    access['email'] = user.email
    access['user_id'] = str(user.id)
    return {
        'refresh': str(refresh),
        'access': str(access),
    }