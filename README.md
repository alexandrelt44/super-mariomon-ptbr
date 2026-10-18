# Super Mariomon — tradução PT-BR (protótipo)

Ferramentas para traduzir o *Super Mariomon v1.5.1-Anniversary* (hack de
Pokémon Emerald) para português e distribuir como patch `.bps`.
O ROM não faz parte do repositório.

## Uso

```bash
# catálogo de todos os textos do jogo (≈20 mil strings) com seus ponteiros
python3 tools/extract.py "Sup.Mrmn (v1.5.1-Anniversary).gba" build/textos.json

# gera build/Mariomon-PTBR.gba e build/Mariomon-PTBR.bps
python3 tools/build.py "Sup.Mrmn (v1.5.1-Anniversary).gba"
```

## Como traduzir

Cada arquivo em `traducao/*.json` é uma lista de entradas copiadas de
`build/textos.json`:

```json
{"offset": "02E846D", "en": "So you're {PLAYER}, eh?\\p...", "pt": "Então você é {PLAYER}, é?\\p..."}
```

- `\n` quebra a linha, `\l` rola para a próxima linha, `\p` abre nova caixa.
- Parágrafos escritos sem `\n`/`\l` são quebrados automaticamente em 208 px
  (largura da caixa de diálogo). Linhas mais largas que isso falham no build.
- Tags como `{PLAYER}`, `{PAUSE 60}`, `{COLOR 02}` devem ser mantidas.
- `max_width` (opcional) muda o limite para menus.
- Acentos disponíveis: á à â ã é ê í ó ô õ ú ç (e maiúsculas). ã õ Ã Õ não
  existem na fonte original; o build desenha esses glifos nas 4 fontes.

O build confere se o `en` bate com o ROM, então um patch para outra versão do
jogo falha em vez de corromper o arquivo. Textos que cabem no espaço original
são escritos no lugar; os maiores vão para o espaço livre do ROM (≈12 MB) e
todos os ponteiros são atualizados.

## Estado atual

Tradução completa do texto do jogo: 18.562 entradas, cobrindo 96% dos
caracteres do catálogo. Ficam em inglês, de propósito: nomes de CAPTURAS e
de personagens, palavras do Easy Chat (usadas nas frases secretas), nomes de
lugares de Hoenn, o menu de depuração, nomes de músicas do teste de som e
textos em imagem ("PRESS START", botões da tela de nome).

Organização:
- `traducao/nomes/`: tabelas de tamanho fixo (itens, golpes, habilidades, tipos);
- `traducao/00_*` a `02_*`: lugares, intro, menus e configuração;
- `traducao/mapas/` e `traducao/lotes/`: diálogos e textos de sistema;
- `traducao/glossario.md` e `traducao/guia.md`: termos e regras;
- `traducao/revisao.md`: pontos para revisão humana.

Fluxo de manutenção: `tools/padronizar.py` (grafias finais),
`tools/consistencia.py --fix` (falas repetidas) e `tools/build.py`.

## Teste no emulador

`tools/emulador/remote.lua` é carregado no mGBA (Tools > Scripting) e lê
comandos de botão (`A`, `START`, `UP*20` para segurar, `SAVESTATE`/`LOADSTATE`) de `$MARIOMON_REMOTE_DIR/cmd.txt` (padrão
`/tmp/mariomon-remote`), salvando a tela após cada lote. Útil para conferir
textos sem jogar manualmente.
