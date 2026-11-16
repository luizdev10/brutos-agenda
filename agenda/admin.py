from django.contrib import admin

from .models import Agendamento, Barbeiro, Cliente, Servico

admin.site.register(Barbeiro)
admin.site.register(Servico)
admin.site.register(Cliente)


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("inicio", "barbeiro", "cliente", "servico", "status")
    list_filter = ("status", "barbeiro")
