from django.contrib import admin
from .models import InventoryItem, Category, LogEntry

admin.site.register(InventoryItem)
admin.site.register(Category)

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('item__name', 'user__username')

admin.site.register(LogEntry, LogEntryAdmin)

