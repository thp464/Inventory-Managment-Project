import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from rest_framework import viewsets, permissions

from .forms import UserRegistrationForm, InventoryItemForm
from .models import InventoryItem, Category, LogEntry
from .serializers import InventoryItemSerializer, CategorySerializer
from inventory_managment.settings import LOW_QUANTITY

# Homepage View
class Index(TemplateView):
    template_name = 'inventory/index.html'

# Dashboard View - Displays inventory list with sorting, searching, and low inventory alerts
class Dashboard(LoginRequiredMixin, View):
	def get(self, request):
		# Get sort parameter from query string (default to 'id')
		sort_by = request.GET.get('sort', 'id')

		# Get search query (if any), stripping whitespace
		query = request.GET.get('q','').strip()

		 # Only allow specific fields to be sorted
		allowed_fields = ['id', 'name', 'quantity', 'category__name']
		clean_sort = sort_by.lstrip('-')
		if clean_sort not in allowed_fields:
			sort_by = 'id'

		# Get all inventory items from the database that belong to the currently logged-in user.
		items = InventoryItem.objects.filter(is_active=True)

		# If a search query exists, filter by item name or category name (case-insensitive)
		if query:
			items = items.filter(
                Q(name__icontains=query) | Q(category__name__icontains=query)
            )
		
		
		items = items.order_by(sort_by)

        # Low inventory alerts
		low_inventory = InventoryItem.objects.filter(
			quantity__lte=LOW_QUANTITY,
			is_active=True
		) 

		if low_inventory.count() > 0:
			if low_inventory.count() > 1:
				messages.error(request, f'{low_inventory.count()} items have low inventory')
			else:
				messages.error(request, f'{low_inventory.count()} item has low invetory')

		low_inventory_ids = InventoryItem.objects.filter(
			quantity__lte=LOW_QUANTITY,
			is_active=True
		).values_list('id', flat=True)

		return render(request, 'inventory/dashboard.html', {
			'items': items, 
			'low_inventory_ids': low_inventory_ids, 
			'sort_by': sort_by,
			'query': query
			})

class SignUpView(View):
	def get(self, request):
		form = UserRegistrationForm()
		return render(request, 'inventory/signup.html', {'form': form})

	def post(self, request):
		form = UserRegistrationForm(request.POST)

		if form.is_valid():
			form.save()
			user = authenticate(
				username=form.cleaned_data['username'],
				password=form.cleaned_data['password1']
			)

			login(request, user)
			return redirect('index')

		return render(request, 'inventory/signup.html', {'form': form})
	
class AddItem(LoginRequiredMixin, CreateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item-form.html'
	success_url = reverse_lazy('dashboard')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['categories'] = Category.objects.all()
		return context

	def form_valid(self, form):
		form.instance.user = self.request.user
		response = super().form_valid(form)
		LogEntry.objects.create(
			user=self.request.user,
			item=self.object,
			action='created'
		)
		return response

class EditItem(LoginRequiredMixin, UpdateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item-form.html'
	success_url = reverse_lazy('dashboard')

	def form_valid(self, form):
		response = super().form_valid(form)
		LogEntry.objects.create(
			user=self.request.user,
			item=self.object,
			action='updated'
		)
		return response


class DeleteItem(LoginRequiredMixin, DeleteView):
	model = InventoryItem
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('dashboard')
	content_object_name = 'item'
	
	def post(self, request, pk):
		item = InventoryItem.objects.get(pk=pk, user=request.user)
		item.is_active = False
		item.save()
		LogEntry.objects.create(
            user=request.user,
            item=item,
            action='deleted'
        )
		Context = None
		messages.success(request, f"{item.name} was archived.")
		return redirect('dashboard')
	
class ItemHistory(LoginRequiredMixin, View):
    def get(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        logs = LogEntry.objects.filter(item=item).order_by('-timestamp')		
        return render(request, 'inventory/item-history.html', {
            'item': item,
            'logs': logs,
        })
	
def export_inventory_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory.csv"'

    writer = csv.writer(response)
    
    writer.writerow(['ID', 'Name', 'Quantity', 'Category', 'Created By'])

    items = InventoryItem.objects.filter(user=request.user, is_active=True)

    for item in items:
        writer.writerow([
            item.id,
            item.name,
            item.quantity,
            item.category.name if item.category else '',
            item.user.username if item.user else '',
        ])

    return response

class BulkActionView(LoginRequiredMixin, View):
    def post(self, request):
        selected_ids = request.POST.getlist('selected_items')
        action = request.POST.get('action')

        if not selected_ids:
            messages.error(request, "No items selected.")
            return HttpResponseRedirect(reverse('dashboard'))

        items = InventoryItem.objects.filter(id__in=selected_ids, user=request.user)

        if action == 'delete':
            count, _ = items.delete()
            messages.success(request, f"Deleted {count} items.")
            return HttpResponseRedirect(reverse('dashboard'))

        elif action == 'export':
            # Export selected items as CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=inventory_export.csv'

            writer = csv.writer(response)
            writer.writerow(['ID', 'Name', 'Quantity', 'Category'])
            for item in items:
                writer.writerow([
                    item.id,
                    smart_str(item.name),
                    item.quantity,
                    smart_str(item.category.name if item.category else '')
                ])
            return response

        else:
            messages.error(request, "Invalid action.")
            return HttpResponseRedirect(reverse('dashboard'))
		
# --- REST API Views ---

# InventoryItem API - Full CRUD for authenticated users		
class InventoryItemViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InventoryItem.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Category API - Read-only for authenticated users
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
