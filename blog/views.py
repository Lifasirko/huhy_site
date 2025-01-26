from django.shortcuts import render, get_object_or_404

from .models import BlogPost, Tag
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Кешування на 15 хвилин
def blog_list(request):
    # posts = BlogPost.objects.all()
    posts = BlogPost.objects.prefetch_related('tags').all()
    tags = Tag.objects.all()

    # Пошук за назвою
    search_query = request.GET.get('q', '').strip()
    if search_query:
        posts = posts.filter(title__icontains=search_query)

    # Фільтрація за тегами
    selected_tag_slug = request.GET.get('tag', '').strip()
    if selected_tag_slug:
        posts = posts.filter(tags__slug=selected_tag_slug)

    return render(request, 'blog_list.html', {
        'posts': posts,
        'tags': tags,
        'search_query': search_query,
        'selected_tag_slug': selected_tag_slug,
    })


@cache_page(60 * 15)  # Кешування на 15 хвилин
def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    related_posts = BlogPost.objects.filter(tags__in=post.tags.all()).exclude(id=post.id)[:5]
    return render(request, 'blog_detail.html', {'post': post, 'related_posts': related_posts})
