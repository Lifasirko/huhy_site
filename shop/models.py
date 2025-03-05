from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Назва тегу")

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Назва категорії")
    slug = models.SlugField(unique=True, verbose_name="URL slug")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Батьківська категорія"
    )

    class Meta:
        verbose_name_plural = "Категорії"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name="Категорія"
    )
    name = models.CharField(max_length=255, verbose_name="Назва товару")
    slug = models.SlugField(unique=True, verbose_name="URL slug")
    description = models.TextField(blank=True, verbose_name="Опис товару")
    image = models.ImageField(
        upload_to='shop/products/',
        blank=True,
        null=True,
        verbose_name="Головне зображення"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    stock = models.PositiveIntegerField(default=0, verbose_name="Кількість на складі")
    available = models.BooleanField(default=True, verbose_name="Доступний")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    tags = models.ManyToManyField(Tag, blank=True, related_name='products', verbose_name="Теги")
    # Поля для знижки
    discount_active = models.BooleanField(default=False, verbose_name="Активна знижка")
    discount_percent = models.PositiveIntegerField(default=0, verbose_name="Відсоток знижки")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('shop:product_detail', kwargs={'slug': self.slug})

    @property
    def discounted_price(self):
        if self.discount_active and self.discount_percent > 0:
            return self.price * (100 - self.discount_percent) / 100
        return self.price

    # Додано для визначення чи товар є бандлом
    @property
    def is_bundle(self):
        return hasattr(self, 'pack_details')

    # Додано для отримання компонентів бандлу
    @property
    def bundle_components(self):
        if hasattr(self, 'pack_details'):
            return self.pack_details.components.all()
        return Product.objects.none()


# Модель паку (бандлу)
class Pack(models.Model):
    # Товар, який представляє пак – створюється окремо в Product
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='pack_details',
        verbose_name="Товар-пак"
    )
    # Компоненти паку
    components = models.ManyToManyField(
        Product,
        related_name='included_in_packs',
        verbose_name="Компоненти паку"
    )
    # Автооновлення ціни за замовчуванням
    auto_price = models.BooleanField(default=True, verbose_name="Автооновлення ціни")

    def __str__(self):
        return f"Pack: {self.product.name}"

    def update_price(self):
        if self.auto_price:
            total = sum([p.price for p in self.components.all()])
            self.product.price = total
            self.product.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_price()


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Товар"
    )
    image = models.ImageField(upload_to='shop/products/', verbose_name="Зображення")
    caption = models.CharField(max_length=255, blank=True, null=True, verbose_name="Підпис")

    def __str__(self):
        return f"Image for {self.product.name}"


class Order(models.Model):
    PAYMENT_CHOICES = (
        ('online', 'Онлайн-оплата'),
        ('cash', 'Готівка'),
    )
    DELIVERY_CHOICES = (
        ('nova_poshta', 'Нова Пошта'),
        ('pickup', 'Самовивіз'),
    )
    STATUS_CHOICES = (
        ('new', 'Нове'),
        ('processing', 'В обробці'),
        ('shipped', 'Відправлено'),
        ('completed', 'Виконано'),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Користувач"
    )
    full_name = models.CharField(max_length=255, verbose_name="Ім'я")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.TextField(verbose_name="Адреса")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, verbose_name="Спосіб оплати")
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, verbose_name="Спосіб доставки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    def __str__(self):
        return f"Order {self.id} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Замовлення"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Unknown'}"
