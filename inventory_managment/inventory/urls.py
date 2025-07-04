from django.contrib import admin
from django.urls import path, include
from .views import (Index, SignUpView, Dashboard, AddItem, EditItem, DeleteItem,
                    ItemHistory, export_inventory_csv, BulkActionView, InventoryItemViewSet,
                    CategoryViewSet)
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'items', InventoryItemViewSet, basename='item')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('add-item/', AddItem.as_view(), name='add-item'),
    path('edit-item/<int:pk>', EditItem.as_view(), name='edit-item'),
    path('delete-item/<int:pk>', DeleteItem.as_view(), name='delete-item'),
    path('item/<int:pk>/history/', ItemHistory.as_view(), name='item-history'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='inventory/logout.html'), name='logout'),
    path('export-csv/', export_inventory_csv, name='export-csv'),
    path('bulk-action/', BulkActionView.as_view(), name='bulk_action'),
    path('api/', include(router.urls)),
]