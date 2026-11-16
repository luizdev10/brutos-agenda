"""Regras de negócio da agenda, sem dependência do Django.

Mantidas em Python puro para serem testadas de forma rápida e isolada
(RF01: consultar horários livres; RF02: impedir overbooking).
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime, time, timedelta

PASSO_MINUTOS = 30


def _minutos(t: time) -> int:
    return t.hour * 60 + t.minute


def _para_time(minutos: int) -> time:
    return time(minutos // 60, minutos % 60)


def blocos_necessarios(duracao_min: int, passo: int = PASSO_MINUTOS) -> int:
    """Quantos blocos de agenda um serviço ocupa (arredonda para cima)."""
    if duracao_min <= 0:
        raise ValueError("A duração do serviço deve ser positiva.")
    return math.ceil(duracao_min / passo)


def horarios_livres(
    abertura: time,
    fechamento: time,
    agendamentos: list[tuple[time, int]],
    duracao_min: int,
    passo: int = PASSO_MINUTOS,
) -> list[time]:
    """Devolve os horários de início livres para um serviço de `duracao_min`.

    `agendamentos` é uma lista de (hora_de_inicio, duracao_em_minutos) já
    confirmados para o barbeiro no dia. Um horário só é livre se o serviço
    inteiro couber antes do fechamento e sem tocar em outro agendamento.
    """
    necessarios = blocos_necessarios(duracao_min, passo)
    inicio_dia, fim_dia = _minutos(abertura), _minutos(fechamento)

    ocupados: set[int] = set()
    for inicio, duracao in agendamentos:
        base = _minutos(inicio)
        for i in range(blocos_necessarios(duracao, passo)):
            ocupados.add(base + i * passo)

    livres = []
    for comeco in range(inicio_dia, fim_dia, passo):
        if comeco + necessarios * passo > fim_dia:
            break
        blocos = [comeco + i * passo for i in range(necessarios)]
        if not any(b in ocupados for b in blocos):
            livres.append(_para_time(comeco))
    return livres


def conflita(
    novo_inicio: datetime,
    nova_duracao: int,
    existentes: list[tuple[datetime, int]],
) -> bool:
    """True se o novo agendamento se sobrepõe a algum já confirmado."""
    novo_fim = novo_inicio + timedelta(minutes=nova_duracao)
    for inicio, duracao in existentes:
        fim = inicio + timedelta(minutes=duracao)
        if novo_inicio < fim and inicio < novo_fim:
            return True
    return False


_NAO_DIGITO = re.compile(r"\D")


def normalizar_telefone(valor: str) -> str:
    """Valida um telefone brasileiro com DDD e devolve só os dígitos.

    Aceita 10 dígitos (fixo) ou 11 (celular, começando com 9 após o DDD).
    """
    digitos = _NAO_DIGITO.sub("", valor or "")
    if digitos.startswith("55") and len(digitos) in (12, 13):
        digitos = digitos[2:]
    if len(digitos) not in (10, 11):
        raise ValueError("Digite o telefone com DDD, por exemplo 11 90000-0000.")
    ddd = int(digitos[:2])
    if ddd < 11:
        raise ValueError("DDD inválido.")
    if len(digitos) == 11 and digitos[2] != "9":
        raise ValueError("Celular deve começar com 9 após o DDD.")
    return digitos


def formatar_telefone(digitos: str) -> str:
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"


def dia_valido(dia: date, hoje: date) -> bool:
    """Não se agenda no passado."""
    return dia >= hoje
