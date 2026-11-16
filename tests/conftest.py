from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from agenda.models import Barbeiro, Servico


@pytest.fixture
def servico(db):
    return Servico.objects.create(nome="Corte", duracao_min=30, preco=Decimal("40.00"))


@pytest.fixture
def barbeiro(db):
    return Barbeiro.objects.create(nome="Rafael")


@pytest.fixture
def amanha_10h():
    """Amanhã às 10:00, sempre no futuro e dentro do horário de funcionamento."""
    dia = timezone.localdate() + timedelta(days=1)
    return timezone.make_aware(datetime(dia.year, dia.month, dia.day, 10, 0))


@pytest.fixture
def usuario_barbeiro(db, barbeiro):
    User = get_user_model()
    usuario = User.objects.create_user("rafael", password="senha-bem-longa-123")
    barbeiro.usuario = usuario
    barbeiro.save()
    return usuario
