import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404
import stripe.error
from django.contrib.auth.models import User

from product.models import Product
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer

from .filters import OrdersFilter

from utils.helpers import get_current_host

import stripe


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def new_order(request):

    user = request.user
    data = request.data
    order_items = data["orderItems"]

    if len(order_items) == 0:
        return Response({"error": "No Order Items. Please add atleast one product"}, status=status.HTTP_400_BAD_REQUEST)

    else:

        # Create Order

        total_amount = sum(item["price"] * item["quantity"]
                           for item in order_items)

        order = Order.objects.create(
            user=user,
            street=data["street"],
            city=data["city"],
            state=data["state"],
            zip_code=data["zip_code"],
            phone_no=data["phone_no"],
            country=data["country"],
            total_amount=total_amount,
        )

        # Create Order Items and set order to order items

        for i in order_items:
            product = Product.objects.get(id=i["product"])

            item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                quantity=i["quantity"],
                price=i["price"]
            )

            # update product stock
            product.stock = product.stock - item.quantity
            product.save()

        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_orders(request):

    # filter

    filterset = OrdersFilter(
        request.GET, queryset=Order.objects.all().order_by("id"))
    count = filterset.qs.count()

    # pagination

    resPerPage = 1
    paginator = PageNumberPagination()
    paginator.page_size = resPerPage

    queryset = paginator.paginate_queryset(filterset.qs, request)

    serializer = OrderSerializer(queryset, many=True)

    return Response({
        "count": count,
        "resPerPage": resPerPage,
        "orders": serializer.data
    })

    # without filter
    # orders = Order.objects.all()
    # serializer = OrderSerializer(orders, many=True)
    # return Response({"orders": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_order(request, pk):
    order = get_object_or_404(Order, id=pk)
    serializer = OrderSerializer(order, many=False)
    return Response({"order": serializer.data})


@api_view(["PUT"])
@permission_classes([IsAdminUser])
def process_order(request, pk):

    order = get_object_or_404(Order, id=pk)

    order.status = request.data["status"]
    order.save()

    serializer = OrderSerializer(order, many=False)
    return Response({"order": serializer.data})


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_order(request, pk):
    order = get_object_or_404(Order, id=pk)
    order.delete()
    return Response({"message": "Order deleted"})


# payment endpoint

stripe.api_key = os.environ.get("STRIPE_PRIVATE_KEY")


# this is the route for taking checkout
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):

    DOMAIN = get_current_host(request)

    user = request.user
    data = request.data

    order_items = data["orderItems"]

    shipping_details = {
        "street": data["street"],
        "city": data["city"],
        "state": data["state"],
        "zip_code": data["zip_code"],
        "phone_no": data["phone_no"],
        "country": data["country"],
        "user": user.id
    }

    checkout_order_items = []
    for item in order_items:
        checkout_order_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": item["name"],
                    "images": [item["image"]],
                    "metadata": {"product_id": item["product"]}
                },
                "unit_amount": item["price"] * 100
            },
            "quantity": item["quantity"]
        })

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        metadata=shipping_details,
        line_items=checkout_order_items,
        customer_email=user.email,
        mode="payment",
        success_url=DOMAIN,
        cancel_url=DOMAIN
    )

    return Response({"session": session})


# this is the route if user pays with the card
@api_view(["POST"])
def stripe_webhook(request):
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            webhook_secret
        )
    except ValueError as e:
        return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError as e:
        return Response({"error": "Invalid Signature"}, status=status.HTTP_400_BAD_REQUEST)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        print("session", session)

        line_items = stripe.checkout.Session.list_line_items(session["id"])

        price = session["amount_total"] / 100

        order = Order.objects.create(
            user=User(session.metadata.user),
            street=session.metadata.street,
            city=session.metadata.city,
            state=session.metadata.state,
            zip_code=session.metadata.zip_code,
            phone_no=session.metadata.phone_no,
            country=session.metadata.country,
            total_amount=price,
            payment_mode="CARD",
            payment_status="PAID"
        )

        for item in line_items["data"]:

            print("item", item)

            line_product = stripe.Product.retrieve(item.price.product)
            product_id = line_product.metadata.product_id

            product = Product.objects.get(id=product_id)

            item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                quantity=item.quantity,
                price=item.price.unit_amount / 100,
                image=line_product.images[0]
            )

            product.stock = product.stock - item.quantity

            product.save()

    return Response({"message": "Payment successfull"})
