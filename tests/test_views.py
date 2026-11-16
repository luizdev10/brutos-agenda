from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from agenda.models import Agendamento, Cliente


def _dados(servico, barbeiro, inicio, nome="Marcos Teste", telefone="(11) 90000-0000"):
    return {
        "servico": servico.pk, "barbeiro": barbeiro.pk,
        "inicio": inicio.strftime("%Y-%m-%dT%H:%M"), "nome": nome, "telefone": telefone,
    }


def test_tela_escolher_lista_horarios_livres(client, servico, barbeiro):
    dia = timezone.localdate() + timedelta(days=1)
    r = client.get(reverse("escolher"), {"servico": servico.pk, "barbeiro": barbeiro.pk, "dia": dia.isoformat()})
    assert r.status_code == 200
    assert "10:00" in r.content.decode()


def test_agendamento_valido_e_confirmado(client, servico, barbeiro, amanha_10h):
    r = client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h))
    assert r.status_code == 302
    ag = Agendamento.objects.get()
    assert ag.status == Agendamento.Status.CONFIRMADO
    assert ag.cliente.telefone == "11900000000"


def test_segundo_agendamento_no_mesmo_horario_e_recusado(client, servico, barbeiro, amanha_10h):
    client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h))
    r = client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h, "Outro Cliente", "(11) 91111-1111"))
    assert r.status_code == 409
    assert Agendamento.objects.count() == 1


def test_horario_ocupado_some_da_lista(client, servico, barbeiro, amanha_10h):
    client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h))
    r = client.get(reverse("escolher"), {
        "servico": servico.pk, "barbeiro": barbeiro.pk, "dia": amanha_10h.date().isoformat()})
    assert "T10:00" not in r.content.decode()


def test_telefone_invalido_mostra_erro_em_texto_e_nao_grava(client, servico, barbeiro, amanha_10h):
    r = client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h, telefone="(11) 9000"))
    assert r.status_code == 200
    assert "Digite o telefone com DDD" in r.content.decode()
    assert Agendamento.objects.count() == 0


def test_script_digitado_no_nome_e_escapado_na_saida(client, servico, barbeiro, amanha_10h):
    client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h, nome="<script>alert(1)</script>"))
    ag = Agendamento.objects.get()
    r = client.get(reverse("resultado", args=[ag.pk]))
    assert "<script>alert(1)</script>" not in r.content.decode()


def test_nao_agenda_no_passado(client, servico, barbeiro):
    passado = timezone.now() - timedelta(days=1)
    r = client.post(reverse("confirmar"), _dados(servico, barbeiro, passado))
    assert r.status_code == 409
    assert Agendamento.objects.count() == 0


def test_cancelar_exige_telefone_correto(client, servico, barbeiro, amanha_10h):
    client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h))
    ag = Agendamento.objects.get()
    errado = client.post(reverse("cancelar", args=[ag.pk]), {"telefone": "(11) 98888-8888"})
    ag.refresh_from_db()
    assert errado.status_code == 200 and ag.status == Agendamento.Status.CONFIRMADO
    client.post(reverse("cancelar", args=[ag.pk]), {"telefone": "(11) 90000-0000"})
    ag.refresh_from_db()
    assert ag.status == Agendamento.Status.CANCELADO


def test_horario_cancelado_volta_a_ficar_livre(client, servico, barbeiro, amanha_10h):
    client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h))
    ag = Agendamento.objects.get()
    client.post(reverse("cancelar", args=[ag.pk]), {"telefone": "11900000000"})
    r = client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h, "Outro", "(11) 91111-1111"))
    assert r.status_code == 302


def test_painel_exige_login(client):
    r = client.get(reverse("painel"))
    assert r.status_code == 302 and "/entrar/" in r["Location"]


def test_barbeiro_ve_somente_a_propria_agenda(client, servico, barbeiro, usuario_barbeiro, amanha_10h):
    from agenda.models import Barbeiro
    outro = Barbeiro.objects.create(nome="Outro Barbeiro")
    cliente = Cliente.objects.create(nome="Cliente do Outro", telefone="11911111111")
    Agendamento.objects.create(cliente=cliente, barbeiro=outro, servico=servico, inicio=amanha_10h)
    client.force_login(usuario_barbeiro)
    r = client.get(reverse("painel"), {"dia": amanha_10h.date().isoformat()})
    assert r.status_code == 200
    assert "Cliente do Outro" not in r.content.decode()


def test_login_bloqueia_apos_cinco_falhas(client, usuario_barbeiro):
    from django.core.cache import cache
    cache.clear()
    for _ in range(5):
        client.post(reverse("login"), {"username": "rafael", "password": "errada"})
    r = client.post(reverse("login"), {"username": "rafael", "password": "senha-bem-longa-123"})
    assert r.status_code == 429


def test_senha_e_guardada_com_hash_pbkdf2(usuario_barbeiro):
    assert usuario_barbeiro.password.startswith("pbkdf2_sha256$")


def test_nao_cancela_atendimento_ja_concluido(client, servico, barbeiro, amanha_10h):
    client.post(reverse("confirmar"), _dados(servico, barbeiro, amanha_10h))
    ag = Agendamento.objects.get()
    ag.status = Agendamento.Status.CONCLUIDO
    ag.save()
    r = client.post(reverse("cancelar", args=[ag.pk]), {"telefone": "11900000000"})
    ag.refresh_from_db()
    assert r.status_code == 200 and ag.status == Agendamento.Status.CONCLUIDO
    assert "não pode mais ser cancelado" in r.content.decode()
