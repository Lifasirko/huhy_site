from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Category, Product, Order, OrderItem

# Додано для Telegram-сповіщення
import requests
from django.conf import settings


def send_telegram_message(message: str):
    bot_token = settings.TGBOT_TOKEN
    admin_ids = settings.TELEGRAM_ADMIN_IDS  # Переконайтеся, що цей список заданий у налаштуваннях
    for admin_id in admin_ids:
        try:
            if admin_id is None:
                raise ValueError("TELEGRAM_ADMIN_ID is not set in the environment.")
            admin_id = int(admin_id)
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {"chat_id": admin_id, "text": message}
            response = requests.post(url, data=data)
            response.raise_for_status()  # Перевірка на помилки HTTP
        except ValueError:
            print(f"Невірний ID адміністратора: {admin_id}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to admin {admin_id}: {e}")


class ShopHomeView(TemplateView):
    # Шаблон знаходиться прямо у shop/templates/index.html
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(available=True).order_by('-created')[:8]
        return context


class CatalogView(ListView):
    model = Product
    template_name = 'catalog.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(available=True).order_by('-created')
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = self.object.images.all()
        return context


class CartView(TemplateView):
    template_name = 'cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get('cart', {})
        items = []
        total = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, pk=product_id)
            subtotal = product.price * quantity
            total += subtotal
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
        context['cart_items'] = items
        context['total'] = total
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        cart = self.request.session.get('cart', {})
        if product_id:
            if action == 'add':
                cart[product_id] = cart.get(product_id, 0) + 1
            elif action == 'update':
                quantity = int(request.POST.get('quantity', 1))
                if quantity > 0:
                    cart[product_id] = quantity
                else:
                    cart.pop(product_id, None)
            elif action == 'remove':
                if product_id in cart:
                    del cart[product_id]
        request.session['cart'] = cart
        return redirect('shop:cart')


class CheckoutView(View):
    template_name = 'checkout.html'

    def get(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('shop:cart')
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('shop:cart')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        delivery_method = request.POST.get('delivery_method')
        if not (full_name and phone and address and payment_method and delivery_method):
            return render(request, self.template_name, {'error': 'Будь ласка, заповніть всі поля'})
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            phone=phone,
            address=address,
            payment_method=payment_method,
            delivery_method=delivery_method
        )
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, pk=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )
        # Відправка повідомлення в Telegram адміну з деталями замовлення
        order_items = order.items.all()
        message_lines = [
            f"Нове замовлення #{order.id}",
            f"Ім'я: {order.full_name}",
            f"Телефон: {order.phone}",
            f"Адреса: {order.address}",
            f"Оплата: {order.payment_method}",
            f"Доставка: {order.delivery_method}",
            "Замовлені товари:"
        ]
        for item in order_items:
            product_name = item.product.name if item.product else "Unknown"
            message_lines.append(f"- {product_name}: {item.quantity} шт. за ціною {item.price}")
        message = "\n".join(message_lines)
        send_telegram_message(message)
        request.session['cart'] = {}
        return redirect('shop:order_success')


class OrderSuccessView(TemplateView):
    template_name = 'order_success.html'


class PersonalCabinetView(LoginRequiredMixin, TemplateView):
    template_name = 'personal_cabinet.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = self.request.user.orders.all().order_by('-created')
        return context
