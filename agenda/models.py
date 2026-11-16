from django.conf import settings
from django.db import models
from django.db.models import Q


class Barbeiro(models.Model):
    nome = models.CharField(max_length=80)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Conta de login do barbeiro (painel do dia).",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Servico(models.Model):
    nome = models.CharField(max_length=60)
    duracao_min = models.PositiveSmallIntegerField()
    preco = models.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.duracao_min} min)"


class Cliente(models.Model):
    # Minimização de dados: apenas nome e telefone (sem CPF/endereço).
    nome = models.CharField(max_length=80)
    telefone = models.CharField(max_length=11, unique=True)

    def __str__(self):
        return self.nome


class Agendamento(models.Model):
    class Status(models.TextChoices):
        CONFIRMADO = "confirmado", "Confirmado"
        CANCELADO = "cancelado", "Cancelado"
        CONCLUIDO = "concluido", "Concluído"
        FALTOU = "faltou", "Faltou"

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="agendamentos")
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name="agendamentos")
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT)
    inicio = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CONFIRMADO)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["inicio"]
        constraints = [
            # Última barreira contra overbooking: um barbeiro não tem dois
            # agendamentos confirmados começando no mesmo instante.
            models.UniqueConstraint(
                fields=["barbeiro", "inicio"],
                condition=Q(status="confirmado"),
                name="unico_barbeiro_horario_confirmado",
            ),
        ]

    def __str__(self):
        return f"{self.cliente} - {self.servico.nome} - {self.inicio:%d/%m %H:%M}"
