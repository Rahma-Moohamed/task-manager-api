from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Task
from .serializers import LoginSerializer, RegisterSerializer, TaskSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    return Response({"tasks": "/api/tasks/"}, status=status.HTTP_200_OK)


@extend_schema(
    request=RegisterSerializer,
    responses={201: None, 400: None},
    auth=[],
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "User registered successfully."},
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=LoginSerializer,
    responses={200: None, 400: None, 401: None},
    auth=[],
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(
        request,
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )

    if user is None:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "message": "Login successful.",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(
    request=TaskSerializer,
    responses={200: TaskSerializer(many=True), 201: TaskSerializer, 400: None},
)
@api_view(["GET", "POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_new_task(request):
    if request.method == "POST":
        serializer = TaskSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    tasks = Task.objects.filter(owner=request.user)
    is_done = request.query_params.get("is_done")
    if is_done is not None:
        tasks = tasks.filter(is_done=is_done.lower() == "true")

    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(tasks, request)

    if page is not None:
        serializer = TaskSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def get_user_task(request, pk):
    """Return the task if it belongs to the logged-in user, otherwise None."""
    try:
        return Task.objects.get(pk=pk, owner=request.user)
    except Task.DoesNotExist:
        return None


@extend_schema(responses={200: TaskSerializer, 404: None})
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def task_detail(request, pk):
    task = get_user_task(request, pk)
    if task is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = TaskSerializer(task)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=TaskSerializer,
    responses={200: TaskSerializer, 400: None, 404: None},
)
@api_view(["PUT", "PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_task(request, pk):
    task = get_user_task(request, pk)
    if task is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = TaskSerializer(
        task,
        data=request.data,
        partial=(request.method == "PATCH"),
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses={204: None, 404: None})
@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_task(request, pk):
    task = get_user_task(request, pk)
    if task is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    task.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)