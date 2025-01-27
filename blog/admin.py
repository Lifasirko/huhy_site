# huhy_site/blog/admin.py

from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ManyToManyWidget
from django.utils.text import slugify
from .models import BlogPost, Tag


class TagResource(resources.ModelResource):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        export_order = ('id', 'name', 'slug')


@admin.register(Tag)
class TagAdmin(ImportExportModelAdmin):
    resource_class = TagResource
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class BlogPostResource(resources.ModelResource):
    tags = fields.Field(
        column_name='tags',
        attribute='tags',
        widget=ManyToManyWidget(Tag, field='name')
    )

    class Meta:
        model = BlogPost
        fields = (
            'id',
            'title',
            'slug',
            'content',
            'main_image',
            'author',
            'published_date',
            'updated_date',
            'tags',
        )
        export_order = (
            'id',
            'title',
            'slug',
            'content',
            'main_image',
            'author',
            'published_date',
            'updated_date',
            'tags',
        )
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('id',)
        # Видалено use_bulk=True, щоб уникнути помилок з bulk_update

    def before_import_row(self, row, **kwargs):
        """
        Автоматично генерує slug, якщо він не вказаний.
        """
        if not row.get('slug'):
            row['slug'] = slugify(row['title'])


@admin.register(BlogPost)
class BlogPostAdmin(ImportExportModelAdmin):
    resource_class = BlogPostResource
    list_display = ('title', 'author', 'published_date')
    search_fields = ('title', 'author', 'content')
    list_filter = ('published_date', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)  # Покращує відображення ManyToManyField у адмінці

    def get_queryset(self, request):
        """
        Оптимізує запити до бази даних, використовуючи prefetch_related.
        """
        return super().get_queryset(request).prefetch_related('tags')
