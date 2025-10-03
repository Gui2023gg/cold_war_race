import pygame, time, random, sys
import os

# Configurações locais
GRID_W, GRID_H = 10, 20
BLOCK = 28
PADDING = 20
FALL_INTERVAL_MS = 600  # mais lento
MIN_LINES = 5           # meta de linhas para finalizar Tetris
POPUP_MS = 3000
TITLE = "Montagem do Foguete"
FPS = 60

# Tetrominoes
TETROMINOES = {
    'I': [[(0,1),(1,1),(2,1),(3,1)], [(2,0),(2,1),(2,2),(2,3)]],
    'O': [[(1,0),(2,0),(1,1),(2,1)]],
    'T': [[(1,0),(0,1),(1,1),(2,1)], [(1,0),(1,1),(2,1),(1,2)],
          [(0,1),(1,1),(2,1),(1,2)], [(1,0),(0,1),(1,1),(1,2)]],
    'L': [[(2,0),(0,1),(1,1),(2,1)], [(1,0),(1,1),(1,2),(2,2)],
          [(0,1),(1,1),(2,1),(0,2)], [(0,0),(1,0),(1,1),(1,2)]],
    'J': [[(0,0),(0,1),(1,1),(2,1)], [(1,0),(2,0),(1,1),(1,2)],
          [(0,1),(1,1),(2,1),(2,2)], [(1,0),(1,1),(1,2),(0,2)]],
    'S': [[(1,0),(2,0),(0,1),(1,1)], [(1,0),(1,1),(2,1),(2,2)]],
    'Z': [[(0,0),(1,0),(1,1),(2,1)], [(2,0),(1,1),(2,1),(1,2)]]
}
COLORS = {
    'I': (0,255,255),'O':(255,255,0),'T':(160,32,240),'L':(255,165,0),
    'J':(0,0,255),'S':(0,255,0),'Z':(255,0,0)
}

# Notícias (manchetes) - a lista que você pediu (mantive exatamente)
NEWS = [
    "1957 - URSS lança o Sputnik 1:\n primeiro satélite artificial em órbita, provocando onda de orgulho e temor mundial.",
    "1957 - Laika embarca no Sputnik 2:\n cadela pioneira torna-se o primeiro ser vivo a orbitar a Terra.",
    "1958 - Explorer 1 detecta cinturões de Van Allen:\n Congresso cria a NASA em resposta à corrida espacial.",
    "1961 - Yuri Gagarin faz história:\n primeiro humano a orbitar o planeta em missão soviética vitoriosa.",
    "1961 - Kennedy promete:\n 'Vamos pôr um homem na Lua antes de 1969', novo objetivo americano na corrida lunar.",
    "1965 - Aleksei Leonov realiza a primeira\n caminhada espacial, demonstrando a capacidade de operações fora da cabine.",
    "1968 - Apollo 8 orbita a Lua e nos dá Earthrise:\n imagem icônica que muda a visão do planeta."
]
# duração (ms) que cada manchete fica visível
NEWS_DURATION_MS = 3000

# --- Funções de Tetris (sem alterações de lógica) ---
def new_board():
    return [[None for _ in range(GRID_W)] for _ in range(GRID_H)]

def spawn_piece():
    kind = random.choice(list(TETROMINOES.keys()))
    return {'kind': kind, 'rot': 0, 'x': GRID_W//2 - 2, 'y': -1}

def get_cells(piece):
    shape = TETROMINOES[piece['kind']][piece['rot'] % len(TETROMINOES[piece['kind']])]
    return [(piece['x'] + dx, piece['y'] + dy) for dx,dy in shape]

def valid_position(board, piece, dx=0, dy=0, rot=None):
    rot = piece['rot'] if rot is None else rot
    shape = TETROMINOES[piece['kind']][rot % len(TETROMINOES[piece['kind']])]
    for ox, oy in shape:
        x = piece['x'] + dx + ox
        y = piece['y'] + dy + oy
        if x < 0 or x >= GRID_W or y >= GRID_H:
            if y < 0:
                continue
            return False
        if y >= 0 and board[y][x] is not None:
            return False
    return True

def lock_piece(board, piece):
    for x,y in get_cells(piece):
        if 0 <= y < GRID_H:
            board[y][x] = piece['kind']

def clear_lines(board):
    newb = [row for row in board if any(cell is None for cell in row)]
    cleared = GRID_H - len(newb)
    while len(newb) < GRID_H:
        newb.insert(0, [None]*GRID_W)
    return newb, cleared

def draw_board(surface, board, top_left):
    ox, oy = top_left
    pygame.draw.rect(surface, (30,30,30), (ox-4, oy-4, GRID_W*BLOCK+8, GRID_H*BLOCK+8))
    for r in range(GRID_H):
        for c in range(GRID_W):
            cell = board[r][c]
            rect = pygame.Rect(ox + c*BLOCK, oy + r*BLOCK, BLOCK-1, BLOCK-1)
            if cell:
                pygame.draw.rect(surface, COLORS.get(cell,(200,200,200)), rect)
            else:
                pygame.draw.rect(surface, (15,15,15), rect, 1)

def draw_piece(surface, piece, top_left):
    ox, oy = top_left
    for x,y in get_cells(piece):
        if y >= 0:
            rect = pygame.Rect(ox + x*BLOCK, oy + y*BLOCK, BLOCK-1, BLOCK-1)
            pygame.draw.rect(surface, COLORS.get(piece['kind'], (200,200,200)), rect)

# --- Nova função: desenha as notícias empilhadas (estilo jornal) ---
def draw_news_stack(screen, font_title, font_text, news_list, max_boxes=7):
    """
    Desenha as notícias empilhadas centralizadas.
    max_boxes: quantas caixas desenhar no máximo (usa len(news_list) se for menor).
    """
    w, h = screen.get_size()
    box_w = 320
    # calcular heights dinâmicos (cada notícia pode ter 1-2 linhas)
    boxes = []
    spacing = 12
    for text in news_list[:max_boxes]:
        # considera quebrar linhas já presentes
        lines = [ln.strip() for ln in text.split("\n")]
        # altura: faixa título (40) + linhas*20 + margem
        bh = 40 + len(lines)*22 + 12
        boxes.append((text, lines, bh))

    total_h = sum(bh for (_,_,bh) in boxes) + spacing * (len(boxes)-1)
    start_y = max(110, h//2 - total_h//2)  # não muito alto

    for i, (full_text, lines, bh) in enumerate(boxes):
        box_x = w//2 - box_w//2
        box_y = start_y + i*(bh + spacing)

        # Sombra e borda leve
        shadow = pygame.Surface((box_w+8, bh+8), pygame.SRCALPHA)
        shadow.fill((0,0,0,90))
        screen.blit(shadow, (box_x+4, box_y+4))

        # Caixa branca principal
        pygame.draw.rect(screen, (255,255,255), (box_x, box_y, box_w, bh))
        pygame.draw.rect(screen, (30,30,30), (box_x, box_y, box_w, bh), 2)

        # Faixa vermelha superior (NEWS)
        pygame.draw.rect(screen, (220,80,80), (box_x, box_y, box_w, 36))
        news_label = font_title.render("NEWS", True, (255,255,255))
        screen.blit(news_label, (box_x + 12, box_y + 6))

        # Linha preta decorativa (abaixo do título)
        pygame.draw.rect(screen, (10,10,10), (box_x + 8, box_y + 44, box_w - 16, 6))

        # Conteúdo (texto)
        # se o texto começar com "YYYY — ..." vamos quebrar o ano e título com destaque
        # aqui simplificamos: tiramos a primeira linha e mostramos em negrito (font_title)
        first_line = lines[0] if lines else ""
        rest_lines = lines[1:] if len(lines) > 1 else []
        # desenhar a primeira linha (mais destacada)
        y_text = box_y + 56
        # split first line roughly into year/title if contains '—'
        if '—' in first_line:
            parts = first_line.split('—', 1)
            year = parts[0].strip()
            title = parts[1].strip()
            year_title_surf = font_title.render(f"{year} — {title}", True, (10,10,10))
            screen.blit(year_title_surf, (box_x + 12, box_y + 46))
            y_text = box_y + 46 + year_title_surf.get_height() + 6
        else:
            # fallback: draw whole first line with title font
            t = font_title.render(first_line, True, (10,10,10))
            screen.blit(t, (box_x + 12, box_y + 46))
            y_text = box_y + 46 + t.get_height() + 6

        # desenhar restante das linhas (desc)
        for ln in rest_lines:
            txt = font_text.render(ln, True, (20,20,20))
            screen.blit(txt, (box_x + 12, y_text))
            y_text += txt.get_height() + 4

def wrap_text(text, font, max_width):
    """Quebra texto em linhas que caibam em max_width usando medidas do font."""
    lines = []
    for paragraph in text.splitlines():
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

def draw_news_box(screen, font_title, font_text, news_text, x_center, y_top, box_w=520, min_box_h=None):
    """Desenha UMA caixa de notícia centralizada em x_center, com topo em y_top.
    Se min_box_h for fornecido, força a altura mínima da caixa para deixá-la mais alta.
    """
    w, h = screen.get_size()
    padding_x = 12
    inner_w = box_w - padding_x*2

    parts = news_text.split("\n")
    first_line = parts[0] if parts else ""
    rest_text = "\n".join(parts[1:]) if len(parts) > 1 else ""

    title_lines = wrap_text(first_line, font_title, inner_w)
    rest_lines = wrap_text(rest_text, font_text, inner_w) if rest_text else []

    title_h = len(title_lines) * font_title.get_linesize()
    rest_h = len(rest_lines) * font_text.get_linesize()
    header_h = 44
    box_h = header_h + title_h + rest_h + 20
    if min_box_h:
        box_h = max(box_h, min_box_h)

    box_x = x_center - box_w//2
    box_y = y_top

    # sombra + fundo (respeita box_h possivelmente maior)
    shadow = pygame.Surface((box_w+6, box_h+6), pygame.SRCALPHA)
    shadow.fill((0,0,0,100))
    screen.blit(shadow, (box_x+3, box_y+3))
    pygame.draw.rect(screen, (255,255,255), (box_x, box_y, box_w, box_h))
    pygame.draw.rect(screen, (30,30,30), (box_x, box_y, box_w, box_h), 2)

    # faixa NEWS
    pygame.draw.rect(screen, (200,50,50), (box_x, box_y, box_w, 36))
    news_label = font_title.render("Noticias", True, (255,255,255))
    screen.blit(news_label, (box_x + 12, box_y + 6))

    # Título (first_line) — tenta destacar ano se houver "—"
    y_cursor = box_y + header_h
    if '—' in first_line:
        parts = first_line.split('—', 1)
        year = parts[0].strip()
        title = parts[1].strip()
        year_title_surf = font_title.render(f"{year} — {title}", True, (10,10,10))
        screen.blit(year_title_surf, (box_x + padding_x, y_cursor))
        y_cursor += year_title_surf.get_height() + 6
    else:
        for tl in title_lines:
            surf = font_title.render(tl, True, (10,10,10))
            screen.blit(surf, (box_x + padding_x, y_cursor))
            y_cursor += surf.get_height()
        y_cursor += 6

    # Desenha uma linha preta fina (divisor) separando o título do restante
    divider_y = y_cursor + 6
    pygame.draw.rect(screen, (0,0,0), (box_x + padding_x, divider_y, box_w - padding_x*2, 2))
    y_cursor = divider_y + 10

    # Descrição/linhas restantes
    for ln in rest_lines:
        surf = font_text.render(ln, True, (20,20,20))
        screen.blit(surf, (box_x + padding_x, y_cursor))
        y_cursor += surf.get_height() + 4

    return box_w, box_h

# --- Função principal do Tetris (mantive toda lógica original) ---
def tetris_phase(screen, x_offset=0, headlines_y=None):
    pygame.font.init()
    font = pygame.font.SysFont("Arial", 20)
    title_font = pygame.font.SysFont("Arial", 28, bold=True)
    big_font = pygame.font.SysFont("Arial", 36, bold=True)
    clock = pygame.time.Clock()

    if headlines_y is None:
        headlines_y = screen.get_height() - 80  # comportamento antigo se não passar param

    # Areas - centraliza cada jogo na sua metade
    w = screen.get_width()
    h = screen.get_height()
    # x_offset: deslocamento aplicado em direções opostas para abrir espaço no centro
    # Ex.: x_offset = -150 -> left_x move 150px para a esquerda, right_x move 150px para a direita.
    left_x = (w // 3.2) - (GRID_W * BLOCK) // 2 + x_offset
    right_x = (2.2 * w // 3.2) - (GRID_W * BLOCK) // 2 - x_offset
    top_y = (h - GRID_H * BLOCK) // 1.5

    # Players state
    boards = [new_board(), new_board()]
    pieces = [spawn_piece(), spawn_piece()]
    fall_times = [pygame.time.get_ticks(), pygame.time.get_ticks()]
    lines = [0,0]
    finish_ms = [None, None]
    popups = ["",""]
    popup_ts = [0,0]

    # News timing (não mais necessário para empilhamento, mas mantido para compat.)
    news_index = 0
    last_news_ts = pygame.time.get_ticks()
    # se quiser iniciar com a primeira notícia parcialmente exibida, ajuste last_news_ts para menor
    # news_start_ts mantido apenas para compatibilidade com código antigo (não usado)
    news_start_ts = last_news_ts

    # End-of-tetris overlay control
    overlay_shown = False
    overlay_winner = None  # 0 or 1
    overlay_msg = ""
    overlay_start = 0

    # Carregar fundos distintos para cada lado (fallback para cor sólida se arquivo ausente)
    # caminho absoluto relativo a este arquivo (src/)
    assets_bg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'backgrounds'))
    bg_left = None
    bg_right = None
    p_left = os.path.join(assets_bg_dir, "lab_urss.png")
    p_right = os.path.join(assets_bg_dir, "lab_usa.png")
    if os.path.exists(p_left):
        try:
            bg_left = pygame.image.load(p_left).convert()
        except Exception:
            bg_left = None
    if os.path.exists(p_right):
        try:
            bg_right = pygame.image.load(p_right).convert()
        except Exception:
            bg_right = None

    # redimensiona/cobre cada metade
    if bg_left:
        bg_left = pygame.transform.scale(bg_left, (w//2, h))
    if bg_right:
        bg_right = pygame.transform.scale(bg_right, (w//2, h))

    running = True
    start_time = time.time()

    while running:
        now = pygame.time.get_ticks()
        elapsed = int(time.time() - start_time)

        # process events properly (fix: handle inside the loop so player 0 keys work)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                now_ms = int((time.time() - start_time) * 1000)
                urss_ms = finish_ms[0] if finish_ms[0] is not None else now_ms
                eua_ms  = finish_ms[1] if finish_ms[1] is not None else now_ms
                return {"URSS_ms": urss_ms, "EUA_ms": eua_ms}

            # If overlay is shown, only listen for a key/mouse to continue
            if overlay_shown:
                if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                    now_ms = int((time.time() - start_time) * 1000)
                    urss_ms = finish_ms[0] if finish_ms[0] is not None else now_ms
                    eua_ms  = finish_ms[1] if finish_ms[1] is not None else now_ms
                    return {"URSS_ms": urss_ms, "EUA_ms": eua_ms}
                # ignore other events while overlay is up
                continue

            # Normal input handling for both players
            if event.type == pygame.KEYDOWN:
                # Player 0 controls (URSS): A/D move, S drop, W rotate
                if event.key == pygame.K_a:
                    if valid_position(boards[0], pieces[0], dx=-1):
                        pieces[0]['x'] -= 1
                elif event.key == pygame.K_d:
                    if valid_position(boards[0], pieces[0], dx=1):
                        pieces[0]['x'] += 1
                elif event.key == pygame.K_s:
                    if valid_position(boards[0], pieces[0], dy=1):
                        pieces[0]['y'] += 1
                elif event.key == pygame.K_w:
                    new_rot = (pieces[0]['rot'] + 1) % len(TETROMINOES[pieces[0]['kind']])
                    for shift in (0,-1,1,-2,2):
                        if valid_position(boards[0], pieces[0], dx=shift, rot=new_rot):
                            pieces[0]['rot'] = new_rot
                            pieces[0]['x'] += shift
                            break

                # Player 1 controls (EUA): Arrows
                elif event.key == pygame.K_LEFT:
                    if valid_position(boards[1], pieces[1], dx=-1):
                        pieces[1]['x'] -= 1
                elif event.key == pygame.K_RIGHT:
                    if valid_position(boards[1], pieces[1], dx=1):
                        pieces[1]['x'] += 1
                elif event.key == pygame.K_DOWN:
                    if valid_position(boards[1], pieces[1], dy=1):
                        pieces[1]['y'] += 1
                elif event.key == pygame.K_UP:
                    new_rot = (pieces[1]['rot'] + 1) % len(TETROMINOES[pieces[1]['kind']])
                    for shift in (0,-1,1,-2,2):
                        if valid_position(boards[1], pieces[1], dx=shift, rot=new_rot):
                            pieces[1]['rot'] = new_rot
                            pieces[1]['x'] += shift
                            break

        # Se overlay foi acionado, pausa lógica e mostra UI até o jogador prosseguir
        if overlay_shown:
            # desenhar apenas UI abaixo; não processa gravidade
            screen.fill((10,10,40))
            title_surf = title_font.render(TITLE, True, (255,215,0))
            screen.blit(title_surf, (w//2 - title_surf.get_width()//2, 8))
            timer_surf = font.render(f"Tempo: {elapsed}s", True, (255,255,255))
            screen.blit(timer_surf, (w//2 - timer_surf.get_width()//2, 44))

            # desenha boards e peças (congeladas)
            draw_board(screen, boards[0], (left_x, top_y))
            draw_board(screen, boards[1], (right_x, top_y))
            draw_piece(screen, pieces[0], (left_x, top_y))
            draw_piece(screen, pieces[1], (right_x, top_y))

            # overlay de vencedor do Tetris
            overlay_bg = pygame.Surface((w//2, 160))
            overlay_bg.set_alpha(230)
            overlay_bg.fill((8,8,20))
            ox = w//2 - overlay_bg.get_width()//2
            oy = h//2 - overlay_bg.get_height()//2 - 40
            screen.blit(overlay_bg, (ox, oy))

            winner_text = big_font.render(overlay_msg, True, (255,255,255))
            screen.blit(winner_text, (w//2 - winner_text.get_width()//2, oy + 20))

            button_rect = pygame.Rect(w//2 - 120, oy + 90, 240, 40)
            pygame.draw.rect(screen, (60,120,180), button_rect)
            btn_text = font.render("Ir para a Corrida (press/clk)", True, (255,255,255))
            screen.blit(btn_text, (button_rect.centerx - btn_text.get_width()//2, button_rect.centery - btn_text.get_height()//2))

            pygame.display.flip()
            clock.tick(FPS)
            continue

        # Gravity per player
        for i in (0,1):
            if now - fall_times[i] > FALL_INTERVAL_MS:
                fall_times[i] = now
                if valid_position(boards[i], pieces[i], dy=1):
                    pieces[i]['y'] += 1
                else:
                    lock_piece(boards[i], pieces[i])
                    boards[i], cleared = clear_lines(boards[i])
                    if cleared:
                        lines[i] += cleared
                        popups[i] = f"Linha completa! (+{cleared})"
                        popup_ts[i] = pygame.time.get_ticks()
                        if finish_ms[i] is None and lines[i] >= MIN_LINES:
                            finish_ms[i] = int((time.time() - start_time) * 1000)
                            # Decide vencedor do Tetris: se outro já terminou, menor tempo; se não, este jogador venceu
                            other = 1 - i
                            if finish_ms[other] is not None:
                                if finish_ms[i] < finish_ms[other]:
                                    overlay_winner = i
                                elif finish_ms[i] > finish_ms[other]:
                                    overlay_winner = other
                                else:
                                    overlay_winner = None  # empate
                            else:
                                overlay_winner = i
                            # configura mensagem do overlay
                            if overlay_winner is None:
                                overlay_msg = "Tetris: Empate!"
                            elif overlay_winner == 0:
                                overlay_msg = "URSS venceu o Tetris!"
                            else:
                                overlay_msg = "EUA venceu o Tetris!"
                            overlay_shown = True
                            overlay_start = now
                            # notifica opponent pop-up with diff
                            if finish_ms[other] is None:
                                current_ms = int((time.time() - start_time) * 1000)
                                diff_s = (current_ms - finish_ms[i]) / 1000.0
                                popups[other] = f"Diferença: {diff_s:.2f}s"
                                popup_ts[other] = pygame.time.get_ticks()
                            popups[i] = "Terminou!"
                            popup_ts[i] = pygame.time.get_ticks()
                    pieces[i] = spawn_piece()
                    # spawn invalid -> treat as finished
                    if not valid_position(boards[i], pieces[i]):
                        if finish_ms[i] is None:
                            finish_ms[i] = int((time.time() - start_time) * 1000)
                        popups[i] = "Game over"
                        popup_ts[i] = pygame.time.get_ticks()
                        other = 1 - i
                        if finish_ms[other] is None:
                            current_ms = int((time.time() - start_time) * 1000)
                            diff_s = (current_ms - finish_ms[i]) / 1000.0
                            popups[other] = f"Diferença: {diff_s:.2f}s"
                            popup_ts[other] = pygame.time.get_ticks()

        # Draw normal game UI
        # em vez de fill uniforme, desenhamos os dois fundos (ou fallback)
        # Left background
        if bg_left:
            screen.blit(bg_left, (0,0))
        else:
            screen.fill((10,10,40))
            pygame.draw.rect(screen, (22,30,46), (0,0,w//2,h))

        # Right background
        if bg_right:
            screen.blit(bg_right, (w//2,0))
        else:
            pygame.draw.rect(screen, (16,20,36), (w//2,0,w//2,h))

        # Linha divisória (desenhada agora, mas ficará "atrás" das notícias,
        # porque desenhamos as notícias depois)
        pygame.draw.line(screen, (80,80,100), (w//2, 0), (w//2, h), 6)

        title_surf = title_font.render(TITLE, True, (255,255,255))
        screen.blit(title_surf, (w//2 - title_surf.get_width()//2, 10))
        timer_surf = font.render(f"Tempo: {elapsed}s", True, (255,255,255))
        screen.blit(timer_surf, (w//2 - timer_surf.get_width()//2, 50))

        draw_board(screen, boards[0], (left_x, top_y))
        draw_board(screen, boards[1], (right_x, top_y))
        draw_piece(screen, pieces[0], (left_x, top_y))
        draw_piece(screen, pieces[1], (right_x, top_y))

        label0 = font.render(f"URSS - Peças Montadas: {lines[0]}/{MIN_LINES}", True, (255,255,255))
        label1 = font.render(f"EUA  - Peças Montadas: {lines[1]}/{MIN_LINES}", True, (255,255,255))
        screen.blit(label0, (left_x + (GRID_W*BLOCK - label0.get_width())//2, top_y - 30))
        screen.blit(label1, (right_x + (GRID_W*BLOCK - label1.get_width())//2, top_y - 30))

        # Popups dos jogadores
        for i, msg in enumerate(popups):
            if msg and pygame.time.get_ticks() - popup_ts[i] < POPUP_MS:
                half_center_x = (w//4) if i == 0 else (3*w//4)
                popup_surf = font.render(msg, True, (255,180,180))
                x = half_center_x - popup_surf.get_width()//2
                y = h - 60
                screen.blit(popup_surf, (x, y))

        # ------------------------------------------------------------
        # Aqui desenhamos as notícias empilhadas (no topo de tudo),
        # estilo jornal — esta parte substitui a antiga "news cycling".
        # ------------------------------------------------------------
        # avançar notícia a cada intervalo
        if now - last_news_ts > NEWS_DURATION_MS:
            news_index = (news_index + 1) % len(NEWS)
            last_news_ts = now

        # desenha apenas UMA notícia: largura anterior (estreita) e caixa alta,
        # agora CENTRALIZADA verticalmente na tela
        box_w = min(w - 270, 320)
        min_box_h = 300
        # calcule y de modo que a caixa fique exatamente centralizada verticalmente
        news_y = h//2 - (min_box_h // 2)
        draw_news_box(screen, title_font, font, NEWS[news_index], w//2, news_y, box_w=box_w, min_box_h=min_box_h)

        title_surf = title_font.render(TITLE, True, (255,255,255))
        screen.blit(title_surf, (w//2 - title_surf.get_width()//2, 10))
        timer_surf = font.render(f"Tempo: {elapsed}s", True, (255,255,255))
        screen.blit(timer_surf, (w//2 - timer_surf.get_width()//2, 50))

        pygame.display.flip()
        clock.tick(FPS)

    # Fallback return (won't usually reach aqui)
    now_ms = int((time.time() - start_time) * 1000)
    urss_ms = finish_ms[0] if finish_ms[0] is not None else now_ms
    eua_ms = finish_ms[1] if finish_ms[1] is not None else now_ms
    return {"URSS_ms": urss_ms, "EUA_ms": eua_ms}


# Se executar diretamente para teste rápido
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1000,700))
    pygame.display.set_caption("Tetris - Teste")
    res = tetris_phase(screen)
    print("retorno:", res)
    pygame.quit()