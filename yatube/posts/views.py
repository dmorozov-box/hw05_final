from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

MAX_POSTS = 10


def index(request):
    posts = Post.objects.select_related('author', 'group')
    paginator = Paginator(posts, MAX_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Последние обновления на сайте',
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')

    paginator = Paginator(posts, MAX_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': f'Записи сообщества "{group.title}"',
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    author_posts_count = posts.count()

    paginator = Paginator(posts, MAX_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    following = False
    if request.user.is_authenticated:
        if author.following.filter(user=request.user).count():
            following = True

    context = {
        'page_obj': page_obj,
        'author': author,
        'author_posts_count': author_posts_count,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author_posts_count = post.author.posts.count()
    comments = post.comments.all()
    context = {
        'post': post,
        'author_posts_count': author_posts_count,
        'form': CommentForm(request.POST or None),
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required()
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    template = 'posts/create_post.html'

    if request.method != 'POST':
        return render(request, template, {'form': form, 'is_edit': False})

    if not form.is_valid():
        return render(request, template, {'form': form, 'is_edit': False})

    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect(
        'posts:profile', username=request.user.username
    )


@login_required()
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    template = 'posts/create_post.html'

    if request.method != 'POST':
        return render(request, template, {'form': form, 'is_edit': True})

    if not form.is_valid():
        return render(request, template, {'form': form, 'is_edit': True})

    form.save()
    return redirect('posts:post_detail', post_id=post_id)


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
    posts = Post.objects.filter(author__following__user=request.user)

    paginator = Paginator(posts, MAX_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'title': 'Последние обновления на сайте - подписки',
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
