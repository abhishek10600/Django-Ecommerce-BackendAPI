from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404

from product.models import Product
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer

from .filters import OrdersFilter


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