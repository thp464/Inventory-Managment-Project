from django.db import models
from django.contrib.auth.models import User

class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class LogEntry(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('deleted', 'Deleted'),
        ('archived', 'Archived')
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='inventory_logs')
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='created')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.item.name} @ {self.timestamp}"