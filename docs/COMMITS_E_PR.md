# Roteiro de commits e Pull Request

Sugestão de histórico semântico (rode na pasta do projeto, depois de `git init` e de
conectar o repositório do GitHub). Cada bloco é um commit.

```bash
git checkout -b feat/mvp-agendamento

git add .gitignore README.md requirements.txt pytest.ini conftest.py
git commit -m "chore: estrutura inicial do projeto, dependências e README"

git add config manage.py agenda/apps.py agenda/__init__.py config/__init__.py
git commit -m "feat(config): configuração Django com segredos em variáveis de ambiente (RNF02)"

git add agenda/services.py tests/test_services.py tests/__init__.py
git commit -m "feat(agenda): regra de horários livres, conflito e validação de telefone (RF01, RF02)"

git add agenda/models.py agenda/admin.py
git commit -m "feat(models): Barbeiro, Servico, Cliente e Agendamento com unicidade barbeiro+horário"

git add agenda/forms.py agenda/views.py agenda/urls.py agenda/templates
git commit -m "feat(views): telas de escolher, confirmar, resultado, cancelar e painel (RF01-RF04, RAC01)"

git add tests/conftest.py tests/test_models.py tests/test_views.py
git commit -m "test: testes de integração de agendamento, cancelamento, painel e login (RNF01, RNF02)"

git add .github
git commit -m "ci: pipeline com checagem de migrações, testes e cobertura mínima de 80%"
```

Antes do commit de modelos, rode `python manage.py makemigrations agenda` e inclua a
pasta `agenda/migrations/` no commit de modelos.

Depois: `git push -u origin feat/mvp-agendamento`, abra o Pull Request no GitHub para a
`main`, faça a auto-revisão (comentários nas linhas que decidiu explicar) e só então
faça o merge.

## Modelo de descrição do Pull Request

**Título:** feat: MVP de agendamento online da Barbearia Brutos

**O que muda:** fluxo do cliente (escolher, confirmar, resultado, cancelar) e painel do
barbeiro com login.

**Requisitos atendidos:** RF01, RF02, RF03, RF04, RNF01, RNF02, RAC01.

**Como testar:** `pytest --cov=agenda` e o passo a passo do README.

**Auto-revisão:** conferi que a regra de overbooking tem duas camadas (checagem de
conflito com trava de linha e restrição única no banco), que a senha usa PBKDF2 e que o
nome digitado é escapado na saída. Limitação conhecida: horário de funcionamento fixo
em configuração e sem lembrete automático (RF05).
