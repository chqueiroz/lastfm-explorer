# LastFM Explorer

Sistema de recomendação de artistas baseado no histórico de scrobbles de usuários do Last.fm.

## Status

Projeto em desenvolvimento.

Atualmente o sistema possui uma interface CLI funcional e gera recomendações de artistas inéditos a partir do histórico musical do usuário.

## Como funciona

O recomendador utiliza:

- histórico de scrobbles do Last.fm;
- tags dos artistas;
- TF-IDF para construção do perfil musical;
- ponderação temporal dos scrobbles;
- artistas similares fornecidos pelo Last.fm;
- compatibilidade entre as tags dos candidatos e o perfil do usuário.

A versão atual do modelo utiliza:

- meia-vida dos scrobbles de 180 dias;
- 30% de peso para similaridade do Last.fm;
- 70% de peso para compatibilidade das tags.

## Estrutura

- `api.py` — comunicação com a API Last.fm
- `database.py` — banco SQLite e sincronização dos dados
- `preprocessing.py` — normalização das tags e construção do perfil
- `recommender.py` — lógica de recomendação
- `cli.py` — interface de terminal
- `main.py` — fluxo principal da aplicação
- `notebooks/` — experimentos e desenvolvimento do modelo

## Próximos passos

- desenvolvimento de dashboard;
- melhoria da experiência de uso;
- documentação final;
- testes adicionais.