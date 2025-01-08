import pygame
import random
from time import time

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 30 
PLAYER_SPEED = 5
SAFE_RADIUS = 150

player_img = pygame.image.load("game_assets/player.png")
enemy_img = pygame.image.load("game_assets/enemy.png")
bullet_img = pygame.image.load("game_assets/bullet.png")
background_img = pygame.image.load("game_assets/background.png")

player_img = pygame.transform.scale(player_img, (50, 50))
enemy_img = pygame.transform.scale(enemy_img, (40, 40))
bullet_img = pygame.transform.scale(bullet_img, (10, 10))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Room-Based Game with Pistol Only")
clock = pygame.time.Clock()

player = pygame.Rect(WIDTH // 2, HEIGHT // 2, 50, 50)
player_hp = 10
player_damage_delay = 1000  
last_damage_time = 0

weapon = {"damage": 1, "delay": 300}  
last_shot_time = 0
shooting = False

enemies = []
enemy_speed = 2
enemy_hp = 3
enemy_damage = 1
wave_size = 5
current_wave = 0
waves_per_room = 3
current_room = 1
max_rooms = 6
enemies_spawned = 0
last_spawn_time = 0
enemy_spawn_delay = 2000

bullets = []
bullet_speed = 10

def spawn_enemy():
    global enemies_spawned
    x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
    while abs(x - player.centerx) <= SAFE_RADIUS and abs(y - player.centery) <= SAFE_RADIUS:
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
    enemies.append({"rect": pygame.Rect(x, y, 40, 40), "hp": enemy_hp})
    enemies_spawned += 1

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

def shoot():
    global last_shot_time
    current_time = time() * 1000  

    if current_time - last_shot_time >= weapon["delay"]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        direction = pygame.math.Vector2(mouse_x - player.centerx, mouse_y - player.centery).normalize()
        
        bullets.append({"rect": pygame.Rect(player.centerx, player.centery, 10, 10), "dir": direction,
                        "damage": weapon["damage"]})

        last_shot_time = current_time

running = True
while running:
    clock.tick(FPS)
    screen.blit(background_img, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  
            shooting = True
            
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            shooting = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] and player.top > 0:
        player.y -= PLAYER_SPEED
    if keys[pygame.K_s] and player.bottom < HEIGHT:
        player.y += PLAYER_SPEED
    if keys[pygame.K_a] and player.left > 0:
        player.x -= PLAYER_SPEED
    if keys[pygame.K_d] and player.right < WIDTH:
        player.x += PLAYER_SPEED

    if shooting:
        shoot()

    if enemies_spawned < wave_size and len(enemies) < wave_size:
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time > enemy_spawn_delay:
            spawn_enemy()
            last_spawn_time = current_time
            
    move_enemies()

    current_time = pygame.time.get_ticks()
    for enemy in enemies:
        if enemy["rect"].colliderect(player) and current_time - last_damage_time > player_damage_delay:
            player_hp -= enemy_damage
            last_damage_time = current_time
            if player_hp <= 0:
                print("Вы проиграли!")
                running = False

    for bullet in bullets[:]:
        bullet["rect"].x += bullet["dir"].x * bullet_speed
        bullet["rect"].y += bullet["dir"].y * bullet_speed
        
        if not screen.get_rect().contains(bullet["rect"]):
            bullets.remove(bullet)
            continue

        for enemy in enemies[:]:
            if bullet["rect"].colliderect(enemy["rect"]):
                enemy["hp"] -= bullet["damage"]
                if enemy["hp"] <= 0:
                    enemies.remove(enemy)
                bullets.remove(bullet)
                break

    if len(enemies) == 0 and enemies_spawned == wave_size:
        current_wave += 1
        enemies_spawned = 0
        
        wave_size += 5  
        
        if current_wave > waves_per_room:
            current_room += 1 
            current_wave = 1 
            wave_size = 5  
            
            if current_room > max_rooms:
                print("Вы прошли все комнаты!")
                running = False

    screen.blit(player_img, player)

    for enemy in enemies:
        screen.blit(enemy_img, enemy["rect"])

    for bullet in bullets:
        screen.blit(bullet_img, bullet["rect"])

    font = pygame.font.Font(None, 36)
    
    hp_text = font.render(f"HP: {player_hp}", True, 'white')
    room_text = font.render(f"Room: {current_room}/{max_rooms}", True, 'white')
    wave_text = font.render(f"Wave: {current_wave}/{waves_per_room}", True, 'white')
    
    screen.blit(hp_text, (10, 10))
    screen.blit(room_text, (10, 50))
    screen.blit(wave_text, (10, 90))

    pygame.display.flip()

pygame.quit()
