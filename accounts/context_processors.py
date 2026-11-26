MAX_RECENT_NOTIFICATIONS = 15


def notifications(request):
    """Передаёт в базовый шаблон последние уведомления и счётчик непрочитанных."""
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
        }

    qs = request.user.notifications.all()
    return {
        'unread_notifications_count': qs.filter(is_read=False).count(),
        'recent_notifications': list(qs[:MAX_RECENT_NOTIFICATIONS]),
    }
