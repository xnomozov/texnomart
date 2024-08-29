from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from texnomart import serializers


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add additional responses
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['email'] = self.user.email

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data['refresh']
            refresh_token = RefreshToken(refresh_token)
            print(refresh_token)
            refresh_token.blacklist()
            response = {'Details': 'Successfully logged out.',
                        'refresh_token': str(refresh_token)}

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response = {'Details': 'Something went wrong.',
                        'more': str(e)}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(CreateAPIView):
    serializer_class = serializers.UserRegisterSerializer

    def perform_create(self, serializer):
        # Save the user and generate JWT tokens
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Customize the response with JWT tokens
        self.response_data = {
            "message": "User created successfully",
            "access": access_token,
            "refresh": refresh_token,
        }

    def create(self, request, *args, **kwargs):
        # Call the parent method to handle user creation
        response = super().create(request, *args, **kwargs)

        # Add the JWT tokens to the response
        response.data.update(self.response_data)
        return response


class LoginView(GenericAPIView):
    serializer_class = serializers.UserLoginSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')

            # Authenticate the user
            user = authenticate(username=username, password=password)

            if user:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # Return tokens and additional user information
                return Response({
                    "access": access_token,
                    "refresh": refresh_token,
                    **serializer.validated_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Handle serializer errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
