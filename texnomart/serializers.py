from django.contrib.auth.models import User

from rest_framework.exceptions import ValidationError

from rest_framework import serializers
from .models import Product, Category, AttributeValue, AttributeKey


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    user_likes = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    def get_category(self, obj):
        return obj.category.title

    def get_user_likes(self, obj):
        return hasattr(obj, 'user_liked') and bool(obj.user_liked)

    def get_image(self, obj):
        request = self.context.get('request')
        image = next((img for img in obj.images.all() if img.is_primary), None)
        if image:
            return request.build_absolute_uri(image.image.url)
        return None

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'discounted_price', 'discount', 'user_likes', 'image', 'monthly_pay',
                  'category', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    image_of_category = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(source='products_count', read_only=True)
    total_price_of_products = serializers.IntegerField(source='products_price_sum', read_only=True)

    def get_image_of_category(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    class Meta:
        model = Category
        fields = '__all__'


class ProductDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    user_likes = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()

    def get_attributes(self, obj):
        attributes_dict = {}
        for attr in obj.attributes.all():
            attributes_dict[attr.key.key] = attr.value.value
        return attributes_dict

    def get_images(self, obj):
        request = self.context.get('request')
        images = obj.images.all()
        return [request.build_absolute_uri(img.image.url) for img in images] if images else []

    def get_user_likes(self, obj):
        return bool(obj.user_likes_prefetched)

    def get_comments(self, obj):
        comments = obj.comments.select_related('user').all()
        return [
            {
                comment.user.username: {
                    'content': comment.content,
                    'time': comment.created_at.isoformat(),
                    'rating': comment.rating
                }
            }
            for comment in comments
        ]

    def get_rating(self, obj):
        return obj.rating

    class Meta:
        model = Product
        fields = '__all__'


class AttributeKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeKey
        fields = ['id', 'key', 'created_at', ]


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = ['id', 'value', 'created_at', ]


class UserLoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ["id", "username", "password"]


class UserRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password", "password2"]

    def validate_username(self, username):
        if User.objects.filter(username=username).exists():
            raise ValidationError({"detail": "User already exists!"})
        return username

    def validate(self, data):
        if data['password'] != data['password2']:
            raise ValidationError({"message": "Both passwords must match!"})

        if User.objects.filter(email=data['email']).exists():
            raise ValidationError({"message": "Email already taken!"})

        return data

    def create(self, validated_data):
        # Remove password2 as it is not needed for user creation
        validated_data.pop('password2')

        # Create the user
        user = User.objects.create_user(**validated_data)
        return user
