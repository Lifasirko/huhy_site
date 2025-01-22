from django.shortcuts import render, get_object_or_404

from .models import BlogPost, Tag


def blog_list(request):
    posts = BlogPost.objects.all()
    tags = Tag.objects.all()
    search_query = request.GET.get('q', '')
    selected_tag = request.GET.get('tag', '')

    if search_query:
        posts = posts.filter(title__icontains=search_query)
    if selected_tag:
        posts = posts.filter(tags__slug=selected_tag)

    return render(request, 'blog_list.html', {'posts': posts, 'tags': tags})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    related_posts = BlogPost.objects.filter(tags__in=post.tags.all()).exclude(id=post.id)[:5]
    return render(request, 'blog_detail.html', {'post': post, 'related_posts': related_posts})
