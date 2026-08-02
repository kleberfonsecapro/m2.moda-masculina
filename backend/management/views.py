from decimal import Decimal
from datetime import timedelta
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, View
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models.functions import TruncDate, TruncMonth
from django.urls import reverse_lazy
from orders.models import Order
from catalog.models import Product
from .models import OrderStatusHistory, Shipment


def is_manager(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Gerentes').exists())


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return is_manager(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('/vendas/entrar/')
        return redirect('/')


class DashboardView(ManagerRequiredMixin, View):
    def get(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        # Pedidos hoje
        orders_today = Order.objects.filter(created_at__date=today).count()
        orders_month = Order.objects.filter(created_at__date__gte=month_start).count()
        orders_last_month = Order.objects.filter(
            created_at__date__gte=last_month_start,
            created_at__date__lt=month_start
        ).count()

        # Faturamento
        revenue_today = Order.objects.filter(
            created_at__date=today
        ).aggregate(total=Sum('shipping_cost') + Sum(F('items__price') * F('items__quantity')))['total'] or Decimal('0')

        revenue_month = Order.objects.filter(
            created_at__date__gte=month_start
        ).aggregate(total=Sum('shipping_cost') + Sum(F('items__price') * F('items__quantity')))['total'] or Decimal('0')

        revenue_last_month = Order.objects.filter(
            created_at__date__gte=last_month_start,
            created_at__date__lt=month_start
        ).aggregate(total=Sum('shipping_cost') + Sum(F('items__price') * F('items__quantity')))['total'] or Decimal('0')

        # Pedidos por status
        status_counts = Order.objects.values('status').annotate(count=Count('id'))
        status_data = {item['status']: item['count'] for item in status_counts}

        # Top vendedores (PDV)
        top_sellers = Order.objects.filter(user__isnull=False).values(
            'user__username', 'user__first_name', 'user__last_name'
        ).annotate(
            total_orders=Count('id'),
            total_revenue=Sum(F('items__price') * F('items__quantity') + F('shipping_cost'))
        ).order_by('-total_revenue')[:5]

        # Pedidos recentes
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

        # Estoque crítico
        low_stock = Product.objects.filter(stock__lte=5, available=True).order_by('stock')[:10]

        context = {
            'orders_today': orders_today,
            'orders_month': orders_month,
            'orders_last_month': orders_last_month,
            'revenue_today': revenue_today,
            'revenue_month': revenue_month,
            'revenue_last_month': revenue_last_month,
            'status_data': status_data,
            'top_sellers': top_sellers,
            'recent_orders': recent_orders,
            'low_stock': low_stock,
        }
        return render(request, 'management/dashboard.html', context)


class OrderListView(ManagerRequiredMixin, ListView):
    model = Order
    template_name = 'management/order_list.html'
    context_object_name = 'orders'
    paginate_by = 25

    def get_queryset(self):
        qs = Order.objects.select_related('user', 'shipment').prefetch_related('items__product', 'items__variant').order_by('-created_at')

        # Filtros
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        payment = self.request.GET.get('payment')
        if payment:
            qs = qs.filter(payment_method=payment)

        channel = self.request.GET.get('channel')
        if channel == 'site':
            qs = qs.filter(user__isnull=True)
        elif channel == 'pdv':
            qs = qs.filter(user__isnull=False)

        date_from = self.request.GET.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                Q(id__icontains=search) |
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(cpf__icontains=search)
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Order.STATUS_CHOICES
        ctx['payment_choices'] = Order.PAYMENT_CHOICES
        ctx['current_filters'] = self.request.GET
        return ctx


class OrderDetailView(ManagerRequiredMixin, DetailView):
    model = Order
    template_name = 'management/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.select_related('user', 'shipment').prefetch_related(
            'items__product', 'items__variant', 'history__changed_by'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['history'] = self.object.history.select_related('changed_by').all()
        ctx['shipment'] = getattr(self.object, 'shipment', None)
        ctx['status_choices'] = Order.STATUS_CHOICES
        return ctx


class OrderStatusUpdateView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')

        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])

            # O signal cria o histórico automaticamente
            # Podemos adicionar notas extras se fornecido
            if notes:
                history = order.history.first()
                if history and history.status == new_status:
                    history.notes = f'{history.notes}\n{notes}'
                    history.save(update_fields=['notes'])

            return JsonResponse({'success': True, 'status': order.get_status_display()})
        return JsonResponse({'success': False, 'error': 'Status inválido'}, status=400)


class DispatchView(ManagerRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        shipment, _ = Shipment.objects.get_or_create(order=order)
        return render(request, 'management/dispatch.html', {'order': order, 'shipment': shipment})

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        shipment, _ = Shipment.objects.get_or_create(order=order)

        action = request.POST.get('action')
        if action == 'dispatch':
            tracking = request.POST.get('tracking_code', '').strip()
            if not tracking:
                return JsonResponse({'success': False, 'error': 'Código de rastreio obrigatório'}, status=400)

            shipment.tracking_code = tracking
            shipment.dispatched_at = timezone.now()
            shipment.notes = request.POST.get('notes', '')
            if 'label_pdf' in request.FILES:
                shipment.label_pdf = request.FILES['label_pdf']
            shipment.save()

            order.status = 'shipped'
            order.save(update_fields=['status', 'updated_at'])

            return JsonResponse({'success': True, 'tracking': tracking, 'dispatched': True})

        elif action == 'deliver':
            shipment.delivered_at = timezone.now()
            shipment.notes = request.POST.get('notes', '')
            shipment.save()

            order.status = 'delivered'
            order.save(update_fields=['status', 'updated_at'])

            return JsonResponse({'success': True, 'delivered': True})

        return JsonResponse({'success': False, 'error': 'Ação inválida'}, status=400)


class FinancialView(ManagerRequiredMixin, View):
    def get(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        period = request.GET.get('period', 'month')
        if period == 'today':
            date_from = today
        elif period == 'week':
            date_from = today - timedelta(days=7)
        elif period == 'month':
            date_from = month_start
        elif period == 'year':
            date_from = today.replace(month=1, day=1)
        else:
            date_from = month_start

        qs = Order.objects.filter(created_at__date__gte=date_from)

        # Resumo geral
        summary = qs.aggregate(
            total_orders=Count('id'),
            total_items=Sum(F('items__quantity')),
            total_revenue=Sum(F('items__price') * F('items__quantity') + F('shipping_cost')),
            total_shipping=Sum('shipping_cost'),
        )

        # Por forma de pagamento
        by_payment = qs.values('payment_method').annotate(
            count=Count('id'),
            revenue=Sum(F('items__price') * F('items__quantity') + F('shipping_cost'))
        ).order_by('-revenue')

        # Por canal
        by_channel = qs.values(
            channel=F('user__isnull')
        ).annotate(
            count=Count('id'),
            revenue=Sum(F('items__price') * F('items__quantity') + F('shipping_cost'))
        )

        # Por vendedor (PDV)
        by_seller = qs.filter(user__isnull=False).values(
            'user__username', 'user__first_name', 'user__last_name'
        ).annotate(
            count=Count('id'),
            revenue=Sum(F('items__price') * F('items__quantity') + F('shipping_cost'))
        ).order_by('-revenue')

        # Evolução diária (últimos 30 dias)
        thirty_days_ago = today - timedelta(days=30)
        daily = Order.objects.filter(created_at__date__gte=thirty_days_ago).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            orders=Count('id'),
            revenue=Sum(F('items__price') * F('items__quantity') + F('shipping_cost'))
        ).order_by('day')

        context = {
            'summary': summary,
            'by_payment': by_payment,
            'by_channel': by_channel,
            'by_seller': by_seller,
            'daily': list(daily),
            'period': period,
        }
        return render(request, 'management/financial.html', context)


class StockAlertView(ManagerRequiredMixin, View):
    def get(self, request):
        threshold = int(request.GET.get('threshold', 5))

        low_stock = Product.objects.filter(
            stock__lte=threshold, available=True
        ).order_by('stock')

        # Valor total em estoque
        total_stock_value = sum(p.stock_value for p in Product.objects.filter(available=True))
        total_items = sum(p.stock for p in Product.objects.filter(available=True))

        context = {
            'low_stock': low_stock,
            'threshold': threshold,
            'total_stock_value': total_stock_value,
            'total_items': total_items,
        }
        return render(request, 'management/stock_alert.html', context)


class ExportOrdersView(ManagerRequiredMixin, View):
    def get(self, request):
        import csv
        from django.http import HttpResponse

        qs = OrderListView().get_queryset(request)

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="pedidos.csv"'

        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'ID', 'Data', 'Canal', 'Cliente', 'Email', 'Telefone', 'CPF',
            'Endereço', 'Cidade', 'Estado', 'CEP',
            'Status', 'Pagamento', 'Frete', 'Total', 'Vendedor'
        ])

        for order in qs:
            writer.writerow([
                order.id,
                order.created_at.strftime('%d/%m/%Y %H:%M'),
                'Site' if not order.user else 'PDV',
                order.full_name,
                order.email,
                order.phone,
                order.cpf,
                order.address,
                order.city,
                order.state,
                order.zip_code,
                order.get_status_display(),
                order.get_payment_method_display(),
                f'{order.shipping_cost:.2f}'.replace('.', ','),
                f'{order.total:.2f}'.replace('.', ','),
                order.user.get_full_name() or order.user.username if order.user else '-',
            ])

        return response