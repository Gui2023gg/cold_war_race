import pygame, time, sys
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

        screen.fill((6,12,40))
        title = big.render("CORRIDA ATÉ A LUA", True, (255, 215, 0))
        subtitle = small.render(adv_msg, True, (240,240,240))
        hint = small.render("Aperte Esc para sair", True, (180,180,180))

        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 60))

        pygame.display.flip()
        clock.tick(60)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cold War Race - Montagem & Corrida")

    # === FASE 1: TETRIS (montagem do foguete) ===
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

        # News global
    if news_index >= 0 and now - news_start_ts < NEWS_DISPLAY_MS:
            news_msg = NEWS[news_index]
            # largura máxima para as manchetes (deixe margem nas laterais)
            max_w = min(w - 200, 900)  # ajuste se quiser mais/menos largura
            lines = wrap_text(news_msg, font, max_w)
            # calcula altura total do bloco de texto
            line_h = font.get_linesize()
            total_h = line_h * len(lines)
            x = w//2 - max_w//2
            y = headlines_y
            bg_rect = pygame.Rect(x-12, y-8, max_w+24, total_h+16)
            pygame.draw.rect(screen, (25,25,25), bg_rect)
            ly = y
            for line in lines:
                if line == "":
                    ly += line_h
                    continue
                line_surf = font.render(line, True, (240,240,200))
                screen.blit(line_surf, (x + (max_w - line_surf.get_width())//2, ly))
                ly += line_h
