from datetime import date, datetime, time

import pytest

from agenda import services


ABERTURA, FECHAMENTO = time(9, 0), time(12, 0)


def test_dia_vazio_oferece_todos_os_horarios_de_30_min():
    livres = services.horarios_livres(ABERTURA, FECHAMENTO, [], 30)
    assert livres == [time(9, 0), time(9, 30), time(10, 0), time(10, 30), time(11, 0), time(11, 30)]


def test_horario_ocupado_nao_e_oferecido():
    livres = services.horarios_livres(ABERTURA, FECHAMENTO, [(time(10, 0), 30)], 30)
    assert time(10, 0) not in livres
    assert time(9, 30) in livres and time(10, 30) in livres


def test_servico_longo_nao_pode_invadir_horario_ocupado():
    # Corte + barba (60 min) às 9:30 invadiria o atendimento das 10:00.
    livres = services.horarios_livres(ABERTURA, FECHAMENTO, [(time(10, 0), 30)], 60)
    assert time(9, 30) not in livres
    assert time(9, 0) in livres  # termina às 10:00, encostando sem sobrepor
    assert time(10, 30) in livres


def test_atendimento_existente_longo_bloqueia_todos_os_seus_blocos():
    livres = services.horarios_livres(ABERTURA, FECHAMENTO, [(time(9, 0), 60)], 30)
    assert time(9, 0) not in livres and time(9, 30) not in livres
    assert time(10, 0) in livres


def test_servico_nao_pode_ultrapassar_o_fechamento():
    livres = services.horarios_livres(ABERTURA, FECHAMENTO, [], 60)
    assert time(11, 0) in livres
    assert time(11, 30) not in livres


def test_duracao_nao_multipla_do_passo_ocupa_bloco_extra():
    assert services.blocos_necessarios(45) == 2
    assert services.blocos_necessarios(30) == 1


def test_duracao_invalida_levanta_erro():
    with pytest.raises(ValueError):
        services.blocos_necessarios(0)


def test_conflita_detecta_sobreposicao_parcial():
    existente = [(datetime(2026, 11, 22, 10, 0), 30)]
    assert services.conflita(datetime(2026, 11, 22, 9, 45), 30, existente)
    assert services.conflita(datetime(2026, 11, 22, 10, 0), 30, existente)
    assert services.conflita(datetime(2026, 11, 22, 10, 15), 30, existente)


def test_conflita_permite_horarios_encostados():
    existente = [(datetime(2026, 11, 22, 10, 0), 30)]
    assert not services.conflita(datetime(2026, 11, 22, 9, 30), 30, existente)
    assert not services.conflita(datetime(2026, 11, 22, 10, 30), 30, existente)


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("(11) 90000-0000", "11900000000"),
        ("11 90000-0000", "11900000000"),
        ("+55 11 90000-0000", "11900000000"),
        ("(11) 3000-0000", "1130000000"),
    ],
)
def test_telefone_valido_e_normalizado(entrada, esperado):
    assert services.normalizar_telefone(entrada) == esperado


@pytest.mark.parametrize("entrada", ["", "(11) 9000", "90000-0000", "(11) 80000-0000", "(05) 90000-0000", "abc"])
def test_telefone_invalido_levanta_erro(entrada):
    with pytest.raises(ValueError):
        services.normalizar_telefone(entrada)


def test_formatar_telefone():
    assert services.formatar_telefone("11900000000") == "(11) 90000-0000"
    assert services.formatar_telefone("1130000000") == "(11) 3000-0000"


def test_nao_agenda_no_passado():
    hoje = date(2026, 11, 22)
    assert services.dia_valido(date(2026, 11, 22), hoje)
    assert not services.dia_valido(date(2026, 11, 21), hoje)
