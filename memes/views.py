from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import Notification

from .forms import MemeCommentForm, MemeForm
from .models import REPLY_PREFIX_RE, Meme, MemeComment, MemeVote


def _render_meme_feed(
    request,
    *,
    form=None,
    form_open=False,
    open_comments_id=None,
    invalid_comment_form=None,
):
    """Общая отрисовка ленты мемов с голосами и комментариями."""
    sort = 'top' if request.GET.get('sort') == 'top' else 'new'
    if form is None:
        form = MemeForm()

    if open_comments_id is None:
        raw_comments_id = request.GET.get('comments', '')
        if raw_comments_id.isdigit():
            open_comments_id = int(raw_comments_id)

    memes_qs = (
        Meme.objects.published()
        .with_score()
        .select_related('author')
        .prefetch_related('comments__author')
    )
    if sort == 'top':
        memes_qs = memes_qs.order_by('-score', '-created_at')
    else:
        memes_qs = memes_qs.order_by('-created_at')

    memes = list(memes_qs)
    user_votes = {}
    if request.user.is_authenticated and memes:
        user_votes = dict(
            MemeVote.objects.filter(
                user=request.user,
                meme_id__in=[meme.pk for meme in memes],
            ).values_list('meme_id', 'value')
        )
    for meme in memes:
        meme.user_vote = user_votes.get(meme.pk, 0)
        meme.comment_list = list(meme.comments.all())
        meme.comment_count = len(meme.comment_list)
        if invalid_comment_form is not None and meme.pk == open_comments_id:
            meme.comment_form = invalid_comment_form
        else:
            meme.comment_form = MemeCommentForm(auto_id=f'id_meme_{meme.pk}_%s')

    return render(request, 'memes/meme_list.html', {
        'memes': memes,
        'sort': sort,
        'form': form,
        'form_open': form_open,
        'open_comments_id': open_comments_id,
    })


def meme_list(request):
    """Лента опубликованных мемов с сортировкой «Новые / Топ» и формой загрузки."""
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        form = MemeForm(request.POST, request.FILES)
        if form.is_valid():
            meme = form.save(commit=False)
            meme.author = request.user
            meme.is_published = False
            meme.save()
            messages.success(request, 'Мем отправлен на модерацию и появится после проверки')
            return redirect('memes:list')
        return _render_meme_feed(request, form=form, form_open=True)

    return _render_meme_feed(request)


@login_required
@require_POST
def meme_vote(request, pk):
    """Голосование за мем стрелочками: +1 (апвоут) или -1 (даунвоут)."""
    meme = get_object_or_404(Meme.objects.published(), pk=pk)
    raw_value = request.POST.get('value')
    if raw_value not in ('1', '+1', '-1'):
        return HttpResponseBadRequest('Некорректное значение голоса.')

    target_value = 1 if raw_value in ('1', '+1') else -1
    existing = MemeVote.objects.filter(meme=meme, user=request.user).first()

    if existing is None:
        MemeVote.objects.create(meme=meme, user=request.user, value=target_value)
        user_vote = target_value
    elif existing.value == target_value:
        # Повторное нажатие на ту же стрелку отменяет голос
        existing.delete()
        user_vote = 0
    else:
        # Переключение между апвоутом и даунвоутом
        existing.value = target_value
        existing.save(update_fields=['value'])
        user_vote = target_value

    score = Meme.objects.with_score().get(pk=meme.pk).score

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'score': score, 'user_vote': user_vote})

    return redirect('memes:list')


@login_required
@require_POST
def meme_delete(request, pk):
    """Удаление собственного мема автором."""
    meme = get_object_or_404(Meme, pk=pk, author=request.user)
    if meme.image:
        meme.image.delete(save=False)
    meme.delete()
    messages.success(request, 'Мем удалён')
    return redirect('memes:list')


def _notify_on_comment(meme, comment):
    """Создаёт уведомления об ответе на комментарий и о новом комментарии к мему."""
    comment_link = f"{reverse('memes:list')}?comments={meme.pk}#meme-{meme.pk}"
    replied_user = None

    match = REPLY_PREFIX_RE.match(comment.text)
    if match:
        replied_username = match.group(1)
        User = get_user_model()
        replied_user = User.objects.filter(username__iexact=replied_username).first()
        if replied_user and replied_user != comment.author:
            Notification.objects.create(
                recipient=replied_user,
                message=f'{comment.author.username} ответил на ваш комментарий к мему',
                link=comment_link,
            )

    if meme.author != comment.author and meme.author != replied_user:
        Notification.objects.create(
            recipient=meme.author,
            message=f'{comment.author.username} прокомментировал ваш мем',
            link=comment_link,
        )


@login_required
@require_POST
def meme_comment_create(request, pk):
    """Добавление комментария к опубликованному мему."""
    meme = get_object_or_404(Meme.objects.published(), pk=pk)
    form = MemeCommentForm(request.POST, auto_id=f'id_meme_{meme.pk}_%s')
    if form.is_valid():
        comment = form.save(commit=False)
        comment.meme = meme
        comment.author = request.user
        comment.save()
        _notify_on_comment(meme, comment)
        messages.success(request, 'Комментарий опубликован')
        return redirect(f"{reverse('memes:list')}?comments={meme.pk}")

    return _render_meme_feed(
        request,
        open_comments_id=meme.pk,
        invalid_comment_form=form,
    )


@login_required
@require_POST
def meme_comment_delete(request, pk, comment_pk):
    """Удаление собственного комментария к мему."""
    meme = get_object_or_404(Meme.objects.published(), pk=pk)
    comment = get_object_or_404(
        MemeComment,
        pk=comment_pk,
        meme=meme,
        author=request.user,
    )
    comment.delete()
    messages.success(request, 'Комментарий удалён')
    return redirect(f"{reverse('memes:list')}?comments={meme.pk}")
