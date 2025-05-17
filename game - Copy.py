import pygame, sys, time, random, math, pytmx.util_pygame
pygame.init()

WIDTH = 960 * 1.25
HEIGHT = WIDTH / 2
prev_time = time.time()

window = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.SysFont("arial", 30)
font2 = pygame.font.Font("data/oldeenglish.ttf", 30)

walk_spritesheet = pygame.transform.scale_by(pygame.image.load("data/graphics/player/WALK.png"), 2)
idle_spritesheet = pygame.transform.scale_by(pygame.image.load("data/graphics/player/IDLE.png"), 2)

class Player(pygame.sprite.Sprite):
    def __init__(self, platforms, ref_platform, chest_sprites):
        super().__init__()
        self.current_spritesheet = idle_spritesheet

        self.status = "idle_right"
        scale = 3
        self.animation_dictionary = {
                                     "idle_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/idle/{x}.png").convert_alpha(), scale) for x in range(0, 7)],
                                     "idle_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/idle/{x}.png").convert_alpha(), scale) for x in range(0, 7)]],
                                     "walk_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/run/{x}.png").convert_alpha(), scale) for x in range(0, 8)],
                                     "walk_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/run/{x}.png").convert_alpha(), scale) for x in range(0, 8)]],
                                     "jump_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/jump/jump/{x}.png").convert_alpha(), scale) for x in range(0, 9)],
                                     "jump_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/jump/jump/{x}.png").convert_alpha(), scale) for x in range(0, 9)]],
                                     "attack1_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/attack1/{x}.png").convert_alpha(), scale) for x in range(0, 6)],
                                     "attack1_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/attack1/{x}.png").convert_alpha(), scale) for x in range(0, 6)]],
                                     "attack2_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/attack2/{x}.png").convert_alpha(), scale) for x in range(0, 6)],
                                     "attack2_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/attack2/{x}.png").convert_alpha(), scale) for x in range(0, 6)]],
                                     "attack3_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/attack3/{x}.png"), scale).convert_alpha() for x in range(0, 6)],
                                     "attack3_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/attack3/{x}.png"), scale).convert_alpha() for x in range(0, 6)]],
                                     "defend_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/defend/{x}.png"), scale).convert_alpha() for x in range(0, 9)],
                                     "defend_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/defend/{x}.png"), scale).convert_alpha() for x in range(0, 9)]],
                                     "dead_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/dead/{x}.png"), scale).convert_alpha() for x in range(0, 31)],
                                     "dead_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/player/dead/{x}.png"), scale).convert_alpha() for x in range(0, 31)]]
                                     }
        self.image = self.animation_dictionary[self.status][0]
        self.rect = self.image.get_rect(center = (200, 200))
        self.rect.inflate_ip(-20, 0)
        self.direction = "right"
        self.surround_box =  self.rect.inflate(3, 3)
        self.attacking = False
        self.last_attack_time = 0
        self.attack_status = ""
        self.defending = False
        self.last_defend_time = 0
        self.on_moving_platform = False

        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, 0)
        self.platforms = platforms

        self.in_air = True

        self.coords = [self.rect.centerx, self.rect.centery]
        self.ref_platform = ref_platform

        self.frame_index = 0
        self.health = 5
        self.max_health = self.health
        self.display_health = self.max_health
        self.invincible = False
        self.last_damage_time = 0
        self.chests = chest_sprites
        self.dead = False

        self.wasted = pygame.transform.scale_by(pygame.image.load("data/wasted.png").convert_alpha(), 0.1)
        self.can_play_sound = False
        self.can_play_sound2 = False
        self.sfx = pygame.mixer.Sound("data/missionfailed.ogg")
        self.sfx2 = pygame.mixer.Sound("data/getout.ogg")

        self.dir = pygame.math.Vector2()
        self.prev_rect = self.rect.copy()
        self.speed = 7
        self.gravity = 1.2
        self.jump_speed = 30
        self.on_floor = False
        self.jump_press_lock = False
        self.max_vel = 0
        self.added_velocity = pygame.math.Vector2()

        self.acceleration = pygame.math.Vector2()
        self.acceleration.y = self.gravity
        self.acceleration.x = 0

        self.center_axis = self.image.get_width() / 2
        self.index1 = 0
        self.index2 = 0

        self.screenshake = 0
        self.camshake = 0
        self.last_ground_hit = 0
        self.hit_ground = False

    def input(self):
        self.keys = pygame.key.get_pressed()
        if self.keys[pygame.K_a] and not self.attack_status and not self.defending:
            self.dir.x = -1
            if self.status not in ["jump_left", "jump_right"]: self.status = "walk_left"
            self.direction = "left"
        elif self.keys[pygame.K_d] and not self.attack_status and not self.defending:
            self.dir.x = 1
            if self.status not in ["jump_left", "jump_right"]: self.status = "walk_right"
            self.direction = "right"
        else:
            self.dir.x = 0
            if self.status not in ["jump_left", "jump_right"]:
                if self.direction == "right":
                    self.status = "idle_right"
                if self.direction == "left":
                    self.status = "idle_left"

        if self.keys[pygame.K_w] and self.on_floor and not self.jump_press_lock:
            self.dir.y = -self.jump_speed# * dt
            if self.direction == "right":
                self.status = "jump_right"
            if self.direction == "left":
                self.status = "jump_left"
            self.jump_press_lock = True
            self.on_moving_platform = False
            self.added_velocity.x = 0

        #if self.on_floor and self.keys[pygame.K_w] and :
            #self.jump_press_lock = True

    def check_contact(self):
        self.bottom_rect = pygame.Rect(0, 0, self.rect.width, 5)
        self.bottom_rect.midtop = self.rect.midbottom
        for sprite in self.platforms:
            if sprite.rect.colliderect(self.bottom_rect) and sprite.collideable:
                self.on_floor = True

    def move(self, dt):
        if not self.dead: self.input()
        else: self.dir.x = 0

        #self.rect.x += self.dir.x * dt * self.speed + self.added_velocity.x * dt
        self.rect.x += (self.dir.x) * dt * self.speed + 0.5 * self.acceleration.x * dt * dt + self.added_velocity.x
        self.acceleration.y = self.gravity
        self.collision("horizontal")

        self.dir.y += self.gravity * dt#/ 2# * dt
        #self.rect.y += self.dir.y * dt + self.added_velocity.y * dt
        self.rect.y += self.dir.y * dt + 0.5 * self.acceleration.y * dt * dt
       # self.dir.y += self.gravity / 2# * dt
        self.collision("vertical")

        self.max_vel = max(self.max_vel, self.dir.y * dt)

        inflate_rect = pygame.Rect(0, 0, self.rect.width, 50)
        inflate_rect.midtop = self.rect.midbottom
        in_range = False
        for platform in self.platforms:
            if inflate_rect.colliderect(platform.rect) and platform.collideable:
                in_range = True
        if self.dir.y * dt > 40 and in_range and False:
            if self.direction == "right":
                self.status = "dead_right"
            if self.direction == "left":
                self.status = "dead_left"
            if int(self.frame_index) != 0:
                self.frame_index = 0   


        last_row = []
        for x in range(0, self.image.get_width()):
            last_row.append(self.image.get_at((x, self.image.get_height() - 1)))

        index1 = 0
        for item in last_row:
            index1 += 1
            if item == (27, 27, 27, 255):
                 break
        index2 = 0
        #for item in list(reversed(last_row)):
            #index2 += 1
            #if item == (27, 27, 27, 255):
                #break

        index2 = len(last_row) - index2
        index2 = len(last_row) - 1 - last_row[::-1].index((27, 27, 27, 255))
        self.center_axis = (index1 + index2) / 2
        self.index1 = index1
        self.index2 = index2

    
    def collision(self, direction):
        for sprite in self.platforms:
            if sprite.rect.colliderect(self.rect) and sprite.collideable:
                if sprite in spikes.sprites():
                    if self.direction == "left":
                        self.status = "dead_left"
                    if self.direction == "right":
                        self.status = "dead_right"
                if direction == "horizontal" and not sprite.oneway:
                    if self.rect.left <= sprite.rect.right and self.prev_rect.left >= sprite.prev_rect.right:
                        self.rect.left = sprite.rect.right
                        self.status = "idle_left"      
                                          
                    if self.rect.right >= sprite.rect.left and self.prev_rect.right <= sprite.prev_rect.left:
                        self.rect.right = sprite.rect.left
                        self.status = "idle_right"

                if direction == "vertical":
                    if self.rect.bottom >= sprite.rect.top and self.prev_rect.bottom <= sprite.prev_rect.top:
                        if self.status == "jump_left" or self.status == "jump_right":
                            self.screenshake = 30
                            self.hit_ground = True
                            
                        self.rect.bottom = sprite.rect.top
                        self.on_floor = True
                        self.dir.y = 0
                        self.acceleration.y = 0

                        if self.direction == "right" and self.status in ["jump_right", "jump_left"]:
                            self.status = "idle_right"
                        if self.direction == "left" and self.status in ["jump_right", "jump_left"]:
                            self.status = "idle_left"

                        if self.jump_press_lock and not self.keys[pygame.K_w]:
                            self.jump_press_lock = False
                        else:
                            if self.keys[pygame.K_w]:
                                self.jump_press_lock = True
                        
                        if hasattr(sprite, "moving") and sprite.moving:
                            self.on_moving_platform = True
                        else:
                            self.on_moving_platform = False
                            self.added_velocity.x = 0
                    else:
                        self.on_moving_platform = False
                        self.added_velocity.x = 0

                    if self.rect.top <= sprite.rect.bottom and self.prev_rect.top >= sprite.prev_rect.bottom and not sprite.oneway:
                        self.rect.top = sprite.rect.bottom
                        if not sprite.oneway:
                            self.dir.y = 0
                            self.acceleration.y = 0

        if not self.hit_ground:
            self.screenshake = 0

        if self.on_floor and self.dir.y != 0:
            self.on_floor = False
        
        if self.screenshake > 0:
            self.screenshake -= 1
            print(random.randint(0,10))
            self.camshake = random.randint(-8,8)
        else:
            for sprite in all_sprites:
                sprite.rect.x -= self.camshake
            self.camshake = 0

    def attack_check(self): 
        if pygame.mouse.get_pressed()[0] and self.status in ["idle_right", "idle_left", "walk_right", "walk_left"] and not self.dead and not self.attack_status and pygame.time.get_ticks() - self.last_attack_time > 300 and not self.dead:
            self.attacking = True
            if self.direction == "right":
                self.attack_status = random.choice(["attack1_right", "attack2_right", "attack3_right"])
            if self.direction == "left":
                self.attack_status = random.choice(["attack1_left", "attack2_left", "attack3_left"])
            self.last_attack_time = pygame.time.get_ticks()
            self.frame_index = 0

    def animate(self, xdt):
        speed = 0.2
        self.frame_index += speed * xdt
        if self.frame_index >= len(self.animation_dictionary[self.status]):
            self.frame_index = 0
        self.image = self.animation_dictionary[self.status][int(self.frame_index)]
        self.surround_box =  self.rect.inflate(3, 3)

    def defend(self):
        if pygame.mouse.get_pressed()[2] and not self.defending and not self.dead:
            self.defending = True
            self.frame_index = 0
        if self.defending:
            if self.direction == "right":
                self.status = "defend_right"
            if self.direction == "left":
                self.status = "defend_left"
            if self.frame_index >= len(self.animation_dictionary[self.status]) - 1:
                self.defending = False

    def interact_with_chests(self):
        for chest in self.chests:
            if ((chest.rect.centerx - self.rect.centerx) ** 2 + (chest.rect.centery - self.rect.centery) ** 2) ** 0.5 < 200:
                if self.keys[pygame.K_e] and chest.status == "unopened" and not self.dead:
                    chest.status = "opening"
                    chest.frame_index = 0

    def display_health_bar(self):
        ratio = self.health / self.max_health
        if ratio >= 0:
            ratio = self.health / self.max_health
        else:
            ratio = 0
        health_bar_length = 30 + self.rect.width

        difference = self.health - self.display_health
        self.display_health += difference * 0.05
        if self.display_health < 0:
            self.display_health = 0

        #if not self.dead:
            #pygame.draw.rect(window, "red", pygame.Rect(self.rect.left - 15 + offset.x, self.rect.top - 20 + offset.y, health_bar_length, 10), border_radius = 5)
            #pygame.draw.rect(window, "yellow", pygame.Rect(self.rect.left - 15 + offset.x, self.rect.top - 20 + offset.y, self.display_health / self.max_health * health_bar_length, 10), border_radius = 5) 
            #pygame.draw.rect(window, "green", pygame.Rect(self.rect.left - 15 + offset.x, self.rect.top - 20 + offset.y, ratio * health_bar_length, 10), border_radius = 5)

        pygame.draw.rect(window, "red", pygame.Rect(20, HEIGHT - 50, health_bar_length * 4, 30), border_radius = 5)
        pygame.draw.rect(window, "yellow", pygame.Rect(20, HEIGHT - 50, self.display_health / self.max_health * health_bar_length * 4, 30), border_radius = 5) 
        pygame.draw.rect(window, "green", pygame.Rect(20, HEIGHT - 50, ratio * health_bar_length * 4, 30), border_radius = 5)

        if self.health == 0:
            self.frame_index = 0
            self.can_play_sound = True
            self.health = -1
            if self.direction == "right":
                self.status = "dead_right"
            if self.direction == "left":
                self.status = "dead_left"
            self.dir.x = 0

        if self.frame_index >= len(self.animation_dictionary[self.status]) - 1 and self.status in ["dead_right", "dead_left"]:
            for monster in self.monsters:
                monster.health = monster.max_health
            self.frame_index = 0
            self.status = "idle_right"
            self.health = 5
            self.rect.center = (200, 200)
            self.dir = pygame.math.Vector2()

        if self.status in ["dead_right", "dead_left"]:
            self.dead = True
            window.blit(self.wasted, (WIDTH / 2 - self.wasted.get_width() / 2, HEIGHT / 2 - self.wasted.get_height() / 2 + 00))
        else:
            self.dead = False

        if self.can_play_sound:
            self.sfx.play()
            self.can_play_sound = False


    def update(self, xdt):
        self.prev_rect = self.rect.copy()
        self.keys = pygame.key.get_pressed()
        #if self.status not in ["dead_right", "dead_left"]:
        self.move(dt)
        self.check_contact()

        self.attack_check()
        if self.attacking and self.attack_status and self.frame_index < len(self.animation_dictionary[self.attack_status]) - 1 and not self.defending:
            self.status = self.attack_status
        else:
            self.attack_status = ""
        
        self.defend()
        self.interact_with_chests()
        self.animate(xdt)
        self.display_health_bar()

        if self.status in ["attack1_left", "attack2_left", "attack3_left", "attack1_right", "attack2_right", "attack3_right", "defend_left", "defend_right"]:
            self.dir.x = 0

        self.health_before = self.health

        for monster in self.monsters:
            if (monster.distance_to_player < 120) and (monster.attacking) and (monster.status in ["attack1_right", "attack2_right", "attack1_left", "attack2_left"]) and (not self.invincible) and (4 <= int(monster.frame_index) <= 6):
                if not self.defending:
                    self.health -= 1
                    for x in range(random.randint(30, 60)): Particle(self.rect.center, "red", all_sprites, platforms)
                    self.invincible = True
                    self.last_damage_time = pygame.time.get_ticks()
                    # note : fixed added velocity with movong platforms
                    # BROKEN : monster blood particle system
                else:
                    self.defending = True
                    self.health = self.health_before
            if self.attack_status and monster.distance_to_player < 120 and pygame.time.get_ticks() - monster.last_damage_time > 1000:
                if ((self.status == "attack1_right" or self.status == "attack1_left") and int(self.frame_index) >= 1) or ((self.status == "attack2_right" or self.status == "attack2_left") and int(self.frame_index) >= 2) or ((self.status == "attack3_right" or self.status == "attack3_left") and int(self.frame_index) >= 2) and monster.status not in ["dead_right", "dead_left"] and monster.health >= 0 and monster.rect.width and monster.rect.height:
                    monster.health -= 1
                    monster.last_damage_time = pygame.time.get_ticks()
                    if monster.direction == "right" and not monster.status in ["hit_left", "hit_right"]:
                        monster.status = "hit_right"
                    if monster.direction == "left" and not monster.status in ["hit_left", "hit_right"]:
                        monster.status = "hit_left"
                    if monster.status not in ["dead_left", "dead_right"]:
                        for x in range(random.randint(30, 60)): Particle(monster.rect.center, "red", all_sprites, platforms)


        if self.invincible and pygame.time.get_ticks() - self.last_damage_time > 1000:
            self.invincible = False

        if self.rect.y > 3000:
            self.rect.center = (0, 0)

class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, color, groups, platforms):
        super().__init__()
        self.pos = pos
        self.color = color
        self.add(groups)

        self.gravity = 0.5
        self.velocity = pygame.Vector2(random.randint(-300, 300), random.randint(-1000, 300))
        self.velocity /= 100

        self.side = random.randint(3, 6)
        self.image = pygame.Surface((self.side, self.side))
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center = self.pos)
        #self.image = pygame.Surface((self.side, self.side))
        self.image.convert_alpha()

        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.side, self.side)
        self.platforms = platforms.sprites()
        self.rect.x += random.randint(-10, 10)
        self.rect.y += random.randint(-10, 10)
        self.last_hit_time = 0
        self.dead = False

    def update(self, dt):
        if self.dead:
            hit = True
        else:
            hit = False
        for platform in self.platforms:
            if self.rect.colliderect(platform.rect) and platform.collideable and not self.dead and not hasattr(platform, "chest"):
                hit = True
                self.dead = True
                self.last_hit_time = pygame.time.get_ticks()
        if not hit:
            self.rect.center += self.velocity * dt
            self.pos += self.velocity * dt
            self.velocity.y += self.gravity * dt
        else:
            self.velocity.x = 0
            self.velocity.y = 0
        if hit and pygame.time.get_ticks() - self.last_hit_time > 1000:
            self.kill()

        #pygame.draw.circle(self.image, "red", self.pos, self.side)

class Deathbringer(pygame.sprite.Sprite):
    def __init__(self, type, coords, groups, player):
        super().__init__()
        for group in groups:
            self.add(group)
        sf = 3
        self.animations_dictionary = {
            "idle_left": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/death_bringer/idle/{x}.png"), sf) for x in range(0, 8)],
            "idle_right": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/death_bringer/idle/{x}.png"), sf) for x in range(0, 8)]],
            "attack_left": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/death_bringer/attack/{x}.png"), sf) for x in range(0, 9)],
            "attack_right": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/death_bringer/attack/{x}.png"), sf) for x in range(0, 9)]],
            "walk_left": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/death_bringer/walk/{x}.png"),sf) for x in range(0, 8)],
            "walk_right": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/death_bringer/walk/{x}.png"),sf) for x in range(0, 8)]]

        }
        self.status = "idle_left"
        self.image = self.animations_dictionary[self.status][0]
        self.frame_index = 0
        self.rect = self.image.get_rect(bottomleft = coords)
        self.player = player
        #self.coords = self.rect.midbottom
        self.notice_radius = 500
        self.draw = False

    def update(self, dt):
        self.frame_index += 0.1 * dt
        if self.frame_index > len(self.animations_dictionary[self.status]):
            self.frame_index = 0
        self.image = self.animations_dictionary[self.status][int(self.frame_index)]
        self.hitbox = self.rect
        #self.rect = self.image.get_rect(topleft = self.coords)

        if self.status == "idle_left" or self.status == "idle_right":
            self.coords = self.rect.midbottom
            self.rect = self.image.get_rect(midbottom = self.coords)
        if self.status == "attack_left":
            self.coords = (self.rect.left + self.rect.width * 3 / 4, self.rect.bottom)
            self.rect = self.image.get_rect(bottomright = (self.coords[0] + self.rect.width * 1 / 4, self.coords[1]))
        if self.status == "attack_right":
            self.coords = (self.rect.left + self.rect.width * 1 / 4, self.rect.bottom)
            self.rect = self.image.get_rect(bottomleft = (self.coords[0] - self.rect.width * 1 / 4, self.coords[1]))     

        self.distance_to_player = math.sqrt((self.rect.centerx - self.player.rect.centerx) ** 2 + (self.rect.centery - self.player.rect.centery) ** 2)
        if self.player.rect.right < self.rect.left:
            if self.distance_to_player < self.notice_radius:
                self.status = "walk_left"
                self.rect.x -= 3 * dt
            else:
                self.status = "idle_left"
        if self.player.rect.left > self.rect.right:
            if self.distance_to_player < self.notice_radius:
                self.status = "walk_right"
                self.rect.x += 3 * dt
            else:
                self.status = "idle_right"


class Imp(pygame.sprite.Sprite):
    def __init__(self, pos, groups, player, left_bound, right_bound):
        super().__init__()
        for group in groups:
            self.add(groups)
        self.player = player
        self.pos = pos

        sf = 3.5
        self.animations_dictionary = {
            "idle_right" : [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/idle/ready_{x}.png"), sf) for x in range(1, 7)], 
            "idle_left" : [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/idle/ready_{x}.png"), sf) for x in range(1, 7)]],
            "walk_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/walk/walk_{x}.png"), sf) for x in range(1, 7)],
            "walk_left" : [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/walk/walk_{x}.png"), sf) for x in range(1, 7)]],
            "run_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/run/run_{x}.png"), sf) for x in range(1, 7)],
            "run_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/run/run_{x}.png"), sf) for x in range(1, 7)]],
            "attack1_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/attack1/attack1_{x}.png"), sf) for x in range(1, 7)],
            "attack1_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/attack1/attack1_{x}.png"), sf) for x in range(1, 7)]],
            "hit_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/hit/hit_{x}.png"), sf) for x in range(1, 4)],
            "hit_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/hit/hit_{x}.png"), sf) for x in range(1, 4)]],
            "dead_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/dead/fall_back_{x}.png"), sf) for x in range(1, 6)],
            "dead_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/dead/fall_back_{x}.png"), sf) for x in range(1, 6)]],
            "attack2_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/attack2/attack2_{x}.png"), sf) for x in range(1, 6)],
            "attack2_left" : [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/imp/attack2/attack2_{x}.png"), sf) for x in range(1, 6)]]
        }
        self.status = "walk_left"
        self.image = self.animations_dictionary[self.status][0]
        self.rect = self.image.get_rect(bottomleft = pos)
        self.frame_index = 0
        self.draw = False
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.direction = "left"
        self.attacking = False
        self.pos_switch = False
        self.health = 3
        self.max_health = self.health
        self.invincible = False
        self.last_damage_time = 0
        self.hit = False
        self.dead_flag = False
        self.display_health = self.max_health
        self.dead = False


    def animate(self, dt):
        self.frame_index += 0.05 * dt
        if self.frame_index > len(self.animations_dictionary[self.status]):
            self.frame_index = 0
            if self.attacking:
                self.attacking = False
                if self.direction == "left":
                    self.status = "walk_left"
                if self.direction == "right":
                    self.status = "walk_right"

            if self.status in ["hit_left", "hit_right"]:
                self.hit = False
                if self.direction == "left":
                    self.status = "walk_left"
                if self.direction == "right":
                    self.status = "walk_right"               

            self.frame_index = 0
        self.image = self.animations_dictionary[self.status][int(self.frame_index)]

    def calibrate_rect(self):
        if self.status in ["run_right", "walk_left", "idle_left"]:
            self.rect = self.image.get_rect(bottomleft = self.pos)
        if self.status in ["run_left", "walk_right", "idle_right"]:
            self.rect = self.image.get_rect(bottomright = (self.pos[0] + self.image.get_width(), self.pos[1]))
        if self.status == "attack1_right" or self.status == "hit_right" or self.status == "attack2_left":
            self.rect = self.image.get_rect(midbottom = (self.pos[0], self.pos[1]))
        if self.status == "attack1_left" or self.status == "hit_left" or self.status == "attack2_left":
            self.rect = self.image.get_rect(midbottom = (self.pos[0], self.pos[1]))
        if self.status == "dead_right":
            self.rect = self.image.get_rect(bottomright = (self.pos[0] + self.rect.width, self.pos[1]))
        if self.status == "dead_left":
            self.rect = self.image.get_rect(bottomleft=  (self.pos[0], self.pos[1]))
        self.hitbox = self.rect

    def manage_status(self, dt):
        if (self.status == "hit_right" or self.status == "hit_left") and self.health >= 0 and self.status not in ["dead_left", "dead_right"]:
            self.hit = True
        else:
            self.hit = False
        self.distance_to_player = ((self.rect.centerx - self.player.rect.centerx) ** 2 + (self.rect.centery - self.player.rect.centery) ** 2) ** 0.5
        if self.direction == "left" and not self.hit and self.health > 0 and "attack" not in self.status:
            if self.status != "attack1_left" and self.status != "attack2_left":
                self.pos[0] -= dt
            if self.rect.left < self.left_bound and self.rect.right > self.left_bound:
                self.direction = "right"
        if self.direction == "right" and not self.hit and self.health > 0 and "attack" not in self.status:
            if self.status != "attack1_right" and self.status != "attack2_right":
                self.pos[0] += dt
            if self.rect.right > self.right_bound and self.rect.left < self.right_bound:
                self.direction = "left"

        if self.direction == "left" and self.status not in ["attack1_left", "attack1_right", "hit_left", "hit_right", "dead_right", "dead_left", "attack2_right", "attack2_left"]:
            self.status = "walk_left"
        if self.direction == "right" and self.status not in ["attack1_left", "attack1_right", "hit_left", "hit_right", "dead_right", "dead_left", "attack2_right", "attack2_left"]:
            self.status = "walk_right"

        if self.left_bound < self.player.rect.centerx < self.right_bound and not self.hit and self.health > 0:
            if self.player.rect.right < self.rect.left and self.player.rect.left < self.rect.left and self.status == "walk_left":
                self.status = "run_left"
                self.pos[0] -= dt
            elif self.player.rect.left > self.rect.right and self.player.rect.right > self.rect.right and self.status == "walk_right":
                self.status = "run_right"
                self.pos[0] += dt

        if self.distance_to_player < 90 and not self.attacking and not self.hit and self.health > 0:
            self.frame_index = 0
            self.attacking = True
            if self.status == "run_right":
                self.status = random.choice(["attack1_right", "attack2_right"])
                self.status = "attack1_right"
            if self.status == "run_left":
                self.status = random.choice(["attack1_left", "attack2_left"])
                self.status = "attack1_left"

    def death_check(self):
        self.health = max(0, self.health)
        if self.health == 0 and self.status not in ["dead_right", "dead_left"]:
            if self.direction == "right":
                self.status = "dead_right"
            if self.direction == "left":
                self.status = "dead_left"
            self.dead_flag = True
            self.health = -1
        
        if self.dead_flag:
            self.dead_flag = False
            self.frame_index = 0
        if self.health == 0:
            if self.direction == "right":
                self.status = "dead_right"
            if self.direction == "left":
                self.status = "dead_left"
        if self.frame_index >= len(self.animations_dictionary[self.status]) - 1 and self.status in ["dead_right", "dead_left"]:
            self.frame_index = len(self.animations_dictionary[self.status]) - 1
            self.player.health = min(self.player.max_health, self.player.health + 1)
            self.dead = True
            #self.kill()

    def display_health_bar(self):
        ratio = self.health / self.max_health
        if ratio >= 0:
            ratio = self.health / self.max_health
        else:
            ratio = 0
        health_bar_length = 30 + self.animations_dictionary["idle_left"][0].get_size()[0]
        height_above = self.animations_dictionary["idle_left"][0].get_size()[1]

        difference = self.health - self.display_health
        self.display_health += difference * 0.05

        pygame.draw.rect(window, "red", pygame.Rect(self.rect.centerx - health_bar_length / 2 + offset.x, self.rect.bottom - height_above - 20 + offset.y, health_bar_length, 10), border_radius = 5)
        pygame.draw.rect(window, "yellow", pygame.Rect(self.rect.centerx - health_bar_length / 2 + offset.x, self.rect.bottom - height_above - 20 + offset.y, self.display_health / self.max_health * health_bar_length, 10), border_radius = 5) 
        pygame.draw.rect(window, "green", pygame.Rect(self.rect.centerx - health_bar_length / 2 + offset.x, self.rect.bottom - height_above - 20 + offset.y, ratio * health_bar_length, 10), border_radius = 5)

    
    def update(self, dt):
        if not self.dead:
            self.animate(dt)
            self.calibrate_rect()
            if self.health > 0:
                self.display_health_bar()
            self.manage_status(dt)
            self.death_check()

class Axeman(pygame.sprite.Sprite):
    def __init__(self, pos, groups, player, left_bound, right_bound):
        super().__init__()
        for group in groups:
            self.add(groups)
        self.player = player
        self.pos = pos

        scale = 4
        self.animations_dictionary = {
            "idle_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/idle/ready_{x}.png"), scale) for x in range(1, 7)],
            "idle_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/idle/ready_{x}.png"), scale) for x in range(1, 7)]],
            "attack1_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/attack1/attack1_{x}.png"), scale) for x in range(1, 7)],
            "attack1_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/attack1/attack1_{x}.png"), scale) for x in range(1, 7)]],
            "attack2_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/attack2/attack2_{x}.png"), scale) for x in range(1, 7)],
            "attack2_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/attack2/attack2_{x}.png"), scale) for x in range(1, 7)]],
            "walk_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/walk/walk_{x}.png"), scale) for x in range(1, 7)],
            "walk_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/walk/walk_{x}.png"), scale) for x in range(1, 7)]],
            "run_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/run/run_{x}.png"), scale) for x in range(1, 7)],
            "run_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/run/run_{x}.png"), scale) for x in range(1, 7)]],
            "hit_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/hit/hit_{x}.png"), scale) for x in range(1, 4)],
            "hit_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/hit/hit_{x}.png"), scale) for x in range(1, 4)]],
            "dead_right": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/dead/dead_{x}.png"), scale) for x in range(1, 5)],
            "dead_left": [pygame.transform.flip(item, True, False) for item in [pygame.transform.scale_by(pygame.image.load(f"data/graphics/axeman/dead/dead_{x}.png"), scale) for x in range(1, 5)]]
        }
        self.status = "walk_left"
        self.image = self.animations_dictionary[self.status][0]
        self.rect = self.image.get_rect(bottomleft = pos)
        self.frame_index = 0
        self.draw = False
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.direction = "left"
        self.attacking = False
        self.pos_switch = False
        self.health = 3
        self.max_health = self.health
        self.invincible = False
        self.last_damage_time = 0
        self.hit = False
        self.dead_flag = False
        self.display_health = self.max_health
        self.dead = False

    def animate(self, dt):
        self.frame_index += 0.05 * dt
        if self.frame_index > len(self.animations_dictionary[self.status]):
            self.frame_index = 0
            if self.attacking:
                self.attacking = False
                if self.direction == "left":
                    self.status = "walk_left"
                if self.direction == "right":
                    self.status = "walk_right"

            if self.status in ["hit_left", "hit_right"]:
                self.hit = False
                if self.direction == "left":
                    self.status = "walk_left"
                if self.direction == "right":
                    self.status = "walk_right"               

            self.frame_index = 0
        self.image = self.animations_dictionary[self.status][int(self.frame_index)]

    def calibrate_rect(self):
        if self.status in ["run_right", "walk_left", "idle_left"]:
            self.rect = self.image.get_rect(bottomleft = self.pos)
        if self.status in ["run_left", "walk_right", "idle_right"]:
            self.rect = self.image.get_rect(bottomright = (self.pos[0] + self.image.get_width(), self.pos[1]))
        if self.status == "attack1_right" or self.status == "hit_right" or self.status == "attack2_left":
            self.rect = self.image.get_rect(midbottom = (self.pos[0], self.pos[1]))
        if self.status == "attack1_left" or self.status == "hit_left" or self.status == "attack2_left":
            self.rect = self.image.get_rect(midbottom = (self.pos[0], self.pos[1]))
        if self.status == "dead_right":
            self.rect = self.image.get_rect(bottomright = (self.pos[0] + self.rect.width, self.pos[1]))
        if self.status == "dead_left":
            self.rect = self.image.get_rect(bottomleft=  (self.pos[0], self.pos[1]))
        self.hitbox = self.rect

    def manage_status(self, dt):
        if (self.status == "hit_right" or self.status == "hit_left") and self.health > 0:
            self.hit = True
        else:
            self.hit = False
        self.distance_to_player = ((self.rect.centerx - self.player.rect.centerx) ** 2 + (self.rect.centery - self.player.rect.centery) ** 2) ** 0.5
        if self.direction == "left" and not self.hit and self.health > 0 and "attack" not in self.status:
            if self.status != "attack1_left" and self.status != "attack2_left":
                self.pos[0] -= dt
            if self.rect.left < self.left_bound and self.rect.right > self.left_bound:
                self.direction = "right"
        if self.direction == "right" and not self.hit and self.health > 0 and "attack" not in self.status:
            if self.status != "attack1_right" and self.status != "attack2_right":
                self.pos[0] += dt
            if self.rect.right > self.right_bound and self.rect.left < self.right_bound:
                self.direction = "left"

        if self.direction == "left" and self.status not in ["attack1_left", "attack1_right", "hit_left", "hit_right", "dead_right", "dead_left", "attack2_right", "attack2_left"]:
            self.status = "walk_left"
        if self.direction == "right" and self.status not in ["attack1_left", "attack1_right", "hit_left", "hit_right", "dead_right", "dead_left", "attack2_right", "attack2_left"]:
            self.status = "walk_right"

        if self.left_bound < self.player.rect.centerx < self.right_bound and not self.hit and self.health > 0:
            if self.player.rect.right < self.rect.left and self.player.rect.left < self.rect.left and self.status == "walk_left":
                self.status = "run_left"
                self.pos[0] -= dt
            elif self.player.rect.left > self.rect.right and self.player.rect.right > self.rect.right and self.status == "walk_right":
                self.status = "run_right"
                self.pos[0] += dt

        if self.distance_to_player < 120 and not self.attacking and not self.hit and self.health > 0:
            self.frame_index = 0
            self.attacking = True
            if self.status == "run_right":
                self.status = random.choice(["attack1_right", "attack2_right"])
            if self.status == "run_left":
                self.status = random.choice(["attack1_left", "attack2_left"])

    def death_check(self):    
        if self.health == 0 and self.status not in ["dead_right", "dead_left"]:
            if self.direction == "right":
                self.status = "dead_right"
            if self.direction == "left":
                self.status = "dead_left"
            self.dead_flag = True
            self.health = -1
        
        if self.dead_flag:
            self.dead_flag = False
            self.frame_index = 0
        if self.health <= 0:
            if self.direction == "right":
                self.status = "dead_right"
            if self.direction == "left":
                self.status = "dead_left"
        if self.frame_index >= len(self.animations_dictionary[self.status]) - 1 and self.status in ["dead_right", "dead_left"]:
            self.frame_index = len(self.animations_dictionary[self.status]) - 1
            self.player.health = min(self.player.max_health, self.player.health + 1)
            self.dead = True
            #self.kill()

    def display_health_bar(self):
        ratio = self.health / self.max_health
        if ratio >= 0:
            ratio = self.health / self.max_health
        else:
            ratio = 0
        health_bar_length = 30 + self.animations_dictionary["idle_left"][0].get_size()[0]
        height_above = self.animations_dictionary["idle_left"][0].get_size()[1]

        difference = self.health - self.display_health
        self.display_health += difference * 0.05

        pygame.draw.rect(window, "red", pygame.Rect(self.rect.centerx - health_bar_length / 2 + offset.x, self.rect.bottom - height_above - 20 + offset.y, health_bar_length, 10), border_radius = 5)
        pygame.draw.rect(window, "yellow", pygame.Rect(self.rect.centerx - health_bar_length / 2 + offset.x, self.rect.bottom - height_above - 20 + offset.y, self.display_health / self.max_health * health_bar_length, 10), border_radius = 5) 
        pygame.draw.rect(window, "green", pygame.Rect(self.rect.centerx - health_bar_length / 2 + offset.x, self.rect.bottom - height_above - 20 + offset.y, ratio * health_bar_length, 10), border_radius = 5)
    
    def update(self, dt):
        if not self.dead:
            self.animate(dt)
            self.calibrate_rect()
            if self.health > 0:
                self.display_health_bar()
            self.manage_status(dt)
            self.death_check()             

class Platform(pygame.sprite.Sprite):
    def __init__(self, coords, size, groups):
        super().__init__(groups)
        for group in groups:
            self.add(group)
        self.image = pygame.Surface(size)
        self.image.fill("blue")
        self.rect = self.image.get_rect(topleft = coords)


class Tile(pygame.sprite.Sprite):
    def __init__(self, coords, size, surf, groups, collideable):
        super().__init__(groups)
        for group in groups:
            self.add(group)
        self.image = pygame.transform.scale_by(surf, 2)
        self.rect = self.image.get_rect(topleft = coords)
        self.rect.width = size[0]
        self.rect.height = size[1]
        self.collideable = collideable
        self.prev_rect = self.rect.copy()
        if self.collideable == "oneway":
            self.collideable = True
            self.oneway = True
        else:
            self.oneway = False

        if self in spikes:
            self.rect = pygame.Rect(self.rect.left, self.rect.bottom, 64, 32)
            self.rect.y -= 32


class MovingTile(pygame.sprite.Sprite):
    def __init__(self, coords, size, surf, groups, left_bound, right_bound, direction):
        super().__init__(groups)
        for group in groups:
            self.add(group)
            
        self.image = pygame.transform.scale_by(surf, 2)
        self.rect = self.image.get_rect(topleft = coords)
        self.rect.width = size[0]
        self.rect.height = size[1]
        self.collideable = True
        self.prev_rect = self.rect.copy()
        self.direction = direction
        self.dir = pygame.math.Vector2(-1, 0)
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.oneway = False
        self.moving = True
        self.speed = 3
        self.coords = coords
    
    def update(self, dt):
        self.prev_rect = self.rect.copy()
        
        if self.direction == "horizontal":
            if self.dir.x < 0:
                self.rect.x -= self.speed * dt
                if self.rect.left < self.left_bound:
                    self.rect.left = self.left_bound
                    self.dir.x *= -1
                    self.player.added_velocity.x = 0
            if self.dir.x > 0:
                self.rect.x += self.speed * dt
                if self.rect.right > self.right_bound:
                    self.rect_right = self.right_bound
                    self.dir.x *= -1
                    self.player.added_velocity.x = 0
        
        if self.player.on_moving_platform and self.player.added_velocity.x == 0:
            self.player.added_velocity.x = self.dir.x * self.speed * dt# * 0.5
        #else:
            #self.player.added_velocity.x = 0
            

class Chest(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        #for group in groups:
        self.add(groups)
        self.animation_dictionary = {
                                    "unopened": [pygame.transform.scale_by(pygame.image.load("data/graphics/chest1/0.png"), 2)],
                                    "opening": [pygame.transform.scale_by(pygame.image.load(f"data/graphics/chest1/{x}.png"), 2) for x in range(0, 7)],
                                    "opened": [pygame.transform.scale_by(pygame.image.load("data/graphics/chest1/6.png"), 2)]
                                    }
        self.status = "unopened"
        self.image = self.animation_dictionary[self.status][0]
        self.pos = pos
        self.rect = self.image.get_rect(bottomleft = pos)
        self.collideable = True
        self.frame_index = 0
        self.prev_rect = self.rect.copy()
        self.oneway = True
        self.chest = True

    def update(self, dt):
        if self.status == "opening":
            self.frame_index += 0.5 * dt
            if self.frame_index > len(self.animation_dictionary[self.status]):
                self.status = "unopened"
                self.frame_index = 0
                for x in range(random.randint(30, 60)): Particle(self.rect.center, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), all_sprites, platforms)

        self.image = self.animation_dictionary[self.status][int(self.frame_index)]
        self.rect = self.image.get_rect(bottomleft = self.pos)
        self.prev_rect = self.rect.copy()
        

all_sprites = pygame.sprite.Group()
platforms = pygame.sprite.Group()
oneways = pygame.sprite.Group()
chests = pygame.sprite.Group()
props = pygame.sprite.Group()
foreground_props = pygame.sprite.Group()
monsters = pygame.sprite.Group()
spikes = pygame.sprite.Group()

ref_platform = Tile((0, 0), (0, 0), pygame.Surface((0, 0)), (all_sprites, platforms), False) # positioned at (0, 0) to keep track of how much player has scrolled

tmx_map = pytmx.util_pygame.load_pygame('map2.tmx')
map_layer_data = pytmx.pytmx.TiledMap("map2.tmx")
sf = 2
for x, y, surf in tmx_map.get_layer_by_name('level-layer1').tiles():
    Tile((x * 32 * sf, y * 32 * sf), (32 * sf, 32 * sf), surf.convert_alpha(), (all_sprites, platforms), True)
for x, y, surf in tmx_map.get_layer_by_name('props-layer1').tiles():
    Tile((x * 32 * sf, y * 32 * sf), (32 * sf, 32 * sf), surf.convert_alpha(), (all_sprites, platforms), False)
for x, y, surf in tmx_map.get_layer_by_name('level-layer2').tiles():
    Tile((x * 32 * sf, y * 32 * sf), (32 * sf, 32 * sf), surf.convert_alpha(), (all_sprites, platforms), True)
for x, y, surf in tmx_map.get_layer_by_name('props-layer2').tiles():
    Tile((x * 32 * sf, y * 32 * sf), (32 * sf, 32 * sf), surf.convert_alpha(), (all_sprites, platforms), False)
for x, y, surf in tmx_map.get_layer_by_name("level-layer3").tiles():
    Tile((x * 32 * sf, y * 32 * sf), (32 * sf, 32 * sf * 0.2), surf.convert_alpha(), (all_sprites, platforms), True)
for x, y, surf in tmx_map.get_layer_by_name("oneway").tiles():
    Tile((x * 32 * sf, y * 32 * sf), (32 * sf, 32 * sf), surf.convert_alpha(), (all_sprites, platforms, oneways), "oneway")
for x, y, surf in tmx_map.get_layer_by_name("foreground").tiles():
    Tile((x * 32 * sf, y * 32 * sf), (32 * sf, 32 * sf), surf.convert_alpha(), (all_sprites, props, foreground_props), False)
for x, y, surf in tmx_map.get_layer_by_name("foreground2").tiles():
    Tile((x * 32 * sf, y * 32 * sf), (32 * sf, 32 * sf), surf.convert_alpha(), (all_sprites, props, foreground_props), False)
player = Player(platforms.sprites(), ref_platform, chests.sprites()) # pass ref_platform into player object
for chest in chests:
    chest.collideable = False
player.add(all_sprites)
for obj in tmx_map.get_layer_by_name("chests"):
    Chest((obj.x * 2, obj.y * 2), (all_sprites, platforms, chests))
for obj in tmx_map.get_layer_by_name("deathbringer"):
    Deathbringer("deathbringer", (obj.x * 2, obj.y * 2), (monsters, all_sprites), player)
for obj in tmx_map.get_layer_by_name("imp"):
    left_bound = int(map_layer_data.get_object_by_id(obj.id).properties["left_bound"])
    right_bound = int(map_layer_data.get_object_by_id(obj.id).properties["right_bound"])
    Imp([obj.x * 2, obj.y * 2], (monsters, all_sprites), player, left_bound * 2, right_bound * 2)
for obj in tmx_map.get_layer_by_name("axeman"):
    left_bound = int(map_layer_data.get_object_by_id(obj.id).properties["left_bound"])
    right_bound = int(map_layer_data.get_object_by_id(obj.id).properties["right_bound"])
    Axeman([obj.x * 2, obj.y * 2], (monsters, all_sprites), player, left_bound * 2, right_bound * 2)

moving_platforms_list = []
for obj in tmx_map.get_layer_by_name("moving-platforms-points"):
    left_bound = int(map_layer_data.get_object_by_id(obj.id).properties["left_bound"])
    right_bound = int(map_layer_data.get_object_by_id(obj.id).properties["right_bound"])
    direction = map_layer_data.get_object_by_id(obj.id).properties["direction"]
    moving_platforms_list.append([[obj.x * 2, obj.y * 2], left_bound * 2, right_bound * 2, direction])
for x, y, surf in tmx_map.get_layer_by_name("moving-platforms").tiles():
    for coords, left_bound, right_bound, direction in moving_platforms_list:
        if x * 32 * sf == coords[0] and y * 32 * sf == coords[1]:
            MovingTile(coords, (32 * sf, 32 * sf * 0.1), surf, (all_sprites, platforms), left_bound, right_bound, direction)
for x, y, surf in tmx_map.get_layer_by_name("spikes").tiles():
    Tile((x * 32 * sf, y * 32 * sf - 32 * sf * 0.5), (32 * sf, 32 * sf), surf.convert_alpha(), (all_sprites, spikes, platforms), True)

player.chests = chests.sprites()
player.platforms = platforms.sprites()
for platform in platforms:
    platform.player = player

player.monsters = monsters

camera = pygame.math.Vector2(player.rect.center)
initial_vector = pygame.math.Vector2(WIDTH / 2, HEIGHT / 2)

for monster in monsters.sprites():
    monster.player = player

clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()

bottom_row = []
for x in range(1, 77):
    bottom_row.append(player.image.get_at((x, 110)))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    now = time.time()
    dt = (now - prev_time) * 60
    #print(dt)
    if pygame.key.get_pressed()[pygame.K_f]:
        clock.tick(30)
    else:
        clock.tick(60)
    #dt = (1 / dt) / (60)
    #
    prev_time = now

    window.fill("black")

    keys = pygame.key.get_pressed()
    

    heading = player.rect.center - camera
    camera += heading * 0.03
    offset = -camera + initial_vector
    current_time_coordinate = pygame.time.get_ticks() / 333
        
    if offset.x > 0:
        offset.x = 0
    if offset.y < -45 * 32:
        offset.y = -45 * 32
    if offset.y > 0:
        offset.y = 0

    for sprite in all_sprites.sprites():
        if not hasattr(sprite, "draw") and sprite != player and sprite not in foreground_props.sprites():
            window.blit(sprite.image, sprite.rect.topleft + offset)
    
    for sprite in monsters.sprites():
        window.blit(sprite.image, (sprite.rect.left + offset.x, sprite.rect.top + offset.y))
    monsters.update(dt)

    #rect = player.image.get_rect(center = player.rect.center)
    #pygame.draw.rect(window, "green", pygame.Rect(rect.left + offset.x, rect.top + offset.y, rect.width, rect.height))

    for sprite in all_sprites.sprites():
        if not hasattr(sprite, "draw") and sprite == player:
            if player.status in ["idle_right", "walk_left", "jump_left", "defend_right", "shield_right"]:
                window.blit(sprite.image, (sprite.rect.right - sprite.image.get_width() + offset.x, sprite.rect.bottom - sprite.image.get_height() + offset.y))
            if player.status in ["idle_left", "walk_right", "jump_right", "defend_left", "shield_left"]:
                window.blit(sprite.image, (sprite.rect.left + offset.x, sprite.rect.bottom - sprite.image.get_height() + offset.y))
            if player.status in ["attack1_left", "attack2_left", "attack3_left", "attack1_right", "attack2_right", "attack3_right", "dead_right", "dead_left"]:
                window.blit(sprite.image, (sprite.rect.centerx - sprite.image.get_width() / 2 + offset.x, sprite.rect.bottom - sprite.image.get_height() + offset.y))
    
    #window.blit(player.image, (player.rect.centerx - player.center_axis + offset.x, player.rect.bottom - player.image.get_height() + offset.y))
    pygame.draw.line(window, "red", (player.center_axis + player.rect.left + offset.x, player.rect.bottom + offset.y), (player.center_axis + player.rect.left + offset.x, player.rect.bottom - 10 + offset.y), 1)
    pygame.draw.line(window, "red", (player.index1 + player.rect.left + offset.x, player.rect.bottom + offset.y), (player.index1 + player.rect.left + offset.x, player.rect.bottom - 10 + offset.y), 1)
    pygame.draw.line(window, "blue", (player.index2 + player.rect.left + offset.x, player.rect.bottom + offset.y), (player.index2 + player.rect.left + offset.x, player.rect.bottom - 10 + offset.y), 1)

    for sprite in foreground_props.sprites():
        window.blit(sprite.image, sprite.rect.topleft + offset)

    all_sprites.update(dt)

    for sprite in all_sprites:
        if sprite != player:
                sprite.rect.x += player.camshake

    #
    window.blit(font2.render(str(player.camshake), True, "yellow"), (100, 0))
    #window.blit(font2.render(str(player.frame_index), True, "yellow"), (100, 30))
    #window.blit(font2.render(str(player.velocity), True, "yellow"), (100, 60))
    #window.blit(font2.render(str(dt), True, "yellow"), (100, 100))
    #window.blit(font2.render(str(player.rect.center), True, "yellow"), (100, 140))
    #window.blit(font2.render(str(clock.get_fps()), True, "yellow"), (100, 180))

    if keys[pygame.K_h]:
        for tile in platforms.sprites():
            if tile.collideable:
                pygame.draw.rect(window, "blue", tile.rect.move(offset))
            else:
                pygame.draw.rect(window, "red", tile.rect.move(offset))
        for monster in monsters.sprites():
            pygame.draw.rect(window, "teal", monster.rect.move(offset))
            pygame.draw.rect(window, "green", monster.hitbox.move(offset))
        pygame.draw.rect(window, "purple", player.rect.move(offset))


    pygame.display.update()