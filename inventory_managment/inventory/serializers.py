from rest_framework import serializers
from .models import InventoryItem, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class InventoryItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category', queryset=Category.objects.all(), write_only=True
    )

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'name', 'quantity', 'category', 'category_id',
            'date_created', 'user', 'is_active'
        ]
        read_only_fields = ['user', 'date_created', 'is_active']