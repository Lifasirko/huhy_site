from django.contrib.sitemaps import Sitemap
from .models import BlogPost

class BlogPostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return BlogPost.objects.all()

    def lastmod(self, obj):
        return obj.updated_date if obj.updated_date else obj.published_date
