# huhy_site/shop/admin.py

from django.contrib import admin
from django.http import HttpResponse
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from django.utils.text import slugify
from django.contrib.auth import get_user_model
import os
import io
import zipfile

from .models import Category, Product, ProductImage, Order, OrderItem

User = get_user_model()


# Ресурс для категорій
class CategoryResource(resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ForeignKeyWidget(Category, 'name')
    )

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'parent')
        export_order = ('id', 'name', 'slug', 'parent')


# Ресурс для товарів
class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'name')
    )

    class Meta:
        model = Product
        fields = (
            'id',
            'category',
            'name',
            'slug',
            'description',
            'image',
            'price',
            'stock',
            'available',
            'created',
            'updated',
        )
        export_order = (
            'id',
            'category',
            'name',
            'slug',
            'description',
            'image',
            'price',
            'stock',
            'available',
            'created',
            'updated',
        )
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('id',)

    def before_import_row(self, row, **kwargs):
        if not row.get('slug') and row.get('name'):
            row['slug'] = slugify(row['name'])


# Ресурс для зображень товарів
class ProductImageResource(resources.ModelResource):
    product = fields.Field(
        column_name='product',
        attribute='product',
        widget=ForeignKeyWidget(Product, 'name')
    )

    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'image', 'caption')
        export_order = ('id', 'product', 'image', 'caption')
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('id',)


# Ресурс для замовлень
class OrderResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'full_name',
            'phone',
            'address',
            'payment_method',
            'delivery_method',
            'status',
            'created',
            'updated',
        )
        export_order = (
            'id',
            'user',
            'full_name',
            'phone',
            'address',
            'payment_method',
            'delivery_method',
            'status',
            'created',
            'updated',
        )
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('id',)


# Ресурс для позицій замовлення
class OrderItemResource(resources.ModelResource):
    order = fields.Field(
        column_name='order',
        attribute='order',
        widget=ForeignKeyWidget(Order, 'id')
    )
    product = fields.Field(
        column_name='product',
        attribute='product',
        widget=ForeignKeyWidget(Product, 'name')
    )

    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product', 'quantity', 'price')
        export_order = ('id', 'order', 'product', 'quantity', 'price')
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('id',)


# Адміністративне представлення для категорій
@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource
    list_display = ('name', 'slug', 'parent')
    prepopulated_fields = {"slug": ("name",)}


# Адміністративне представлення для товарів
@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ('name', 'slug', 'price', 'stock', 'available', 'created', 'updated')
    list_filter = ('available', 'created', 'updated', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {"slug": ("name",)}
    actions = ['download_images_archive']

    def download_images_archive(self, request, queryset):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for product in queryset:
                # Додаємо головне зображення, якщо воно існує
                if product.image:
                    try:
                        file_path = product.image.path
                        file_extension = os.path.splitext(file_path)[1]
                        file_name = f"product_{product.id}_main{file_extension}"
                        zip_file.write(file_path, arcname=file_name)
                    except Exception as e:
                        pass
                # Додаємо додаткові зображення з ProductImage
                for idx, prod_image in enumerate(product.images.all(), start=1):
                    if prod_image.image:
                        try:
                            file_path = prod_image.image.path
                            file_extension = os.path.splitext(file_path)[1]
                            file_name = f"product_{product.id}_image_{idx}{file_extension}"
                            zip_file.write(file_path, arcname=file_name)
                        except Exception as e:
                            pass
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=product_images.zip'
        return response
    download_images_archive.short_description = "Завантажити зображення товарів як архів"


# Адміністративне представлення для зображень товарів
@admin.register(ProductImage)
class ProductImageAdmin(ImportExportModelAdmin):
    resource_class = ProductImageResource
    list_display = ('product', 'caption')


# Інлайн представлення для позицій замовлення
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


# Адміністративне представлення для замовлень
@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource
    list_display = ('id', 'full_name', 'phone', 'payment_method', 'delivery_method', 'status', 'created')
    list_filter = ('status', 'payment_method', 'delivery_method')
    search_fields = ('full_name', 'phone', 'address')
    inlines = [OrderItemInline]
