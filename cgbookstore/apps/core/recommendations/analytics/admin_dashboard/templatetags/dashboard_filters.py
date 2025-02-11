from django import template
import calendar
import locale

register = template.Library()


@register.filter(name='get_weekday_name')
def get_weekday_name(weekday_number):
    """
    Converte um número de dia da semana para seu nome localizado.

    Args:
        weekday_number (int): Dia da semana (0-6, onde 0 é segunda-feira)

    Returns:
        str: Nome localizado do dia da semana
    """
    try:
        # Tenta definir a localização para português do Brasil
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        except locale.Error:
            # Fallback para configuração padrão se pt_BR não estiver disponível
            locale.setlocale(locale.LC_TIME, '')

        # Converte o número para um inteiro
        weekday_number = int(weekday_number)

        # Obtém o nome do dia da semana
        # calendar.day_name usa domingo como 0, então ajustamos
        dias = list(calendar.day_name)
        dias = dias[1:] + [dias[0]]  # Move domingo para o final

        return dias[weekday_number].capitalize()
    except (ValueError, IndexError):
        # Retorna o valor original se a conversão falhar
        return str(weekday_number)


@register.filter
def duration_format(duration):
    """
    Formata timedelta para exibição amigável
    """
    if not duration:
        return "N/A"

    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}min"
    return f"{minutes}min"