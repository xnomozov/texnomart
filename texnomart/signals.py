import json

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, Category
from django.contrib.auth.models import User

import os


@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    if created:
        subject = 'Hello from Texnomart!'
        message = f'Product {instance.name} has been created recently.'
        email_from = settings.EMAIL_HOST_USER
        users = User.objects.filter(is_staff=True, is_superuser=True)
        email_list = [user.email for user in users if user.email]

        if email_list:
            try:
                send_mail(subject, message, email_from, email_list, fail_silently=False)
            except Exception as e:
                print(f'Error sending email: {e}')


@receiver(post_save, sender=Category)
def category_post_save(sender, instance, created, **kwargs):
    if created:
        subject = 'Hello from Texnomart!'
        message = f'Category {instance.name} has been created recently.'
        email_from = settings.EMAIL_HOST_USER
        email_to = ['jasurmavlonov24@gmail.com']
        try:
            send_mail(subject, message, email_from, email_to, fail_silently=False)
        except Exception as e:
            print(f'Error sending email: {e}')


@receiver(pre_delete, sender=Product)
def product_pre_delete(sender, instance, **kwargs):
    directory = 'texnomart/deleted/products'
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, f'{instance.name}_id_{instance.id}.json')

    images = [image.url for image in instance.images.all()]
    category = instance.category.title if instance.category else None

    data = {
        'id': instance.id,
        'name': instance.name,
        'description': instance.description,
        'price': instance.price,
        'images': images,
        'category': category,
        'discount': instance.discount,
        'discounted_price': instance.discounted_price,
        'monthly_pay': instance.monthly_pay,
    }

    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        raise e


@receiver(pre_delete, sender=Category)
def category_pre_delete(sender, instance, **kwargs):
    directory = 'texnomart/deleted/categories'
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, f'{instance.title}_id_{instance.id}.json')
    products = [product.name for product in instance.products.all()]
    data = {
        'id': instance.id,
        'title': instance.title,
        'products': products,
        'slug': instance.slug,
    }
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        raise e
