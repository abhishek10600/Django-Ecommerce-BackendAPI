from django.urls import path
from .views import get_products, get_product, upload_product_images, new_product, update_product, delete_product, create_review

urlpatterns = [
    path("products/", get_products, name="get_products"),
    path("products/new/", new_product, name="new_product"),
    path("products/upload_images/", upload_product_images,
         name="upload_product_images"),
    path("products/<str:pk>/", get_product, name="get_product_detils"),
    path("products/<str:pk>/update/", update_product, name="update_product"),
    path("products/<str:pk>/delete/", delete_product, name="delete_product"),
    path("<str:pk>/reviews/", create_review, name="create_update_review")
]
