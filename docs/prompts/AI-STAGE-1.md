# IFBA OS — ETAPA 1/5
## Arquitetura, autenticação, contas individuais e segurança

Você é o engenheiro principal responsável pelo desenvolvimento do IFBA OS, uma distribuição Linux educacional baseada no Ubuntu 24.04 e XFCE4.

Repositório:
`/Users/leonardo/Documents/IFBA-OS`

Branch obrigatório: `development`.

### MISSÃO

Inspecione o projeto existente e implemente a infraestrutura necessária para um assistente de inteligência artificial integrado ao sistema operacional, com contas individuais, configurações próprias e isolamento seguro dos dados.

Não crie um aplicativo que simule o sistema operacional.

O XFCE4 continuará sendo o ambiente gráfico principal.

### 1. INSPEÇÃO INICIAL

Antes de modificar arquivos:

1. Leia `AGENTS.md`.
2. Examine a arquitetura e a documentação existente.
3. Inspecione scripts de construção da ISO.
4. Identifique o sistema de usuários atual.
5. Examine a configuração do LightDM, PAM e systemd.
6. Verifique os recursos existentes do assistente de IA.
7. Identifique código reutilizável.
8. Examine o estado do Git.
9. Preserve alterações locais preexistentes.

Não reimplemente funcionalidades já existentes sem justificativa.

### 2. ARQUITETURA DO ASSISTENTE

Projete os seguintes componentes:

- `ifba-ai-daemon`: serviço principal da IA.
- `ifba-ai-ui`: interface gráfica GTK.
- `ifba-screen-agent`: integração com aplicativos e tela.
- `ifba-overlay`: destaque de elementos visuais.
- `ifba-memory`: armazenamento de contexto.
- `ifba-ai-settings`: configurações individuais.

Defina contratos entre os componentes, preferencialmente utilizando D-Bus para comunicação local.

Utilize Python como linguagem principal, salvo se a arquitetura existente justificar outra escolha.

Não introduza microsserviços ou tecnologias desnecessárias.

### 3. CONTAS INDIVIDUAIS

Utilize inicialmente as contas locais do Linux como identidade principal.

Cada estudante deverá possuir:

- Diretório pessoal.
- Configurações próprias.
- Chave NVIDIA própria.
- Histórico próprio.
- Memória própria.
- Preferências individuais.
- Permissões individuais.

Não confunda autenticação Linux com autenticação de uma futura conta online.

Não implemente um backend remoto de contas sem necessidade nesta etapa.

### 4. SEGURANÇA DAS CHAVES

Implemente integração com Secret Service/libsecret.

Requisitos:

- Nunca armazenar a chave NVIDIA em texto puro nos arquivos de configuração.
- Nunca incluir chaves reais no repositório ou na ISO.
- Nunca registrar chaves nos logs.
- Permitir adicionar, substituir e remover a chave.
- Utilizar o cofre de credenciais do usuário.
- Tratar indisponibilidade ou bloqueio do cofre.
- Não criar fallback inseguro.
- Não permitir que outro usuário comum acesse a chave.

A interface deverá informar claramente quando a chave não estiver configurada.

### 5. ARMAZENAMENTO INDIVIDUAL

Crie a estrutura local:

`~/.local/share/ifba-ai/`

`~/.config/ifba-ai/`

Utilize os diretórios XDG adequados.

Prepare o armazenamento SQLite para:

- Conversas.
- Configurações não sensíveis.
- Memória.
- Preferências.
- Metadados educacionais.

Implemente permissões restritivas e migrações de esquema.

Não armazene credenciais no SQLite.

### 6. SERVIÇO POR USUÁRIO

Prepare a inicialização do assistente através de um serviço systemd de usuário, quando adequado.

Requisitos:

- Não executar como root.
- Não depender de um daemon global privilegiado.
- Iniciar somente na sessão apropriada.
- Encerrar corretamente.
- Recuperar-se de falhas.
- Não bloquear a inicialização do XFCE4.
- Não abrir uma janela desnecessariamente.

### 7. CONFIGURAÇÃO INICIAL

Prepare uma interface GTK para a primeira configuração do assistente.

Ela deverá permitir:

- Informar chave NVIDIA.
- Escolher modelo compatível.
- Ativar ou desativar memória.
- Consultar informações de privacidade.
- Configurar posteriormente.
- Alterar configurações depois.

O sistema operacional deve funcionar normalmente mesmo sem chave de API.

### 8. TESTES

Implemente testes para:

- Separação de usuários.
- Permissões de arquivos.
- Persistência.
- Migrações SQLite.
- Falha do cofre de credenciais.
- Ausência de chave.
- Inicialização do serviço.
- Tratamento de erros.

Não use chaves reais nos testes.

### 9. LOOP ENGINEERING

Execute continuamente:

INSPECIONAR → PLANEJAR → IMPLEMENTAR → TESTAR → CORRIGIR → VALIDAR → DOCUMENTAR → COMMITAR.

Após cada ciclo:

1. Identifique a próxima tarefa prioritária.
2. Implemente uma unidade funcional.
3. Execute testes.
4. Corrija falhas.
5. Atualize o roadmap.
6. Registre evidências.
7. Faça commit quando apropriado.
8. Continue para a próxima tarefa.

Não encerre após criar apenas documentação ou classes vazias.

Não utilize mocks como substitutos da funcionalidade final. Mocks são permitidos em testes isolados.

Não repita tentativas sem novas evidências.

### 10. GIT

Trabalhe somente no branch `development`.

Configure localmente:

`git config --local user.name "Leonardo de Almeida Silva"`

`git config --local user.email "nardocontapc1234@gmail.com"`

Antes de cada commit, verifique explicitamente autor e committer efetivos, incluindo possíveis variáveis de ambiente que sobrescrevam a configuração.

Não use a identidade Git de outra pessoa.

Não reescreva commits antigos.

Não faça force push.

Use Conventional Commits.

Faça push somente para `origin/development` quando autorizado e seguro.

### 11. DOCUMENTAÇÃO

Crie ou atualize:

- `docs/ARCHITECTURE.md`
- `docs/AI-ASSISTANT.md`
- `docs/SECURITY.md`
- `docs/PROJECT-ROADMAP.md`
- `docs/DEVELOPMENT-LOOP.md`

Registre decisões técnicas e limitações reais.

### CRITÉRIOS DE ACEITAÇÃO

- [ ] Arquitetura implementada e documentada.
- [ ] Serviço individual preparado.
- [ ] Configuração GTK funcional.
- [ ] Cofre de credenciais integrado.
- [ ] SQLite individual funcionando.
- [ ] Dados isolados entre usuários.
- [ ] Testes automatizados passando.
- [ ] Nenhuma chave exposta.
- [ ] Roadmap atualizado.
- [ ] Commits com identidade correta.

Implemente de verdade, valide e continue os ciclos até concluir o escopo ou encontrar um bloqueio verificável.