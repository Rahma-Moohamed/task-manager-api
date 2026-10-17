from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (
    api_root,
    create_new_task,
    delete_task,
    login_view,
    register_user,
    task_detail,
    update_task,
)

urlpatterns = [
    path('', api_root, name='api-root'),
    path('register/', register_user, name='register'),
    path('login/', login_view, name='login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('tasks/', create_new_task, name='tasks'),
    path('tasks/<int:pk>/', task_detail, name='task-detail'),
    path('tasks/<int:pk>/update/', update_task, name='task-update'),
    path('tasks/<int:pk>/delete/', delete_task, name='task-delete'),
]