from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginate_page
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


@cache_page(20, key_prefix='index_page')
def index(request):
    query_set = Post.objects.select_related('author', 'group').all()
    context = {
        'page_obj': paginate_page(query_set, request),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post = group.group_posts.select_related('author').all()
    query_set = group.group_posts.select_related('author').all()
    context = {
        'group': group,
        'posts': post,
        'page_obj': paginate_page(query_set, request),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    query_set = author.author_posts.select_related('group').all()
    context = {
        'author': author,
        'page_obj': paginate_page(query_set, request),
        'following':
            request.user.is_authenticated
            and request.user != author
            and Follow.objects.filter(author=author,
                                      user=request.user).exists(),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.all(),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_edit(request, post_id):
    posts = get_object_or_404(Post, id=post_id)
    if request.user != posts.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=posts)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', new_post.author.username)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    query_set = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': paginate_page(query_set, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.username == username:
        return redirect('posts:index')
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=request.user, author=author).exists():
        return redirect('posts:index')
    follower = Follow()
    follower.author = author
    follower.user = request.user
    follower.save()
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return redirect('posts:index')
