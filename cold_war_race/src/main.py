import pygame, time, sys, os
import math
from settings import WIDTH, HEIGHT, FPS, FINISH_LINE, MS_TO_PROGRESS, MAX_TETRIS_ADV_PCT
from tetris_phase import tetris_phase
from rocket_race import RocketRace
from end_screen import end_screen

def compute_advantage(times):
    urss = times["URSS_ms"]
    eua  = times["EUA_ms"]
    # limita a vantagem a no máximo 25% da pista para dar chance ao adversário
    capped_pct = min(MAX_TETRIS_ADV_PCT, 0.15)
    adv_cap = int(capped_pct * FINISH_LINE)
    diff = abs(urss - eua)
    diff_progress = min(adv_cap, int(diff * MS_TO_PROGRESS))
    if urss < eua:
        return diff_progress, 0  # URSS vantagem
    elif eua < urss:
        return 0, diff_progress  # EUA vantagem
    else:
        return 0, 0

# -------------------------
# Texto utilitário (mantido)
# -------------------------
def wrap_text(text, font, max_width):
    """Quebra texto em linhas que caibam em max_width usando medidas do font."""
    lines = []
    for paragraph in text.splitlines():  # respeita quebras manuais (\n)
        if paragraph.strip() == "":
            lines.append("")
            continue
        words = paragraph.split(' ')
        cur = ""
        for word in words:
            test = cur + (" " if cur else "") + word
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines

def show_text_screen(screen, title_text, body_text):
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("Arial", 36, bold=True)
    body_font = pygame.font.SysFont("Arial", 20)
    btn_font = pygame.font.SysFont("Arial", 20, bold=True)
    back_rect = pygame.Rect(20, HEIGHT-60, 120, 40)

    # prepare wrapped lines
    max_w = min(WIDTH - 120, 900)
    lines = wrap_text(body_text, body_font, max_w)
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if back_rect.collidepoint(ev.pos):
                    return  # volta ao menu

        mouse_pos = pygame.mouse.get_pos()
        screen.fill((10, 14, 30))
        # title
        title_s = title_font.render(title_text, True, (255, 215, 0))
        screen.blit(title_s, (WIDTH//2 - title_s.get_width()//2, 40))
        # body
        x = WIDTH//2 - max_w//2
        y = 110
        line_h = body_font.get_linesize()
        for line in lines:
            line_s = body_font.render(line, True, (230,230,230))
            screen.blit(line_s, (x, y))
            y += line_h

        # back button
        pygame.draw.rect(screen, (60,60,70) if back_rect.collidepoint(mouse_pos) else (40,40,50), back_rect, border_radius=6)
        back_s = btn_font.render("Voltar", True, (240,240,240))
        screen.blit(back_s, (back_rect.x + (back_rect.width-back_s.get_width())//2, back_rect.y + (back_rect.height-back_s.get_height())//2))

        pygame.display.flip()
        clock.tick(60)

# -------------------------
# CUTSCENES: sistema de diálogo (nova implementação)
# -------------------------
def _show_dialogue_generic(screen, dialogues, bg_image=None, typing_speed_chars_per_sec=120):
    """
    Mostra diálogos com imagens estáticas (uma por vez).
    Caixa do narrador menor e nome dentro da caixa.
    Se o diálogo tem imagem (terceiro item), ela é usada; caso contrário, usa fundo escuro.
    """
    pygame.font.init()
    name_font = pygame.font.SysFont("Arial", 22, bold=True)   # menor para caber dentro da caixa
    text_font = pygame.font.SysFont("Arial", 22)
    hint_font = pygame.font.SysFont("Arial", 16)
    clock = pygame.time.Clock()

    box_margin = 48
    box_h = 140  # caixa menor
    box_rect = pygame.Rect(box_margin, HEIGHT - box_margin - box_h, WIDTH - 2*box_margin, box_h)
    chars_per_ms = typing_speed_chars_per_sec / 1000.0  # chars per ms

    def simple_fade(prev_surf, next_surf, duration_ms=420):
        """Crossfade rápido entre imagens; se prev for None faz fade-in next."""
        start = pygame.time.get_ticks()
        while True:
            now = pygame.time.get_ticks()
            t = now - start
            frac = min(1.0, t / max(1, duration_ms))

            if prev_surf:
                screen.blit(prev_surf, (0,0))
            else:
                screen.fill((6,8,18))

            if next_surf:
                tmp = next_surf.copy()
                tmp.set_alpha(int(255 * frac))
                screen.blit(tmp, (0,0))

            pygame.display.flip()
            clock.tick(FPS)
            if frac >= 1.0:
                break

        if next_surf:
            screen.blit(next_surf, (0,0))
        else:
            screen.fill((6,8,18))
        pygame.display.flip()

    prev_bg = None
    for entry in dialogues:
        # support (speaker, text) or (speaker, text, bg_surface)
        if len(entry) == 3:
            speaker, text, dlg_bg = entry
        else:
            speaker, text = entry
            dlg_bg = bg_image

        # se a imagem mudou, faz fade simples (mostra uma por vez)
        if dlg_bg is not prev_bg:
            simple_fade(prev_bg, dlg_bg, duration_ms=420)
            prev_bg = dlg_bg

        # prepara texto
        typed_chars = 0
        wrapped_lines = wrap_text(text, text_font, box_rect.width - 30)
        total_chars = sum(len(line) for line in wrapped_lines)
        finished = False
        last_tick = pygame.time.get_ticks()

        while True:
            now = pygame.time.get_ticks()
            dt = now - last_tick
            last_tick = now

            advance = False
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if not finished:
                            typed_chars = total_chars
                            finished = True
                        else:
                            advance = True
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if not finished:
                        typed_chars = total_chars
                        finished = True
                    else:
                        advance = True

            if advance:
                break

            if not finished:
                typed_chars += int(dt * chars_per_ms)
                if typed_chars >= total_chars:
                    typed_chars = total_chars
                    finished = True

            # fundo: imagem estática por diálogo (se houver) ou fundo escuro
            if dlg_bg:
                screen.blit(dlg_bg, (0,0))
            elif bg_image:
                screen.blit(bg_image, (0,0))
            else:
                screen.fill((6,8,18))

            # escurece levemente para legibilidade (mantém imagem visível)
            overlay = pygame.Surface((WIDTH, HEIGHT), flags=pygame.SRCALPHA)
            overlay.fill((0,0,0,100))
            screen.blit(overlay, (0,0))

            # caixa de diálogo menor, nome DENTRO da caixa (top-left)
            pygame.draw.rect(screen, (245,245,245), box_rect, border_radius=10)
            pygame.draw.rect(screen, (30,30,30), box_rect, 2, border_radius=10)

            # nome do orador dentro da caixa
            name_surf = name_font.render(speaker, True, (18,18,18))
            name_pos = (box_rect.x + 12, box_rect.y + 8)
            screen.blit(name_surf, name_pos)

            # texto com typing começando abaixo do nome
            text_start_y = box_rect.y + 8 + name_surf.get_height() + 6
            remaining = typed_chars
            y = text_start_y
            for line in wrapped_lines:
                if remaining <= 0:
                    break
                if remaining >= len(line):
                    to_draw = line
                else:
                    to_draw = line[:remaining]
                txt_s = text_font.render(to_draw, True, (20,20,20))
                screen.blit(txt_s, (box_rect.x + 12, y))
                y += text_font.get_linesize()
                remaining -= len(line)

            # hint abaixo da caixa
            hint = "Espaço/Enter ou clique para avançar"
            hint_s = hint_font.render(hint, True, (200,200,200))
            screen.blit(hint_s, (WIDTH//2 - hint_s.get_width()//2, box_rect.y + box_rect.height + 10))

            pygame.display.flip()
            clock.tick(FPS)
    # fim for dialogues



def show_story_cutscene(screen):
    """
    Carrega as imagens estáticas diretamente de assets/sprites (cutscene_1..6)
    e empacota cada fala com sua imagem, mostrando uma por vez.
    Corrige o caminho para a pasta assets (uma subida a partir de src).
    """
    dialogues = [
        ("Narrador", "Anos 1950–60 — a Guerra Fria transforma avanços científicos em símbolo de poder."),
        ("Narrador", "Estados Unidos e União Soviética competiam por supremacia tecnológica e prestígio."),
        ("Narrador", "A corrida espacial tornou-se palco dessa rivalidade: satélites, missões e a ambição de chegar à Lua."),
        ("Narrador", "Neste jogo, a montagem do foguete representa a engenharia e rapidez de cada lado."),
        ("Narrador", "Peças bem colocadas significam um foguete mais preparado — e uma vantagem na corrida."),
        ("Narrador", "Prepare-se: monte seu foguete com cuidado. Quando estiver pronto, a corrida começa.")
    ]

    # caminho CORRIGIDO: assets está uma pasta acima de src
    assets_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
    sprites_dir = os.path.join(assets_dir, "sprites")
    dlg_with_bg = []
    for idx, (s, t) in enumerate(dialogues, start=1):
        img = None
        # procura diretamente em assets/sprites por cutscene_#.png
        p = os.path.join(sprites_dir, f"cutscene_{idx}.png")
        if os.path.exists(p):
            try:
                img = pygame.image.load(p).convert_alpha()
                img = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
            except Exception:
                img = None
        dlg_with_bg.append((s, t, img))

    _show_dialogue_generic(screen, dlg_with_bg, bg_image=None, typing_speed_chars_per_sec=140)

# -------------------------
# Mantive a sua show_menu praticamente igual, só ajuste para chamar intro+história
# -------------------------
def show_menu(screen, cover_image=None):
    """
    Mostra a tela inicial com capa e 3 botões: Jogar, História, Sobre.
    Retorna quando o jogador escolher Jogar.
    """
    pygame.font.init()
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("Arial", 48, bold=True)
    btn_font = pygame.font.SysFont("Arial", 26, bold=True)
    small_font = pygame.font.SysFont("Arial", 18)

    # usa a imagem passada ou nenhum fundo se None
    bg_image = cover_image

    # botões centralizados
    btn_w, btn_h = 220, 60
    spacing = 20
    total_h = btn_h*3 + spacing*2
    start_y = HEIGHT//2 - total_h//2 + 80
    play_rect = pygame.Rect(WIDTH//2 - btn_w//2, start_y, btn_w, btn_h)
    history_rect = pygame.Rect(WIDTH//2 - btn_w//2, start_y + btn_h + spacing, btn_w, btn_h)
    about_rect = pygame.Rect(WIDTH//2 - btn_w//2, start_y + 2*(btn_h + spacing), btn_w, btn_h)

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if play_rect.collidepoint(ev.pos):
                    # ao clicar em Jogar, primeiro mostra intro cutscene, depois a história/contexto,
                    # e então retorna para iniciar os minigames no main()
                   
                    show_story_cutscene(screen)
                    return  # começa os minigames
                if history_rect.collidepoint(ev.pos):
                    show_text_screen(screen, "História", (
                        "Durante a Guerra Fria, Estados Unidos e União Soviética disputaram a supremacia espacial.\n\n"
                        "Nesta simulação, você participa da montagem do foguete (mini-game estilo Tetris) e, em seguida, da corrida espacial para a Lua."
                    ))
                if about_rect.collidepoint(ev.pos):
                    show_text_screen(screen, "Sobre", (
                        "Cold War Race - projeto educativo que mistura puzzle e corrida.\n\n"
                        "Desenvolvido como exemplo didático. Ajuste recursos e assets em assets/."
                    ))

        mouse_pos = pygame.mouse.get_pos()
        # desenha fundo
        if bg_image:
            screen.blit(bg_image, (0,0))
            overlay = pygame.Surface((WIDTH, HEIGHT), flags=pygame.SRCALPHA)
            overlay.fill((6,12,40,160))  # leve escurecimento para legibilidade
            screen.blit(overlay, (0,0))
        else:
            screen.fill((6,12,40))

        # titulo e subtitulo
        title_s = title_font.render("CORRIDA ESPACIAL", True, (255, 255, 255))
        screen.blit(title_s, (WIDTH//2 - title_s.get_width()//2, 60))
        hint_s = small_font.render("Use o mouse para escolher.", True, (200,200,200))
        screen.blit(hint_s, (WIDTH//2 - hint_s.get_width()//2, 120))

        # desenha botões
        for rect, text in ((play_rect, "Jogar"), (history_rect, "História"), (about_rect, "Sobre")):
            hovered = rect.collidepoint(mouse_pos)
            color = (160, 40, 40) if text == "Jogar" else (160,40,40)
            bg = tuple(min(255, c + (30 if hovered else 0)) for c in color)
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, (10,10,10), rect, 3, border_radius=8)
            txt = btn_font.render(text, True, (255,255,255))
            screen.blit(txt, (rect.x + (rect.width - txt.get_width())//2, rect.y + (rect.height - txt.get_height())//2))

        pygame.display.flip()
        clock.tick(60)

# -------------------------
# MAIN
# -------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cold War Race - Montagem & Corrida")

    # caminhos de assets (corrigido: assets está uma pasta acima de src)
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
    backgrounds_dir = os.path.join(assets_dir, "backgrounds")
    sprites_dir = os.path.join(assets_dir, "sprites")
    print(f"Procurando assets em: {assets_dir}")

    # CARREGA CAPA: procura primeiro em assets/backgrounds, depois em assets raiz
    cover_image = None
    cover_candidates = [
        os.path.join(backgrounds_dir, "capa.png"),
        os.path.join(backgrounds_dir, "cover.png"),
        os.path.join(assets_dir, "capa.png"),
        os.path.join(assets_dir, "cover.png"),
    ]
    for p in cover_candidates:
        if os.path.exists(p):
            try:
                cover_image = pygame.image.load(p).convert_alpha()
                cover_image = pygame.transform.smoothscale(cover_image, (WIDTH, HEIGHT))
                print("Carregou capa de:", p)
                break
            except Exception as e:
                print("Falha ao carregar capa", p, e)
        else:
            print("Não encontrado:", p)

    # CARREGA FUNDO DO TETRIS: tenta tetris_bg.png, senão usa lab_urss / lab_usa como fallback
    tetris_bg = None
    tetris_candidates = [
        os.path.join(backgrounds_dir, "tetris_bg.png"),
        os.path.join(backgrounds_dir, "lab_urss.png"),
        os.path.join(backgrounds_dir, "lab_usa.png"),
    ]
    for p2 in tetris_candidates:
        if os.path.exists(p2):
            try:
                tetris_bg = pygame.image.load(p2).convert_alpha()
                tetris_bg = pygame.transform.smoothscale(tetris_bg, (WIDTH, HEIGHT))
                print("Carregou tetris bg de:", p2)
                break
            except Exception as e:
                print("Falha ao carregar tetris bg", p2, e)
        else:
            print("Não encontrado:", p2)

    # mostra menu inicial e só prossegue quando Jogar for escolhido
    show_menu(screen, cover_image)

    # === FASE 1: TETRIS (montagem do foguete) ===
    # desenha fundo do Tetris se existir
    if tetris_bg:
        screen.blit(tetris_bg, (0,0))
        pygame.display.flip()
        pygame.time.wait(150)  # breve pausa para o jogador ver o fundo antes do minigame

    # desloca o Tetris para a esquerda para liberar o centro para as manchetes
    x_offset = -150                   # ajuste esse valor conforme quiser (negativo = esquerda)
    headlines_y = HEIGHT // 2 - 20    # y para desenhar as manchetes no meio da tela
    times = tetris_phase(screen, x_offset=x_offset, headlines_y=headlines_y)  # retorna ms de cada player

    # calcula vantagem inicial em progresso para a corrida
    adv_urss, adv_eua = compute_advantage(times)

    # mostra cutscene informativa antes da corrida (usando imagem cutscene_foguete)
    sprites_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'sprites'))
    foguete_img = None
    foguete_path = os.path.join(sprites_dir, "cutscene_foguete.png")
    if os.path.exists(foguete_path):
        try:
            foguete_img = pygame.image.load(foguete_path).convert_alpha()
            foguete_img = pygame.transform.smoothscale(foguete_img, (WIDTH, HEIGHT))
        except Exception as e:
            print("Erro ao carregar cutscene_foguete:", e)
    else:
        print("cutscene_foguete não encontrado em:", foguete_path)

    # prepara texto conforme vantagem
    if adv_urss > adv_eua:
        end_text = "URSS obtém vantagem pela montagem do foguete. A corrida começa com eles em vantagem."
    elif adv_eua > adv_urss:
        end_text = "EUA obtém vantagem pela montagem do foguete. A corrida começa com eles em vantagem."
    else:
        end_text = "Empate na montagem — a corrida começa equilibrada."

    # mostra uma única cena (imagem do foguete + texto do narrador)
    _show_dialogue_generic(screen, [("Narrador", end_text, foguete_img)], bg_image=None, typing_speed_chars_per_sec=140)

    # === FASE 2: CORRIDA ESPACIAL ===
    # RocketRace aceita advantage1 (URSS) e advantage2 (EUA)
    race = RocketRace(screen, advantage1=adv_urss, advantage2=adv_eua)
    winner = race.run()

    # === TELA FINAL ===
    end_screen(screen, winner)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
