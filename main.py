import pygame
import random
from time import time
import os
import sqlite3

conn = sqlite3.connect('results.db')
cursor = conn.cursor()
# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 800, 600
FPS = 30
PLAYER_SPEED = 5
SAFE_RADIUS = 150
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Загрузка изображений
enemy_img = pygame.image.load("game_assets/monkey.png")
bullet_img = pygame.image.load("game_assets/bullet.png")
boss_img = pygame.image.load("game_assets/boss.png")
background_img = pygame.image.load("game_assets/background.png")
ult_icon = pygame.image.load("game_assets/ult.png")
dash_icon = pygame.image.load("game_assets/cuvirock.png")

enemy_img = pygame.transform.scale(enemy_img, (52, 40))
bullet_img = pygame.transform.scale(bullet_img, (10, 10))
boss_img = pygame.transform.scale(boss_img, (144, 100))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
ult_icon = pygame.transform.scale(ult_icon, (50, 50))
dash_icon = pygame.transform.scale(dash_icon, (50, 50))

# Создание окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Progressive Room Game")
clock = pygame.time.Clock()

# Оружие
weapons = {
    "pistol": {"damage": 1, "delay": 400, "spread": 2, "bullets": 1, "unlock_room": 1},
    "shotgun": {"damage": 0.5, "delay": 500, "spread": 20, "bullets": 5, "unlock_room": 2},
    "rifle": {"damage": 0.8, "delay": 100, "spread": 5, "bullets": 1, "unlock_room": 4},
    "sniper": {"damage": 5, "delay": 1000, "spread": 2, "bullets": 1, "unlock_room": 6},
}
unlocked_weapons = ["pistol"]
current_weapon = "pistol"
last_shot_time = 0
shooting = False

# Враги
enemies = []
enemy_speed = 2
enemy_hp = 3
enemy_damage = 1
wave_size = 5
current_wave = 1
waves_per_room = 3
current_room = 0
max_rooms = 6
enemies_spawned = 0
last_spawn_time = 0
enemy_spawn_delay = 2000

# Пауза
paused = False

# Рывок
dash_distance = 150  # Дистанция рывка
dash_cooldown = 2000  # Время перезарядки рывка в миллисекундах
last_dash_time = 0
dashing = False
dash_line_color = (127, 118, 121)  # Цвет линии
dash_line_width = 3  # Толщина линии
dash_direction = (0, 0)  # Направление рывка

# Ульта
ult_active = False
ult_duration = 5000  # Время действия ульты (в миллисекундах)
ult_cooldown = 20000  # Откат ульты (в миллисекундах)
last_ult_time = -ult_cooldown
ult_start_time = 0

player_frames = []
frame_dir = "game_assets/player_frames"
PLAYER_SIZE = (70, 70)  # Новый размер игрока

for frame_file in sorted(os.listdir(frame_dir)):
    frame_path = os.path.join(frame_dir, frame_file)
    frame = pygame.image.load(frame_path)
    frame = pygame.transform.scale(frame, PLAYER_SIZE)  # Масштабирование
    player_frames.append(frame)

# Игрок
player = player = pygame.Rect(WIDTH // 2, HEIGHT // 2, PLAYER_SIZE[0], PLAYER_SIZE[1])
player_hp = 10
player_damage_delay = 100
last_damage_time = 0
player_frame_index = 0
player_frame_delay = 100  # Задержка между кадрами (мс)
last_frame_update_time = 0
player_count = 0

difficulty_levels = {
    "easy": {"enemy_hp": 2, "wave_size": 3},
    "medium": {"enemy_hp": 3, "wave_size": 5},
    "hard": {"enemy_hp": 5, "wave_size": 7},
}
current_difficulty = "medium"  # Уровень сложности по умолчанию

# Босс
boss = None
boss_hp = 200
boss_damage = 10
boss_spawned = False

# Снаряды
bullets = []
bullet_speed = 10

# Бафы
buff_types = {
    "hp": {
        "type": "hp",
        "effect": 5,
        "duration": 0,
        "icon": pygame.transform.scale(pygame.image.load("game_assets/buff_hp.png"), (32, 32))
    },
    "shield": {
        "type": "shield",
        "effect": 0,
        "duration": 100,
        "icon": pygame.transform.scale(pygame.image.load("game_assets/buff_shield.png"), (32, 32))
    },
    "fire_rate": {
        "type": "fire_rate",
        "effect": 0.5,
        "duration": 100,
        "icon": pygame.transform.scale(pygame.image.load("game_assets/buff_fire_rate.png"), (32, 32))
    },
}

buffs = []  # Список активных бафов на карте
active_buffs = {"shield": False, "fire_rate": False}  # Активные бафы игрока
buff_spawn_delay = 15000  # Задержка появления бафа (15 секунд)
last_buff_spawn_time = 0
shield_start_time = 0
fire_rate_start_time = 0
player_original_fire_delay = weapons[current_weapon]["delay"]


# Функция для появления врагов
def spawn_enemy(): 
    global enemies_spawned
    x, y = 0, 0
    while True:
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        if abs(x - player.centerx) > SAFE_RADIUS and abs(y - player.centery) > SAFE_RADIUS:
            break
    enemies.append({"rect": pygame.Rect(x, y, 40, 40), "hp": enemy_hp})
    enemies_spawned += 1

# Функция для появления босса
def spawn_boss():
    global boss
    boss = {"rect": pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 - 50, 100, 100), "hp": boss_hp}

# Функция для движения врагов
def move_enemies():
    for enemy in enemies:
        if enemy["rect"].x < player.x:
            enemy["rect"].x += enemy_speed
        if enemy["rect"].x > player.x:
            enemy["rect"].x -= enemy_speed
        if enemy["rect"].y < player.y:
            enemy["rect"].y += enemy_speed
        if enemy["rect"].y > player.y:
            enemy["rect"].y -= enemy_speed

# Функция стрельбы
def shoot():
    global last_shot_time
    current_time = time() * 1000
    weapon = weapons[current_weapon]

    if current_time - last_shot_time >= weapon["delay"]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        base_angle = pygame.math.Vector2(mouse_x - player.centerx, mouse_y - player.centery).angle_to((1, 0))

        for i in range(-(weapon["bullets"] // 2), (weapon["bullets"] // 2) + 1):
            angle = base_angle + i * weapon["spread"]
            direction = pygame.math.Vector2(1, 0).rotate(-angle)
            bullets.append({"rect": pygame.Rect(player.centerx, player.centery, 10, 10), "dir": direction, "damage": weapon["damage"]})

        last_shot_time = current_time

# Основной игровой цикл
running = True
unlocked_message = ""
message_display_time = 2000  # Время отображения сообщения в миллисекундах
message_start_time = 0

cursor.execute('''
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    score INT NOT NULL
)
''')

def save_score(name, score):
    cursor.execute("INSERT INTO results (name, score) VALUES (?, ?)", (name, score))
    conn.commit()

def load_leaderboard():
    leaderboard = []
    cursor.execute("SELECT * FROM results ORDER BY score DESC")
    rows = cursor.fetchall()
    for row in rows:
        leaderboard.append(f"{row[1]} - {row[2]}")
    return leaderboard[:5]  # Показываем только топ 10

def show_leaderboard():
    leaderboard = load_leaderboard()
    font = pygame.font.Font(None, 36)
    y_position = HEIGHT // 4
    screen.fill('black')
    
    title_text = font.render("Таблица лидеров", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, y_position))
    
    y_position += 50
    for entry in leaderboard:
        score_text = font.render(entry, True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, y_position))
        y_position += 40

    pygame.display.flip()

def show_main_menu():
    menu_running = True
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 36)

    while menu_running:
        screen.blit(background_img, (0, 0))
        title_text = font.render("Выберите уровень сложности", True, BLACK)
        easy_text = small_font.render("1. Легкий", True, BLACK)
        medium_text = small_font.render("2. Средний", True, BLACK)
        hard_text = small_font.render("3. Сложный", True, BLACK)

        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))
        screen.blit(easy_text, (WIDTH // 2 - easy_text.get_width() // 2, HEIGHT // 2 - 40))
        screen.blit(medium_text, (WIDTH // 2 - medium_text.get_width() // 2, HEIGHT // 2))
        screen.blit(hard_text, (WIDTH // 2 - hard_text.get_width() // 2, HEIGHT // 2 + 40))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "easy"
                elif event.key == pygame.K_2:
                    return "medium"
                elif event.key == pygame.K_3:
                    return "hard"
                
def shoot():
    global last_shot_time
    current_time = time() * 1000
    weapon = weapons[current_weapon]

    if current_time - last_shot_time >= weapon["delay"]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        base_angle = pygame.math.Vector2(mouse_x - player.centerx, mouse_y - player.centery).angle_to((1, 0))

        # Увеличение количества пуль при ульте
        additional_bullets = weapon["bullets"] if ult_active else 0
        total_bullets = weapon["bullets"] + additional_bullets

        for i in range(-(total_bullets // 2), (total_bullets // 2) + 1):
            angle = base_angle + i * weapon["spread"]
            direction = pygame.math.Vector2(1, 0).rotate(-angle)
            bullets.append({"rect": pygame.Rect(player.centerx, player.centery, 10, 10), "dir": direction, "damage": weapon["damage"]})

        last_shot_time = current_time

def draw_ult_ui():
    current_time = pygame.time.get_ticks()
    cooldown_progress_ult = (current_time - last_ult_time) / ult_cooldown
    cooldown_progress_ult = min(1, max(0, cooldown_progress_ult))

    cooldown_progress_dash = (current_time - last_dash_time) / dash_cooldown
    cooldown_progress_dash = min(1, max(0, cooldown_progress_dash))

    # Координаты иконок ульты и рывка
    icons_gap = 20  # Расстояние между иконками
    center_x = WIDTH // 2

    # Иконка ульты слева от центра
    ult_icon_x = center_x - ult_icon.get_width() - icons_gap // 2
    ult_icon_y = HEIGHT - 60

    # Иконка рывка справа от центра
    dash_icon_x = center_x + icons_gap // 2
    dash_icon_y = HEIGHT - 60

    # Отрисовка иконок
    screen.blit(ult_icon, (ult_icon_x, ult_icon_y))
    screen.blit(dash_icon, (dash_icon_x, dash_icon_y))

    # Ширина и высота шкал
    bar_width = ult_icon.get_width()
    bar_height = 10

    # Рисуем шкалу перезарядки ульты
    pygame.draw.rect(screen, (200, 200, 200), (ult_icon_x, ult_icon_y + ult_icon.get_height(), bar_width, bar_height))
    pygame.draw.rect(screen, (255, 255, 0), (ult_icon_x, ult_icon_y + ult_icon.get_height(), bar_width * cooldown_progress_ult, bar_height))

    # Рисуем шкалу перезарядки рывка
    pygame.draw.rect(screen, (200, 200, 200), (dash_icon_x, dash_icon_y + dash_icon.get_height(), bar_width, bar_height))
    pygame.draw.rect(screen, (255, 255, 0), (dash_icon_x, dash_icon_y + dash_icon.get_height(), bar_width * cooldown_progress_dash, bar_height))

def spawn_buff():
    global buffs
    x, y = random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)
    buff_type = random.choice(list(buff_types.keys()))
    buffs.append({"rect": pygame.Rect(x, y, 40, 40), "type": buff_type})

def input_name():
    font = pygame.font.Font(None, 36)
    name = ""
    input_active = True
    while input_active:
        screen.fill('black')
        text_surface = font.render(f"Введите ваше имя: {name}", True, WHITE)
        screen.blit(text_surface, (WIDTH // 2 - text_surface.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # Завершаем ввод
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:  # Удалить последний символ
                    name = name[:-1]
                else:
                    name += event.unicode  # Добавляем символ

    return name

current_difficulty = show_main_menu()
enemy_hp = difficulty_levels[current_difficulty]["enemy_hp"]
wave_size = difficulty_levels[current_difficulty]["wave_size"]

while running:
    clock.tick(FPS)
    # screen.blit(background_img, (0, 0))
    screen.fill('black')
    draw_ult_ui()

    # События
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                shooting = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                shooting = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 and "pistol" in unlocked_weapons:
                current_weapon = "pistol"
            elif event.key == pygame.K_2 and "shotgun" in unlocked_weapons:
                current_weapon = "shotgun"
            elif event.key == pygame.K_3 and "rifle" in unlocked_weapons:
                current_weapon = "rifle"
            elif event.key == pygame.K_4 and "sniper" in unlocked_weapons:
                current_weapon = "sniper"
            elif event.key == pygame.K_e:
                current_time = pygame.time.get_ticks()
                if current_time - last_dash_time >= dash_cooldown:
                    dx, dy = 0, 0
                    if keys[pygame.K_w]:
                        dy -= 1
                    if keys[pygame.K_s]:
                        dy += 1
                    if keys[pygame.K_a]:
                        dx -= 1
                    if keys[pygame.K_d]:
                        dx += 1
        
                    # Если есть направление
                    if dx != 0 or dy != 0:
                        dash_direction = pygame.math.Vector2(dx, dy).normalize()
                        dashing = True
                        last_dash_time = current_time
            elif event.key == pygame.K_q:
                current_time = pygame.time.get_ticks()
                if not ult_active and current_time - last_ult_time >= ult_cooldown:
                    ult_active = True
                    ult_start_time = current_time
                    last_ult_time = current_time


    if paused:
        # Отображение текста "Игра на паузе"
        font = pygame.font.Font(None, 74)
        pause_text = font.render("Игра на паузе\nНажмите 'Esc' чтобы продолжить", True, BLACK)
        screen.blit(background_img, (0, 0))  # Отображение фона
        screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))
        pygame.display.flip()
        continue
   
    # Спавн бафов
    current_time = pygame.time.get_ticks()
    if current_time - last_buff_spawn_time > buff_spawn_delay:
        spawn_buff()
        last_buff_spawn_time = current_time

    # Отрисовка и обработка бафов
    for buff in buffs[:]:
        screen.blit(buff_types[buff["type"]]["icon"], buff["rect"])

        if player.colliderect(buff["rect"]):
            buff_type = buff["type"]
            buffs.remove(buff)

            if buff_type == "hp":
                player_hp += buff_types["hp"]["effect"]
                player_hp = min(player_hp, 10)  # Ограничение хп максимум 10
            elif buff_type == "shield":
                active_buffs["shield"] = True
                shield_start_time = current_time
            elif buff_type == "fire_rate":
                active_buffs["fire_rate"] = True
                fire_rate_start_time = current_time
                weapons[current_weapon]["delay"] *= buff_types["fire_rate"]["effect"]

            # Уменьшение длительности временных бафов
            if active_buffs["shield"] and current_time - shield_start_time > buff_types["shield"]["duration"]:
                active_buffs["shield"] = False

            if active_buffs["fire_rate"] and current_time - fire_rate_start_time > buff_types["fire_rate"]["duration"]:
                active_buffs["fire_rate"] = False
                weapons[current_weapon]["delay"] = player_original_fire_delay

    if ult_active:
        current_time = pygame.time.get_ticks()
        if current_time - ult_start_time >= ult_duration:
            ult_active = False

    if dashing:
        dash_target = (
            player.x + dash_direction.x * dash_distance,
            player.y + dash_direction.y * dash_distance,
        )

        # Отрисовка линии рывка
        pygame.draw.line(screen, dash_line_color, player.center, (player.centerx + dash_direction.x * dash_distance, player.centery + dash_direction.y * dash_distance), dash_line_width)
        pygame.draw.line(screen, dash_line_color, player.center, (player.centerx + dash_direction.x * dash_distance, player.centery + dash_direction.y * dash_distance), dash_line_width)
        # Передвижение игрока
        player.x = max(0, min(WIDTH - player.width, dash_target[0]))
        player.y = max(0, min(HEIGHT - player.height, dash_target[1]))
        dashing = False

    # Управление игроком
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] and player.top > 0:
        player.y -= PLAYER_SPEED
    if keys[pygame.K_s] and player.bottom < HEIGHT:
        player.y += PLAYER_SPEED
    if keys[pygame.K_a] and player.left > 0:
        player.x -= PLAYER_SPEED
    if keys[pygame.K_d] and player.right < WIDTH:
        player.x += PLAYER_SPEED

    # Автоматическая стрельба
    if shooting:
        shoot()

    # Спавн врагов
    if enemies_spawned < wave_size and len(enemies) < wave_size:
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time > enemy_spawn_delay:
            spawn_enemy()
            last_spawn_time = current_time

    # Движение врагов
    move_enemies()

    # Урон игроку от врагов
    current_time = pygame.time.get_ticks()
    for enemy in enemies:
        if enemy["rect"].colliderect(player) and current_time - last_damage_time > player_damage_delay:
            if not active_buffs["shield"]:  # Урон только если нет щита
                player_hp -= enemy_damage
                last_damage_time = current_time
            if player_hp <= 0:
                    print('Вы проиграли')
                    name = input_name()  # Вводим имя
                    save_score(name, player_count)  # Сохраняем результат
                    show_leaderboard()  # Показываем таблицу лидеров
                    pygame.time.wait(5000)  # Ждем несколько секунд перед выходом
                    running = False

    # Движение снарядов
    for bullet in bullets[:]:
        bullet["rect"].x += bullet["dir"].x * bullet_speed
        bullet["rect"].y += bullet["dir"].y * bullet_speed
        if not screen.get_rect().contains(bullet["rect"]):
            bullets.remove(bullet)
            continue

        # Проверка столкновения с врагами
        for enemy in enemies[:]:
            if bullet["rect"].colliderect(enemy["rect"]):
                enemy["hp"] -= bullet["damage"]
                if enemy["hp"] <= 0:
                    player_count += 1
                    enemies.remove(enemy)
                bullets.remove(bullet)
                break

        # Проверка столкновения с боссом
        if boss_spawned and bullet["rect"].colliderect(boss["rect"]):
            boss["hp"] -= bullet["damage"]
            if boss["hp"] <= 0:
                print("Босс побежден!")
                player_count += 100
                boss_spawned = False  # Убираем босса из игры
            if bullet in bullets:  # Проверяем, находится ли пуля в списке
                bullets.remove(bullet)  # Удаляем пулю после столкновения


    if unlocked_message:
        current_time = pygame.time.get_ticks()
        if current_time - message_start_time < message_display_time:
            font = pygame.font.Font(None, 36)
            unlock_text = font.render(unlocked_message, True, 'green')
            text_rect = unlock_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(unlock_text, text_rect)
        else:
            unlocked_message = ""

    # Если все враги уничтожены, начинаем новую волну
    if len(enemies) == 0 and enemies_spawned == wave_size:
        current_wave += 1
        enemies_spawned = 0
        wave_size += 5
        if current_wave > waves_per_room:
            current_room += 1
            current_wave = 1
            wave_size = 5
            enemy_speed += 0.5
            enemy_hp += 1
            SAFE_RADIUS = max(50, SAFE_RADIUS - 10)
            if current_room > max_rooms and boss_spawned == False:
                print("Вы прошли все комнаты!")
                name = input_name()  # Вводим имя
                save_score(name, player_count) # Сохраняем результат 
                show_leaderboard()  # Показываем таблицу лидеров
                pygame.time.wait(5000)  # Ждем несколько секунд перед выходом
                running = False

            else:
                # Появление босса в последней комнате
                if current_room == max_rooms:
                    spawn_boss()
                    boss_spawned = True
                    
    for weapon_name, weapon_data in weapons.items():
        if weapon_data["unlock_room"] == current_room and weapon_name not in unlocked_weapons:
            unlocked_weapons.append(weapon_name)
            unlocked_message = f"Вы разблокировали: {weapon_name.capitalize()}!"
            message_start_time = pygame.time.get_ticks()

    # Логика босса
    if boss_spawned:
        if boss["rect"].colliderect(player) and current_time - last_damage_time > player_damage_delay:
            if not active_buffs["shield"]:  # Урон только если нет щита
                player_hp -= enemy_damage
                last_damage_time = current_time
            if player_hp <= 0:
                print("Вы проиграли!")
                name = input_name()  # Вводим имя
                save_score(name, player_count)  # Сохраняем результат
                show_leaderboard()  # Показываем таблицу лидеров
                pygame.time.wait(5000)  # Ждем несколько секунд перед выходом
                running = False


        # Движение босса к игроку
        if boss["rect"].x < player.x:
            boss["rect"].x += 1
        if boss["rect"].x > player.x:
            boss["rect"].x -= 1
        if boss["rect"].y < player.y:
            boss["rect"].y += 1
        if boss["rect"].y > player.y:
            boss["rect"].y -= 1

        # Отображение босса
        screen.blit(boss_img, boss["rect"])

    # Анимация игрока
    current_time = pygame.time.get_ticks()
    if current_time - last_frame_update_time > player_frame_delay:
        player_frame_index = (player_frame_index + 1) % len(player_frames)
        last_frame_update_time = current_time
    
    # Отрисовка текущего кадра
    current_player_frame = player_frames[player_frame_index]
    screen.blit(current_player_frame, player)

    # Отрисовка врагов
    for enemy in enemies:
        screen.blit(enemy_img, enemy["rect"])

    # Отрисовка снарядов
    for bullet in bullets:
        screen.blit(bullet_img, bullet["rect"])

    # Интерфейс
    font = pygame.font.Font(None, 36)
    hp_text = font.render(f"HP: {player_hp}", True, WHITE)
    weapon_text = font.render(f"Weapon: {current_weapon}", True, WHITE)
    room_text = font.render(f"Room: {current_room}/{max_rooms}", True, WHITE)
    wave_text = font.render(f"Wave: {current_wave}/{waves_per_room}", True, WHITE)
    screen.blit(hp_text, (10, 10))
    screen.blit(weapon_text, (10, 50))
    screen.blit(room_text, (10, 90))
    screen.blit(wave_text, (10, 130))

    # Обновление экрана
    pygame.display.flip()

conn.close()
pygame.quit()