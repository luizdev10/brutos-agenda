# Brutos Agenda

MVP de agendamento online para a Barbearia Brutos. Resolve a agenda desorganizada e o
overbooking: o cliente vê só os horários livres do barbeiro e confirma pelo celular, sem
instalar aplicativo. O barbeiro consulta o painel do dia depois de fazer login.

Projeto da disciplina de Projeto de Software (Experiência Prática 3).

## Funcionalidades (requisitos)

| Código | Descrição |
|---|---|
| RF01 | Consultar horários livres por serviço, barbeiro e dia |
| RF02 | Confirmar agendamento com nome e telefone |
| RF03 | Cancelar agendamento (exige o telefone cadastrado) |
| RF04 | Painel do dia do barbeiro (com login) |
| RNF01 | Senha com PBKDF2-SHA256, sessão segura e bloqueio após 5 falhas |
| RNF02 | Validação no servidor, ORM, saída escapada, segredos em variáveis de ambiente |
| RAC01 | Botões de 44 px, rótulos visíveis, erros e status em texto e símbolo |

RF05 (lembrete automático) é desejável e fica fora desta versão.

## Tecnologias

Python 3.12, Django 5.2 LTS (MVT), PostgreSQL em produção (SQLite só em testes locais),
Bootstrap 5.3, pytest + pytest-django.

## Estrutura

- `agenda/services.py`: regras de agenda em Python puro (horários livres, conflito, telefone).
- `agenda/models.py`: Barbeiro, Servico, Cliente, Agendamento (com restrição de unicidade).
- `agenda/views.py`, `forms.py`, `templates/`: telas e fluxo.
- `tests/`: testes unitários (`test_services.py`) e de integração (`test_models.py`, `test_views.py`).
- `.github/workflows/ci.yml`: pipeline de integração contínua.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DJANGO_DEBUG=1                                # Windows PowerShell: $env:DJANGO_DEBUG="1"
python manage.py makemigrations agenda
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Cadastre serviços e barbeiros em `/admin/` (associe a conta do barbeiro ao cadastro dele
para ele ver o painel em `/painel/`). A tela do cliente fica em `/`.

## Testes

```bash
pytest --cov=agenda --cov-report=term-missing
```

## Variáveis de ambiente

| Variável | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | obrigatória fora do modo de desenvolvimento |
| `DJANGO_DEBUG` | `1` apenas em desenvolvimento |
| `DJANGO_ALLOWED_HOSTS` | hosts separados por vírgula |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | banco PostgreSQL |

## Dados de teste

Todos os dados usados em exemplos e testes são fictícios.
