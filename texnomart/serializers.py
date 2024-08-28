from email.mime import image

from django.db.models import Sum, Avg, Count
from rest_framework import serializers
from .models import Product, Category, Image, Attribute, AttributeValue, AttributeKey


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

    # def get_total_price_of_products(self, obj):
    #     total_price = obj.products.aggregate(Sum('price'))['price__sum']
    #     if total_price:
    #         return f'{total_price} sum'
    #     return '0 sum'

    # def get_product_count(self, obj):
    #     # product_count = Category.objects.aggregate(products_count=Count('products'))['products_count']
    #     product_count = obj.products.count()
    #     return product_count

    def get_image_of_category(self, obj):
        request = self.context.get('request')
        image = obj.image  # Access the image directly from the object
        if image:
            return request.build_absolute_uri(image.url)
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
        return bool(obj.user_likes)  # Assuming user_likes is correctly prefetched

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
