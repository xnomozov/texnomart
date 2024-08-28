from django.utils import timezone

from django.db import models
from django.template.defaultfilters import slugify
from rest_framework.authtoken.admin import User


# Create your models here.
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class Category(TimeStampedModel):
    title = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(max_length=300, blank=True, unique=True)
    image = models.ImageField(upload_to='images/', blank=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class Product(TimeStampedModel):
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300)
    price = models.FloatField()
    description = models.TextField()
    user_likes = models.ManyToManyField(User, related_name='likes', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    discount = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1

            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1

        super(Product, self).save(*args, **kwargs)

    @property
    def discounted_price(self):
        if self.discount > 0:
            return self.price * (1 - self.discount / 100)
        return self.price

    @property
    def monthly_pay(self):
        if self.discounted_price:
            payment = self.discounted_price / 24
            return f'{round(payment, 1)} sum / 24 months'

    def __str__(self):
        return self.name


class Image(TimeStampedModel):
    image = models.ImageField(upload_to='images/')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.product.name


class AttributeValue(TimeStampedModel):
    value = models.CharField(max_length=300)

    def __str__(self):
        return self.value


class AttributeKey(TimeStampedModel):
    key = models.CharField(max_length=300)

    def __str__(self):
        return self.key


class Attribute(TimeStampedModel):
    key = models.ForeignKey(AttributeKey, on_delete=models.CASCADE)
    value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')

    def __str__(self):
        return f'{self.product.name} + {self.key}'


class Comment(TimeStampedModel):
    class RatingChoices(models.IntegerChoices):
        Zero = 0
        One = 1
        Two = 2
        Three = 3
        Four = 4
        Five = 5

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    rating = models.IntegerField(choices=RatingChoices.choices, default=RatingChoices.Zero.value)
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments_u')
