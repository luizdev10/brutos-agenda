from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from . import services
from .forms import ConfirmarForm
from .models import Agendamento, Barbeiro, Cliente, Servico


def _hora(texto: str) -> time:
    h, m = texto.split(":")
    return time(int(h), int(m))


def _parse_dia(texto: str | None) -> date:
    hoje = timezone.localdate()
    if not texto:
        return hoje
    try:
        dia = date.fromisoformat(texto)
    except ValueError:
        return hoje
    return dia if services.dia_valido(dia, hoje) else hoje


def _agendamentos_do_dia(barbeiro: Barbeiro, dia: date):
    return Agendamento.objects.filter(
        barbeiro=barbeiro, status=Agendamento.Status.CONFIRMADO, inicio__date=dia
    ).select_related("servico")


def _livres(barbeiro: Barbeiro, servico: Servico, dia: date) -> list[time]:
    ocupados = [
        (timezone.localtime(a.inicio).time(), a.servico.duracao_min)
        for a in _agendamentos_do_dia(barbeiro, dia)
    ]
    livres = services.horarios_livres(
        _hora(settings.HORA_ABERTURA), _hora(settings.HORA_FECHAMENTO), ocupados, servico.duracao_min
    )
    if dia == timezone.localdate():
        agora = timezone.localtime().time()
        livres = [h for h in livres if h > agora]
    return livres


def escolher(request):
    """Tela 1: escolher serviço, barbeiro, dia e horário livre (RF01)."""
    servicos = Servico.objects.all()
    barbeiros = Barbeiro.objects.filter(ativo=True)
    dia = _parse_dia(request.GET.get("dia"))
    servico = servicos.filter(pk=request.GET.get("servico") or 0).first()
    barbeiro = barbeiros.filter(pk=request.GET.get("barbeiro") or 0).first()

    horarios = []
    if servico and barbeiro:
        horarios = [datetime.combine(dia, h).strftime("%Y-%m-%dT%H:%M") for h in _livres(barbeiro, servico, dia)]
        horarios = [(h, h[-5:]) for h in horarios]

    return render(
        request,
        "agenda/escolher.html",
        {
            "servicos": servicos,
            "barbeiros": barbeiros,
            "servico": servico,
            "barbeiro": barbeiro,
            "dia": dia,
            "hoje": timezone.localdate(),
            "horarios": horarios,
        },
    )


def _contexto_confirmacao(request):
    servico = get_object_or_404(Servico, pk=request.GET.get("servico") or request.POST.get("servico") or 0)
    barbeiro = get_object_or_404(Barbeiro, pk=request.GET.get("barbeiro") or request.POST.get("barbeiro") or 0, ativo=True)
    bruto = request.GET.get("inicio") or request.POST.get("inicio") or ""
    try:
        inicio = timezone.make_aware(datetime.strptime(bruto, "%Y-%m-%dT%H:%M"))
    except ValueError:
        raise Http404("Horário inválido.")
    return servico, barbeiro, inicio


@require_http_methods(["GET", "POST"])
def confirmar(request):
    """Tela 2: confirmar o agendamento com nome e telefone (RF02)."""
    servico, barbeiro, inicio = _contexto_confirmacao(request)
    form = ConfirmarForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                # Trava a linha do barbeiro para que dois pedidos simultâneos
                # sejam processados um de cada vez (evita overbooking).
                Barbeiro.objects.select_for_update().get(pk=barbeiro.pk)
                existentes = [
                    (a.inicio, a.servico.duracao_min)
                    for a in _agendamentos_do_dia(barbeiro, timezone.localtime(inicio).date())
                ]
                if inicio <= timezone.now() or services.conflita(inicio, servico.duracao_min, existentes):
                    return render(request, "agenda/resultado.html", {"recusado": True}, status=409)

                cliente, _ = Cliente.objects.update_or_create(
                    telefone=form.cleaned_data["telefone"],
                    defaults={"nome": form.cleaned_data["nome"]},
                )
                agendamento = Agendamento.objects.create(
                    cliente=cliente, barbeiro=barbeiro, servico=servico, inicio=inicio
                )
        except IntegrityError:
            return render(request, "agenda/resultado.html", {"recusado": True}, status=409)
        return redirect("resultado", pk=agendamento.pk)

    return render(
        request,
        "agenda/confirmar.html",
        {"form": form, "servico": servico, "barbeiro": barbeiro, "inicio": inicio,
         "inicio_iso": inicio.strftime("%Y-%m-%dT%H:%M")},
    )


def resultado(request, pk):
    """Tela 3 (cliente): resultado do agendamento."""
    agendamento = get_object_or_404(Agendamento.objects.select_related("cliente", "servico", "barbeiro"), pk=pk)
    return render(request, "agenda/resultado.html", {"agendamento": agendamento})


@require_http_methods(["GET", "POST"])
def cancelar(request, pk):
    """RF03: cancelar exige o telefone cadastrado no agendamento."""
    agendamento = get_object_or_404(Agendamento.objects.select_related("cliente", "servico"), pk=pk)
    erro = ""
    if request.method == "POST" and agendamento.status != Agendamento.Status.CONFIRMADO:
        erro = "Este agendamento não pode mais ser cancelado."
    elif request.method == "POST":
        try:
            telefone = services.normalizar_telefone(request.POST.get("telefone", ""))
        except ValueError as e:
            telefone, erro = "", str(e)
        if telefone and telefone == agendamento.cliente.telefone:
            agendamento.status = Agendamento.Status.CANCELADO
            agendamento.save(update_fields=["status"])
            return redirect("resultado", pk=agendamento.pk)
        erro = erro or "Telefone não confere com o do agendamento."
    return render(request, "agenda/cancelar.html", {"agendamento": agendamento, "erro": erro})


@login_required
def painel(request):
    """Tela 3 (barbeiro): painel do dia (RF04). Cada barbeiro vê só a própria agenda."""
    barbeiro = Barbeiro.objects.filter(usuario=request.user).first()
    if barbeiro is None and not request.user.is_superuser:
        raise Http404("Usuário sem barbeiro associado.")
    try:
        dia = date.fromisoformat(request.GET.get("dia", ""))
    except ValueError:
        dia = timezone.localdate()

    consulta = Agendamento.objects.filter(inicio__date=dia).select_related("cliente", "servico", "barbeiro")
    if barbeiro is not None:
        consulta = consulta.filter(barbeiro=barbeiro)
    return render(request, "agenda/painel.html", {"agendamentos": consulta, "dia": dia, "barbeiro": barbeiro})


class LoginComBloqueio(LoginView):
    """RNF01: bloqueio temporário após 5 falhas seguidas, com mensagem genérica."""

    template_name = "registration/login.html"

    def _chave(self, request):
        usuario = (request.POST.get("username") or "").strip().lower()
        return f"login-falhas:{usuario}"

    def post(self, request, *args, **kwargs):
        if cache.get(self._chave(request), 0) >= settings.LOGIN_MAX_FALHAS:
            form = self.get_form()
            form.add_error(None, "Muitas tentativas. Aguarde alguns minutos e tente de novo.")
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        chave = self._chave(self.request)
        cache.set(chave, cache.get(chave, 0) + 1, settings.LOGIN_BLOQUEIO_SEGUNDOS)
        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(self._chave(self.request))
        return super().form_valid(form)
