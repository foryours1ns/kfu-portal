from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import MemeForm
from .models import Meme, MemeVote


def meme_list(request):
    """Лента опубликованных мемов с сортировкой «Новые / Топ» и формой загрузки."""
    sort = 'top' if request.GET.get('sort') == 'top' else 'new'
    form_open = False

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
        form_open = True
    else:
        form = MemeForm()

    memes_qs = Meme.objects.published().with_score().select_related('author')
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

    return render(request, 'memes/meme_list.html', {
        'memes': memes,
        'sort': sort,
        'form': form,
        'form_open': form_open,
    })


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
