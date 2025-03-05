from django.contrib import admin
from django.http import HttpResponse
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.html import format_html
import os
import io
import zipfile

from .models import Category, Product, Pack, ProductImage, Order, OrderItem, Tag

User = get_user_model()


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
            'discount_active',
            'discount_percent',
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
            'discount_active',
            'discount_percent',
        )
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        if not row.get('slug') and row.get('name'):
            row['slug'] = slugify(row['name'])

    def get_instance(self, instance_loader, row):
        if not row.get('id'):
            return None
        return super().get_instance(instance_loader, row)


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


class ProductCompletenessFilter(admin.SimpleListFilter):
    title = "Заповненість картки товару"
    parameter_name = 'completeness'

    def lookups(self, request, model_admin):
        return (
            ('complete', 'Повна'),
            ('incomplete', 'Неповна'),
        )

    def queryset(self, request, queryset):
        complete_q = Q(image__isnull=False) & ~Q(image="") & ~Q(description="") & Q(price__gt=0)
        if self.value() == 'complete':
            return queryset.filter(complete_q)
        if self.value() == 'incomplete':
            return queryset.exclude(complete_q)
        return queryset


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource
    list_display = ('name', 'slug', 'parent')
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ('id', 'name', 'slug', 'price', 'stock', 'available', 'created', 'updated', 'view_on_site_link')
    list_filter = (ProductCompletenessFilter, 'available', 'created', 'updated', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {"slug": ("name",)}
    actions = ['download_images_archive']

    def view_on_site_link(self, obj):
        return format_html('<a href="{}" target="_blank">Переглянути</a>', obj.get_absolute_url())

    view_on_site_link.short_description = "На сайті"

    def download_images_archive(self, request, queryset):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for product in queryset:
                if product.image:
                    try:
                        file_path = product.image.path
                        file_extension = os.path.splitext(file_path)[1]
                        file_name = f"product_{product.id}_main{file_extension}"
                        zip_file.write(file_path, arcname=file_name)
                    except Exception:
                        pass
                for idx, prod_image in enumerate(product.images.all(), start=1):
                    if prod_image.image:
                        try:
                            file_path = prod_image.image.path
                            file_extension = os.path.splitext(file_path)[1]
                            file_name = f"product_{product.id}_image_{idx}{file_extension}"
                            zip_file.write(file_path, arcname=file_name)
                        except Exception:
                            pass
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=product_images.zip'
        return response

    download_images_archive.short_description = "Завантажити зображення товарів як архів"


@admin.register(ProductImage)
class ProductImageAdmin(ImportExportModelAdmin):
    resource_class = ProductImageResource
    list_display = ('product', 'caption')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource
    list_display = ('id', 'full_name', 'phone', 'payment_method', 'delivery_method', 'status', 'created')
    list_filter = ('status', 'payment_method', 'delivery_method')
    search_fields = ('full_name', 'phone', 'address')
    inlines = [OrderItemInline]


admin.site.register(Tag)


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ('product', 'components_list', 'get_total_price', 'auto_price', 'product_info')
    filter_horizontal = ('components',)
    readonly_fields = ('product_info',)
    fieldsets = (
        (None, {
            'fields': ('product_info', 'auto_price', 'components'),
        }),
    )

    def components_list(self, obj):
        return ", ".join([p.name for p in obj.components.all()])

    components_list.short_description = "Компоненти паку"

    def get_total_price(self, obj):
        return obj.product.price

    get_total_price.short_description = "Розрахункова ціна паку"

    def product_info(self, obj):
        info = f"<strong>Назва:</strong> {obj.product.name}<br>"
        info += f"<strong>Опис:</strong> {obj.product.description}<br>"
        info += f"<strong>Ціна (редагована):</strong> {obj.product.price} грн<br>"
        if obj.product.image:
            info += f'<img src="{obj.product.image.url}" style="max-height:100px;"/><br>'
        return format_html(info)

    product_info.short_description = "Інформація про товар-пак"
