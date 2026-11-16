import os

# Ambiente de testes: segredo fixo e modo de desenvolvimento (sem HTTPS forçado).
os.environ.setdefault("DJANGO_SECRET_KEY", "chave-de-teste")
os.environ.setdefault("DJANGO_DEBUG", "1")
