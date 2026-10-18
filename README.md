# Super Mariomon — tradução PT-BR

Tradução para português do Brasil do *Super Mariomon v1.5.1-Anniversary*
(hack de Pokémon Emerald feito com o pokeemerald-expansion), distribuída como
patch `.bps`, e as ferramentas usadas para fazê-la. O ROM não faz parte do
repositório.

*Translating Super Mariomon into another language? See
[For translators](#for-translators-other-languages) below.*

## Aplicar o patch

1. Baixe o `Mariomon-PTBR.bps` na página de
   [releases](../../releases).
2. Tenha o ROM original **Super Mariomon v1.5.1-Anniversary**:
   - CRC32 `0AA91114`
   - SHA-1 `831fe0f97301f17b24a9cd4a64ef0520835c4dde`
3. Aplique com o [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/),
   o Floating IPS (Flips) ou com este repositório:

   ```bash
   python3 tools/bps.py apply "Sup.Mrmn (v1.5.1-Anniversary).gba" Mariomon-PTBR.bps Mariomon-PTBR.gba
   ```

   O patch confere o CRC do ROM de origem e recusa uma versão diferente.

## O que está traduzido

Menus, intro, telas de configuração (dificuldade, Nuzlocke, randomizador),
diálogos de todos os mapas, Tattledex, nomes e descrições de itens, golpes,
habilidades e tipos, mensagens de batalha e textos de sistema: 18.562
textos, cerca de 96% de todo o texto do jogo.

Ficam em inglês, de propósito: nomes de CAPTURAS e de personagens, TM/HM,
bordões do Mario, palavras do Easy Chat (o hack usa frases secretas em
inglês), nomes de lugares de Hoenn, o menu de depuração, nomes de músicas do
teste de som e textos que são imagem ("PRESS START", botões da tela de nome).

Pontos conhecidos para revisão estão em `traducao/revisao.md`. Achou algo
estranho jogando? Abra uma *issue* com o texto e onde ele aparece.

## Gerar o patch a partir do código

```bash
R="Sup.Mrmn (v1.5.1-Anniversary).gba"
python3 tools/extract.py "$R" build/textos.json          # catálogo de textos e ponteiros
python3 tools/maps.py "$R" build/textos.json build/mapas.json   # texto por mapa
python3 tools/tabelas.py "$R" build/tabelas.json          # tabelas de nomes fixas
python3 tools/build.py "$R"                               # build/Mariomon-PTBR.gba e .bps
python3 tools/build.py "$R" --check                       # só valida
```

Antes de um build final: `tools/padronizar.py` (grafias do glossário) e
`tools/consistencia.py --fix` (falas repetidas iguais).

## Como a tradução está organizada

Cada arquivo em `traducao/` é uma lista de entradas:

```json
{"offset": "02E846D", "en": "So you're {PLAYER}, eh?\\p...", "pt": "Então você é {PLAYER}, é?\\p..."}
```

- `\n` quebra a linha, `\l` rola para a próxima linha, `\p` abre nova caixa.
- Parágrafos escritos sem `\n`/`\l` são quebrados automaticamente na largura
  da caixa (208 px nos diálogos).
- Tags `{PLAYER}`, `{STR_VAR_1}`, `{COLOR 02}`, `{FD 10}`... são mantidas.
- `max_width` / `max_lines`: limites de menus e caixas fixas.
- `max_bytes`: tabelas de tamanho fixo (`traducao/nomes/`), gravadas no lugar.

Pastas: `traducao/nomes/` (itens, golpes, habilidades, tipos),
`traducao/00_*`–`02_*` (lugares, intro, menus, configuração),
`traducao/mapas/` e `traducao/lotes/` (diálogos e sistema),
`traducao/glossario.md` e `traducao/guia.md` (termos e regras).

O build recusa traduções que quebrariam o ROM: texto que não bate com o
original, linhas largas demais, fragmentos de outra string (ponteiros
falsos), entradas dentro das tabelas fixas e gravações sobrepostas. Textos
maiores que o original vão para o espaço livre do ROM (≈12 MB) e os
ponteiros são atualizados.

## Teste no emulador

`tools/emulador/remote.lua` é carregado no mGBA (Tools > Scripting) e lê
comandos de botão de `$MARIOMON_REMOTE_DIR/cmd.txt` (padrão
`/tmp/mariomon-remote`): `A`, `START`, `UP*20` (segura 20 quadros),
`SAVESTATE`/`LOADSTATE`, `DUMPWRAM`. Salva a tela após cada lote de comandos.
`tools/mapa_atual.py` diz em que mapa o jogo está a partir do `DUMPWRAM`.

---

## For translators (other languages)

The tools are language-agnostic; only the text files are Portuguese.
To translate Super Mariomon into your language:

1. Run the extraction commands above on your own copy of the v1.5.1
   ROM. `build/textos.json` lists every string the game points to, with its
   ROM offset and pointers; `build/mapas.json` groups them by map so you can
   translate in game order.
2. Reuse the files in `traducao/`: keep `offset` and `en`, and replace the
   `pt` field with your translation (the field is called `pt` in the build;
   just put your language's text in it). Empty `pt` means "keep English" —
   that is how junk entries, Easy Chat words and names are skipped.
   `tools/novo_lote.py`, `tools/gerar_lotes.py` and `tools/preencher.py`
   create batch files and fill them from `{offset: text}` JSON.
3. Characters: the Gen 3 Western font already has À–ü, ñ, ß, œ, ¿ ¡ and
   more (see `tools/gen3text.py`). Missing letters can be drawn into the free
   glyph slots 0x2F–0x32 by `tools/font.py` (we add ã õ Ã Õ by combining the
   tilde of ñ with á/ó). Edit `EXTRA_CHARS` and `RECIPES` for your letters.
4. Run `python3 tools/build.py ROM --check` until it reports no errors, then
   build and test in mGBA.

Things we learned the hard way:
- Keep Easy Chat words (0x82D90F–0x832578) in English: the hack's secret
  questionnaire phrases are typed with them.
- Item, move, ability and type names live in fixed-size fields
  (`tools/tabelas.py`); translations must fit `max_bytes`, and the visible
  limit is usually the menu width (`max_width`).
- Many catalogue entries are false positives (data that decodes as text,
  movement scripts before a line, the tail of another string). The build
  rejects the dangerous ones; when in doubt, leave `pt` empty.
- `traducao/guia.md` describes the batch workflow we used with parallel
  translators; `tools/consistencia.py` keeps repeated lines identical.
