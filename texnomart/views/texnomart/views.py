from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Prefetch, Avg, Count, Sum
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, ListCreateAPIView, ListAPIView, \
    CreateAPIView, RetrieveUpdateAPIView, get_object_or_404  # Create your views here.
from rest_framework_simplejwt.authentication import JWTAuthentication

from texnomart.models import Product, Category, Image, Comment, Attribute, AttributeKey, AttributeValue
from texnomart.serializers import ProductSerializer, CategorySerializer, ProductDetailSerializer, \
    AttributeKeySerializer, \
    AttributeValueSerializer
from django_filters.rest_framework import DjangoFilterBackend
from texnomart.permissions import IsSuperAdminOrReadOnly
from rest_framework import filters


class AllProductView(ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', ]
    authentication_classes = [JWTAuthentication, TokenAuthentication]

    def get_queryset(self):
        cache_key = 'all_products'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        queryset = Product.objects.select_related('category').prefetch_related('images')

        request = self.request
        if request.user.is_authenticated:
            # Prefetch only the likes for the authenticated user
            user_likes = Prefetch(
                'user_likes',
                queryset=User.objects.filter(id=request.user.id),
                to_attr='user_liked'
            )
            queryset = queryset.prefetch_related(user_likes)
        cache.set(cache_key, queryset, timeout=60 * 15)  # Cache timeout in seconds
        return queryset


class CategoryView(GenericAPIView):
    queryset = Category.objects.annotate(products_count=Count('products'), products_price_sum=Sum('products__price'))
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', ]
    authentication_classes = [JWTAuthentication, TokenAuthentication]

    def get(self, request, *args, **kwargs):
        cache_key = 'category_list'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        data = serializer.data
        cache.set(cache_key, data, timeout=60 * 15)
        return Response(data)


class AddCategoryView(GenericAPIView):
    queryset = Category.objects.annotate(products_count=Count('products'), products_price_sum=Sum('products__price'))
    serializer_class = CategorySerializer

    def get(self, request, *args, **kwargs):
        data = self.get_queryset()
        serializer = self.get_serializer(data, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteCategoryView(GenericAPIView):
    queryset = Category.objects.all()  # No need for annotation here
    serializer_class = CategorySerializer
    permission_classes = [IsSuperAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        category = get_object_or_404(Category, slug=self.kwargs['slug'])
        serializer = self.get_serializer(category, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        category = get_object_or_404(Category, slug=self.kwargs['slug'])
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EditCategoryView(RetrieveUpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def delete(self, request, *args, **kwargs):
        data = Category.objects.get(id=self.kwargs['slug'])
        data.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryProductsView(GenericAPIView):
    queryset = Product.objects.select_related('category').prefetch_related(
        Prefetch('images', queryset=Image.objects.filter(is_primary=True))
    )
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', ]

    def get(self, request, *args, **kwargs):
        category_slug = self.kwargs['slug']
        cache_key = f'category_products_{category_slug}'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        products = self.queryset.filter(category__slug=category_slug)
        serializer = self.serializer_class(products, many=True, context={'request': request})
        data = serializer.data
        cache.set(cache_key, data, timeout=60 * 15)
        return Response(data)


class ProductDetailView(GenericAPIView):
    queryset = Product.objects.prefetch_related(
        Prefetch('images', queryset=Image.objects.filter(is_primary=True)),
        Prefetch('comments', queryset=Comment.objects.select_related('user')),
        Prefetch('attributes',
                 queryset=Attribute.objects.select_related('key').select_related('value'))
    ).annotate(rating=Avg('comments__rating'))
    serializer_class = ProductDetailSerializer

    def get(self, request, *args, **kwargs):
        user = self.request.user
        product_id = self.kwargs.get('pk')  # Extract the primary key from the URL
        product = self.get_queryset().filter(pk=product_id).prefetch_related(
            Prefetch(
                'user_likes',
                queryset=User.objects.filter(id=user.id),
                to_attr='user_likes_prefetched'  # Use a unique attribute name
            )
        ).first()  # Retrieve the specific product instance

        if product is None:
            return Response({'detail': 'Not found.'}, status=404)

        serializer = self.get_serializer(product)
        return Response(serializer.data)


class DeleteProductView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        data = Product.objects.get(id=self.kwargs['pk'])
        if data:
            serializer = ProductSerializer(data, context={'request': request})
            return Response(serializer.data)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        data = Product.objects.get(id=self.kwargs['pk'])
        data.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EditProductView(RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def delete(self, request, *args, **kwargs):
        data = Product.objects.get(id=self.kwargs['pk'])
        data.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AttributeKeyView(GenericAPIView):
    queryset = Attribute.objects.all()
    serializer_class = AttributeKeySerializer

    def get(self, request, *args, **kwargs):
        cache_key = 'attribute_keys'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        data = AttributeKey.objects.all()
        serializer = AttributeKeySerializer(data, many=True, context={'request': request})
        data = serializer.data
        cache.set(cache_key, data, timeout=60 * 15)
        return Response(data, status=status.HTTP_200_OK)


class AttributeValueView(GenericAPIView):
    queryset = AttributeValue.objects.all()
    serializer_class = AttributeValueSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_fields = ['created_at']
    search_fields = ['name', ]

    def get(self, request, *args, **kwargs):
        cache_key = 'attribute_ values'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        data = AttributeValue.objects.all()
        serializer = AttributeValueSerializer(data, many=True, context={'request': request})
        data = serializer.data
        cache.set(cache_key, data, timeout=60 * 15)
        return Response(data, status=status.HTTP_200_OK)
