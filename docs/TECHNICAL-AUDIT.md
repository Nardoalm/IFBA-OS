# Auditoria técnica e de qualidade

**Data:** 2026-11-20 (horário local)
**Revisão auditada:** `b228783795946215f32c7a02f94efdd56e3a2d2f` (`development`)
**Escopo:** boot e systemd, usuários e permissões, serviços, atualizações e dependências, privacidade, ISOs/manifests, AMD64/ARM64 e consumo/estabilidade.

## Resultado executivo

O código-fonte tem controles úteis de privacidade e isolamento dos dados do assistente, e os seis ISOs históricos locais passam a verificação de checksum, tamanho e estrutura de boot. Isso não torna a distribuição pronta para uso público: `latest` ainda combina releases diferentes, a sessão live usa uma conta administrativa compartilhada sem senha, a instalação com Calamares não foi validada e os ISOs atuais não foram inicializados em uma sessão Linux recente para este audit.

Foi corrigida uma falha reproduzível no verificador/publicador de releases: um arquivo de texto com nome `.iso` e manifesto autoconsistente era aceito. O build agora atualiza o rootfs persistente antes de instalar a seleção de pacotes, confirma sua arquitetura e reabre o ISO gerado para validar os arquivos de boot e comparar os metadados embutidos.

## Achados por severidade

### Alta — bloqueios antes de distribuir a imagem atual

1. **A conta live não isola pessoas que compartilham a sessão.** O build cria `ubuntu` no grupo `sudo`, apaga sua senha e configura SDDM para entrar automaticamente nessa conta ([build-iso-container.sh](../scripts/build-iso-container.sh#L93)). O banco e as configurações são privados para outros UIDs, mas todos que usam a sessão live executam sob o mesmo UID e podem acessar esses dados. A configuração do Calamares remove o usuário, o autologin e o sudoers do Casper ao instalar ([shellprocess.conf](../packaging/calamares/shellprocess.conf#L1)); a instalação e a criação de uma nova conta ainda não passaram por teste real. Não armazene dados acadêmicos ou credenciais na sessão live. Resolver isso exige validar o fluxo de contas instalado, não ajustar permissões do mesmo UID.

2. **Não há um par de ISOs da mesma release no `latest`.** A referência ARM64 é v0.3.0, commit `66f71bdac5cc8a08240aa9340627bdfed6095274`; AMD64 é v0.3.1, commit `fe3960ea923108561caf58e0e5ff4bab31fdbd84`. `release-status.json` corretamente mantém `complete_pair: false`; o código-fonte atual está em v0.3.2 e ainda não tem artefatos. Não anuncie essas imagens como uma release pareada ou atual.

3. **O ISO ARM64 v0.3.0 contém alterações de uma árvore suja.** O `build-info.json` extraído da imagem declara `source_dirty: true`; [`ISO-RELEASES.md`](ISO-RELEASES.md) registra que o splash mudou localmente durante o build e não entrou no commit indicado. O SHA identifica as bytes da imagem, mas o commit sozinho não a reproduz. Corrigido para builds futuros: `release_artifacts.publish()` agora recusa manifestos que não declarem `source_dirty: false`. O ISO histórico foi preservado e continua marcado como não reproduzível integralmente a partir do commit.

4. **Instalação e boot de uma instalação persistente continuam pendentes.** A sequência do Calamares configura UEFI, particionamento manual e usuário, mas ainda não houve instalação em disco virtual descartável seguida de reinicialização e login. Os registros de UTM anteriores também não validam a imagem v0.3.2 atual. Logo, a distribuição instalada em computadores pessoais ainda não está demonstrada.

### Média — riscos de atualização e autenticidade

5. **Rootfs em cache podia reter atualizações de segurança.** O build executava `apt-get update`, mas não atualizava todos os pacotes já instalados no rootfs reutilizado antes de instalar a lista explícita. Corrigido: agora executa `apt-get upgrade --with-new-pkgs` sem permitir remoções. Isso reduz pacotes defasados; não torna as versões determinísticas, pois os repositórios `resolute`, `resolute-updates` e `resolute-security` continuam móveis.

6. **Checksum não autenticado não prova origem.** Os manifestos contêm SHA-256 e tamanho, o que detecta corrupção se o manifesto recebido for confiável. Não há assinatura criptográfica do manifesto/ISO no repositório. Quem conseguir substituir ambos pode criar um par que passe na checagem local. É necessário definir e operar uma chave e um canal de assinatura antes da distribuição pública; nenhuma chave foi criada ou incorporada nesta auditoria.

7. **A composição de pacotes não é reproduzível apenas pelo commit.** O build instala versões candidatas atuais do Ubuntu/Mozilla e não registra uma lista completa de versões `dpkg` nem usa um snapshot imutável dos repositórios. O SHA do ISO registra o artefato resultante, mas refazer o build do mesmo commit em outra data pode gerar conteúdo diferente.

8. **Atualização do sistema instalado é manual.** O Discover oferece a interface para atualizações, mas não há política de atualizações automáticas de segurança configurada. O comportamento após uma instalação persistente não foi testado; uma sessão live não mantém as atualizações após reiniciar.

### Baixa — evidência incompleta de desempenho

9. **O consumo em uso real não foi medido.** Há dados históricos de uso alto de CPU durante a compressão de SquashFS, que é custo de build e não desempenho do desktop. Não existe benchmark atual de RAM, CPU em idle, inicialização ou estabilidade em ARM64/AMD64. Não usar esse dado de build para afirmar que a sessão é pesada ou leve.

## Correções implementadas nesta auditoria

- `tools/release_artifacts.py` agora exige ISO 9660, geometria coerente, volume label compatível com série/arquitetura, diretório raiz válido e catálogo El Torito com entradas de boot apropriadas. Também exige entrada UEFI AMD64; ARM64 requer plataforma EFI no catálogo.
- `tools/release_artifacts.py publish` agora recusa artefatos gerados de árvore marcada como suja. A verificação/listagem e preservação dos arquivos históricos ainda permitem identificar a v0.3.0 sem reescrever seu registro.
- `scripts/build-iso-container.sh` atualiza o rootfs em cache, exige que `dpkg` informe a arquitetura solicitada, extrai kernel/initrd/SquashFS/GRUB do ISO recém-gerado e compara o `build-info.json` do SquashFS com os metadados usados no build.
- Os manifestos e bytes históricos não foram editados nem movidos.

## Evidências e validação

- Antes da correção, a reprodução criou um arquivo contendo `not an ISO, but accepted`, gerou um manifesto com o SHA/tamanho correspondentes e `release_artifacts.inspect()` aceitou o arquivo.
- Depois da correção, os testes de regressão rejeitam payload não ISO, rótulo de arquitetura divergente e catálogo AMD64 sem entrada UEFI. Testes de migração/publicação continuam cobrindo preservação de hashes, rejeição de overwrite e atualização de `latest` apenas com pares do mesmo commit.
- `python3 tools/release_artifacts.py list --output output` verificou os seis artefatos históricos. Seus tamanhos e SHA-256 conferem com os manifestos; os descritores ISO 9660/El Torito e rótulos concordam com cada série/arquitetura. O status de runtime de todos permanece `unvalidated`.
- Em contêiner Ubuntu 24.04, `xorriso` extraiu kernel, initrd, SquashFS e `grub.cfg` dos ISOs AMD64 v0.3.1 e ARM64 v0.3.0. `unsquashfs -cat` confirmou os metadados e arquiteturas dos dois; também confirmou que o ARM64 v0.3.0 declara `source_dirty: true`. Isso valida estrutura/conteúdo, não boot de Linux.
- A busca por padrões de chaves encontrou somente `nvapi-example-not-real` nos testes automatizados. O backend usa Secret Service, não tem fallback em texto puro, e persiste configurações/SQLite em diretórios do usuário com modos 0700/0600; estes são resultados de leitura de código/testes, não um teste com cofre real.
- O build de ISO não foi executado: `docs/BUILDING.md` requer 30 GB livres e o host tinha cerca de 4 GB. Nenhum artefato histórico, volume Docker ou disco de VM foi removido ou alterado.

## Cobertura e pendências

| Área | Evidência | Estado |
|---|---|---|
| GRUB/estrutura de boot | Descritores e catálogos dos seis ISOs; um ISO AMD64 extraído por `xorriso` | Estrutura verificada; kernel/initramfs/systemd não iniciados nesta auditoria |
| systemd/serviços | SDDM e NetworkManager ativados pelo build; assistente como serviço systemd de usuário com hardening | `systemd-analyze verify` passou em contêiner Ubuntu 24.04 com D-Bus e executável stub; estado de serviços em guest pendente |
| Usuários/permissões | Conta live, remoção planejada no instalador, diretórios do assistente 0700 e ficheiros 0600 | Fonte/testes; login e isolamento entre contas instaladas pendentes |
| Atualizações/dependências | Repositórios Ubuntu Security/Updates e Mozilla; atualização explícita do rootfs em cache adicionada | Correção de fonte; build real e atualização persistente não executados |
| Privacidade/segredos | Busca em source, testes e inspeção do Secret Service/settings/SQLite | Nenhum segredo real detectado; cofre real não foi exercitado |
| Integridade/manifestos | SHA/tamanho reais e verificação estrutural de seis ISOs; teste reproduzível do falso ISO | Verificado localmente; assinatura de release ausente |
| AMD64/ARM64 | ISOs históricos e catálogos EFI coerentes; imagens pertencem a commits diferentes | Compatibilidade estrutural; novo build/boot pareado pendente |
| Recursos/estabilidade | Sem benchmark do desktop atual | Pendente; só há consumo histórico do build, que não representa runtime |

Nenhuma ISO foi anunciada como boot-testada nesta auditoria. Para liberar, construir o commit auditado em ambas as arquiteturas, gerar um par com manifesto íntegro, instalar/bootar em VMs UEFI descartáveis e testar login, atualizações, serviços, privacidade, reinício e consumo de recursos.
