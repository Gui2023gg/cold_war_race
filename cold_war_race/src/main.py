import pygame, time, sys, os
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

def show_cutscene(screen, adv_urss, adv_eua):
    pygame.font.init()
    big = pygame.font.SysFont("Arial", 48, bold=True)
    small = pygame.font.SysFont("Arial", 28)
    clock = pygame.time.Clock()
    start = pygame.time.get_ticks()
    duration_ms = 2500

    # Determine message about advantage
    if adv_urss > adv_eua:
        adv_msg = f"URSS recebe vantagem inicial: {adv_urss} pts"
    elif adv_eua > adv_urss:
        adv_msg = f"EUA recebe vantagem inicial: {adv_eua} pts"
    else:
        adv_msg = "Empate no Tetris — nenhuma vantagem inicial"

    while pygame.time.get_ticks() - start < duration_ms:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        screen.fill((6,12,40))
        title = big.render("CORRIDA ESPACIAL", True, (255, 215, 0))
        subtitle = small.render(adv_msg, True, (240,240,240))
        hint = small.render("Aperte Esc para sair", True, (180,180,180))

        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 60))

        pygame.display.flip()
        clock.tick(60)

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
        title_s = title_font.render("CORRIDA ATÉ A LUA", True, (255, 215, 0))
        screen.blit(title_s, (WIDTH//2 - title_s.get_width()//2, 60))
        hint_s = small_font.render("Use o mouse para escolher. Esc para sair.", True, (200,200,200))
        screen.blit(hint_s, (WIDTH//2 - hint_s.get_width()//2, 120))

        # desenha botões
        for rect, text in ((play_rect, "Jogar"), (history_rect, "História"), (about_rect, "Sobre")):
            hovered = rect.collidepoint(mouse_pos)
            color = (220, 60, 40) if text == "Jogar" else (60,120,200)
            bg = tuple(min(255, c + (30 if hovered else 0)) for c in color)
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, (10,10,10), rect, 3, border_radius=8)
            txt = btn_font.render(text, True, (255,255,255))
            screen.blit(txt, (rect.x + (rect.width - txt.get_width())//2, rect.y + (rect.height - txt.get_height())//2))

        pygame.display.flip()
        clock.tick(60)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cold War Race - Montagem & Corrida")

    # carrega assets (tenta nomes alternativos)
    # ajustar caminho para a pasta assets na raiz do projeto
    assets_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets'))
    assets_dir = os.path.abspath(assets_dir)
    print(f"Procurando assets em: {assets_dir}")

    cover_image = None
    for name in ("capa.png", "cover.png"):
        p = os.path.join(assets_dir, name)
        if os.path.exists(p):
            try:
                cover_image = pygame.image.load(p).convert_alpha()
                cover_image = pygame.transform.smoothscale(cover_image, (WIDTH, HEIGHT))
                print(f"Carregou capa: {p}")
                break
            except Exception as e:
                print(f"Erro ao carregar {p}: {e}")
        else:
            print(f"Não encontrado: {p}")

    tetris_bg = None
    for name in ("tetris_bg.png",):
        p2 = os.path.join(assets_dir, name)
        if os.path.exists(p2):
            try:
                tetris_bg = pygame.image.load(p2).convert_alpha()
                tetris_bg = pygame.transform.smoothscale(tetris_bg, (WIDTH, HEIGHT))
                print(f"Carregou tetris_bg: {p2}")
                break
            except Exception as e:
                print(f"Erro ao carregar {p2}: {e}")
        else:
            print(f"Não encontrado: {p2}")

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

    # mostra cutscene informativa antes da corrida
    show_cutscene(screen, adv_urss, adv_eua)

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
