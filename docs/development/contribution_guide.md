# Guia de Contribuição

Obrigado pelo interesse em contribuir com o projeto Sentinel! Este guia explica como você pode participar e ajudar a melhorar o sistema.

## Código de Conduta

Este projeto e todos os participantes estão sob um Código de Conduta. Ao participar, espera-se que você respeite este código. Por favor, reporte comportamentos inaceitáveis.

## Como Posso Contribuir?

### Reportando Bugs

Os bugs são rastreados como issues no GitHub. Antes de criar um novo bug:

1. Verifique se o bug já não foi reportado
2. Certifique-se de que está usando a versão mais recente
3. Verifique a seção de Troubleshooting na documentação

Ao reportar um bug, inclua:

- Título claro e descritivo
- Passos exatos para reproduzir o problema
- Comportamento esperado versus comportamento observado
- Capturas de tela, logs ou mensagens de erro
- Versões relevantes (Sentinel, Docker, Python, MikroTik RouterOS, Zabbix)
- Ambiente (sistema operacional, configurações)

### Sugerindo Melhorias

As sugestões também são rastreadas como issues no GitHub. Ao sugerir melhorias:

1. Use um título claro e descritivo
2. Forneça uma descrição detalhada da melhoria proposta
3. Explique por que essa melhoria seria útil para a maioria dos usuários
4. Forneça exemplos de como a funcionalidade poderia ser usada
5. Liste quaisquer funcionalidades semelhantes em outros projetos, se relevante

### Pull Requests

1. Crie uma fork do repositório
2. Clone sua fork localmente
3. Configure o ambiente de desenvolvimento conforme o [Guia de Desenvolvimento](development_guide.md)
4. Crie uma branch para sua feature ou correção:
   ```bash
   git checkout -b feature/nome-da-feature
   # ou
   git checkout -b fix/nome-do-bug
   ```
5. Implemente suas alterações, seguindo as convenções de código
6. Adicione ou atualize testes automatizados
7. Execute os testes localmente: `pytest`
8. Atualize a documentação se necessário
9. Commit suas alterações:
   ```bash
   git commit -m "Descrição clara das alterações"
   ```
10. Push para sua fork:
    ```bash
    git push origin feature/nome-da-feature
    ```
11. Abra um Pull Request para o repositório original

## Convenções de Estilo e Codificação

### Python

- Siga [PEP 8](https://www.python.org/dev/peps/pep-0008/) para formatação de código
- Use [docstrings estilo Google](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) para documentação
- Use tipos anotados (type hints) para parâmetros e retornos de funções
- Limite o comprimento das linhas a 88 caracteres (compatível com black)
- Use nomes descritivos para variáveis, funções e classes
- Escreva código modular e testável

### Commits

- Use mensagens de commit claras e descritivas
- Prefixe as mensagens com o tipo de alteração:
  - `feat`: Nova funcionalidade
  - `fix`: Correção de bug
  - `docs`: Alterações na documentação
  - `style`: Formatação, ponto-e-vírgula faltando, etc; sem alteração de código
  - `refactor`: Refatoração de código
  - `test`: Adição ou correção de testes
  - `chore`: Atualizações de tarefas de build, configurações, etc; sem alteração de código

Exemplo: `feat: Adiciona suporte a traceroute`

### Branches

- `main`: Branch principal, sempre estável
- `develop`: Branch de desenvolvimento, para funcionalidades em andamento
- `feature/nome-da-feature`: Para novas funcionalidades
- `fix/nome-do-bug`: Para correções de bugs
- `docs/nome-da-documentacao`: Para atualizações de documentação
- `refactor/descricao`: Para refatorações de código

## Processo de Desenvolvimento

### Ciclo de Vida das Issues

1. **Aberta**: Uma nova issue foi criada
2. **Confirmada**: O problema ou funcionalidade foi confirmado e aceito
3. **Em Progresso**: Alguém está trabalhando ativamente na issue
4. **Revisão**: A implementação está pronta e aguardando revisão
5. **Feedback**: É necessária mais ação do contribuidor
6. **Resolvida**: A issue foi resolvida e fechada

### Revisão de Código

Todos os Pull Requests passam por revisão de código. Durante a revisão:

1. O código é avaliado quanto à funcionalidade e estilo
2. Os testes automatizados são verificados
3. A documentação é revisada
4. O CI/CD executa verificações automatizadas

Para que um PR seja aprovado, ele deve:

- Passar em todos os testes automatizados
- Seguir as convenções de estilo
- Ter documentação atualizada
- Estar alinhado com os objetivos do projeto
- Ter sido revisado e aprovado por pelo menos um mantenedor

## Configuração de Ambiente para Desenvolvimento

Veja instruções detalhadas no [Guia de Desenvolvimento](development_guide.md).

## Executando Testes

O projeto usa o framework pytest. Para executar os testes:

```bash
# Instale as dependências de desenvolvimento
pip install -r requirements-dev.txt

# Execute todos os testes
pytest

# Execute testes com cobertura
pytest --cov=app

# Execute testes específicos
pytest tests/test_auth.py
```

## Documentação

A documentação é tão importante quanto o código. Ao contribuir:

- Atualize a documentação para quaisquer alterações de API ou funcionalidade
- Adicione exemplos para novas funcionalidades
- Mantenha os guias atualizados com alterações relevantes
- Documente quaisquer decisões ou tradeoffs importantes

## Recursos Adicionais

- [Guia de Desenvolvimento](development_guide.md)
- [Arquitetura do Sistema](../architecture/system_architecture.md)
- [Guia de Troubleshooting](../guides/troubleshooting.md)
- [Documentação do FastAPI](https://fastapi.tiangolo.com/)
- [Documentação da API MikroTik](https://wiki.mikrotik.com/wiki/Manual:API)
- [Documentação do Zabbix](https://www.zabbix.com/documentation/current/)

## Contato

Se tiver dúvidas ou precisar de ajuda para começar:

- Abra uma issue no GitHub
- Entre em contato com os mantenedores do projeto: [email@example.com]

Agradecemos suas contribuições!