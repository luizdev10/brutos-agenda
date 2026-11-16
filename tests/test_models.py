import pytest
from django.db import IntegrityError, transaction

from agenda.models import Agendamento, Cliente


@pytest.fixture
def cliente(db):
    return Cliente.objects.create(nome="Marcos Teste", telefone="11900000000")


def test_banco_impede_dois_confirmados_no_mesmo_horario(cliente, barbeiro, servico, amanha_10h):
    Agendamento.objects.create(cliente=cliente, barbeiro=barbeiro, servico=servico, inicio=amanha_10h)
    with pytest.raises(IntegrityError), transaction.atomic():
        Agendamento.objects.create(cliente=cliente, barbeiro=barbeiro, servico=servico, inicio=amanha_10h)


def test_horario_de_agendamento_cancelado_pode_ser_reutilizado(cliente, barbeiro, servico, amanha_10h):
    Agendamento.objects.create(
        cliente=cliente, barbeiro=barbeiro, servico=servico, inicio=amanha_10h,
        status=Agendamento.Status.CANCELADO,
    )
    Agendamento.objects.create(cliente=cliente, barbeiro=barbeiro, servico=servico, inicio=amanha_10h)
    assert Agendamento.objects.count() == 2


def test_cliente_guarda_apenas_nome_e_telefone():
    campos = {f.name for f in Cliente._meta.get_fields()}
    assert campos == {"id", "nome", "telefone", "agendamentos"}
