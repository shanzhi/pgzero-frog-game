import pgzrun
import pygame

from time import time
from random import random, randint
from pgzero.constants import keys#常数

WIDTH = 800
HEIGHT = 600
LEAP_FRAME_DELAY = 0.15
MAX_ROWS = 5
MAX_COLS = 6
ROCK_POS = (MAX_COLS-1, MAX_ROWS-1)

def scale(actor, factor):#很专业，特无趣
    surf = actor.orig_surf or actor._surf
    rect = surf.get_rect()
    new_w = int(rect.width * factor)
    new_h = int(rect.height * factor)
    actor._surf = pygame.transform.smoothscale(surf, (new_w, new_h))
    actor.width, actor.height = actor._surf.get_size()
    actor.center = (actor.x, actor.y)
    actor._calc_anchor()

def restore_surface(actor, orig_surf):
    actor._surf = orig_surf
    actor.width, actor.height = actor._surf.get_size()
    actor.center = (actor.x, actor.y)
    actor._calc_anchor()


class Frog(Actor):
    def __init__(self):
        super(Frog, self).__init__('frog_right')
        self.pond_pos = 0, 0
        self.next_update = 0
        self.jump_sound = sounds.load('jump')
        self.key_pressed = None

    def jump(self, direction):
        self.image = direction
        self.jump_sound.stop()
        self.jump_sound.play()

    def update(self):
        for key in [keys.RIGHT, keys.LEFT, keys.UP, keys.DOWN]:
            if keyboard[key]:
                self.key_pressed = key
                return

        if self.key_pressed == keys.RIGHT:
            if self.pond_pos[0] + 1 < MAX_COLS:
                self.pond_pos = self.pond_pos[0] + 1, self.pond_pos[1]
                self.jump('frog_right')
        elif self.key_pressed == keys.LEFT:
            if self.pond_pos[0] - 1 >= 0:
                self.pond_pos = self.pond_pos[0] - 1, self.pond_pos[1]
                self.jump('frog_left')
        elif self.key_pressed == keys.UP:
            if self.pond_pos[1] - 1 >= 0:
                self.pond_pos = self.pond_pos[0], self.pond_pos[1] - 1
                self.jump('frog_up')
        elif self.key_pressed == keys.DOWN:
            if self.pond_pos[1] + 1 < MAX_ROWS:
                self.pond_pos = self.pond_pos[0], self.pond_pos[1] + 1
                self.jump('frog_down')

        self.key_pressed = None

class Rock(Actor):
    def __init__(self, image):
        super(Rock, self).__init__(image)
        self.orig_surf = self._surf
        self.state = 'rock'
        self.fly = None
        scale(self, 0.75)

class Lilypad(Actor):
    DECAY_SCALES = [0.80, 0.70, 0.60, 0.50, 0.40, 0.30]
    FINAL_DECAY = len(DECAY_SCALES)-1

    def __init__(self, image, is_initial, pond):
        super(Lilypad, self).__init__(image)
        self.pond = pond
        self.orig_surf = self._surf
        self.fly = None
        self.catch_fly_sound = sounds.load('catch_fly')

        if is_initial:
            self.delay_rate = 2.0
            self.decay_pos = 0
        else:
            self.delay_rate = 0.5 + (random() * 3)
            self.decay_pos = randint(0, Lilypad.FINAL_DECAY)

        self.reset_rate = 1.0 + (random() * 5)
        self.update()

    def reset(self):
        if not self.pond.is_running:
            return

        restore_surface(self, self.orig_surf)
        self.decay_pos = -1
        self.update()

    def update(self):
        if not self.pond.is_running:
            return

        if self.decay_pos == Lilypad.FINAL_DECAY:
            self.state = 'missing'
            clock.schedule(self.reset, self.reset_rate)
        else:
            self.decay_pos += 1

            if self.decay_pos == Lilypad.FINAL_DECAY:
                self.state = 'missing'
            else:
                self.state = 'available'

            if self.decay_pos == Lilypad.FINAL_DECAY-1:
                clock.schedule(self.update, 1.0)
            else:
                clock.schedule(self.update, self.delay_rate)

        scale(self, Lilypad.DECAY_SCALES[self.decay_pos])

    def catch_fly(self):
        self.fly = None
        self.catch_fly_sound.play()

    def draw(self):
        super().draw()
        if self.fly:
            self.fly.draw()

class Pond(object):
    def __init__(self):
        self.end_state = 'none'
        self.lilypads = []
        self.background = Actor('background')
        self.pos = 0, 0
        self.level = 1
        self.score = 0
        self.reset()

    def remove_fly(self):
        for row in self.lilypads:
            for col in row:
                if col.fly:
                    col.fly = None

        clock.schedule_unique(self.show_fly, randint(5, 10))

    def show_fly(self):
        image = ['fly_left', 'fly_right', 'fly_up', 'fly_down'][randint(0,3)]

        x = randint(0, MAX_COLS-1)
        y = randint(0, MAX_ROWS-1)

        self.lily_with_fly = self.lilypads[y][x]

        self.lily_with_fly.fly = Actor(image)
        self.lily_with_fly.fly.pos = self.lily_with_fly.pos

        clock.schedule_unique(self.remove_fly, randint(5, 12))

    def reset(self):
        if self.end_state == 'win':
            self.score += (self.level * 1000)
            self.level += 1
        elif self.end_state == 'lose':
            self.level = 1
            self.score = 0

        clock.unschedule(self.show_fly)
        self.remove_fly()

        self.frog = Frog()
        self.is_running = True
        self.lilypads = []
        is_initial = True
        for y in range(MAX_ROWS):
            row = []
            for x in range(MAX_COLS):

                if (x,y) == ROCK_POS:
                    lilypad = Rock('rock')
                else:
                    lilypad = Lilypad('lilypad_orange', is_initial, self)
                    is_initial = False

                lilypad.pos = 100+(x*120), 120+(y*100)

                row.append(lilypad)
            self.lilypads.append(row)

    def update(self):
        self.frog.update()

        lily = self.lilypads[self.frog.pond_pos[1]][self.frog.pond_pos[0]]
        self.frog.x = lily.x
        self.frog.y = lily.y

        if lily.state == 'missing':
            self.frog.image = 'frog_dead'
            self.is_running = False
            self.end_state = 'lose'
            self.frog.jump_sound.stop()
            sounds.load('lose').play()
        elif lily.state == 'rock':
            self.frog.image = 'smallicon_frog'
            self.is_running = False
            self.end_state = 'win'
            self.frog.jump_sound.stop()
            sounds.load('win').play()
        elif lily.fly:
            lily.catch_fly()
            self.score += 5000

    def draw(self):
        self.background.draw()

        for row in self.lilypads:
            for col in row:
                col.draw()

        self.frog.draw()

        if not self.is_running:
            if self.end_state == 'win':
                screen.draw.text("YOU WIN", (210, 180), color="green", fontsize=120, owidth=1, ocolor="white")
            else:
                screen.draw.text("YOU LOSE", (180, 180), color="red", fontsize=120, owidth=1, ocolor="white")

            screen.draw.text("PRESS SPACE TO CONTINUE", (230, 300), color="yellow", fontsize=32, owidth=1, ocolor="black")

        level_text = 'Level: %d' % self.level
        screen.draw.text(level_text, (20, 10), color="white", fontsize=32, owidth=1, ocolor='black')

        score_text = 'Score: %d' % self.score
        screen.draw.text(score_text, (150, 10), color="white", fontsize=32, owidth=1, ocolor='black')

pond = Pond()

music.play('game_music')
music.set_volume(.3)

def update():
    if pond.is_running:
        pond.update()
    else:
        if keyboard.space:
            pond.reset()

def draw():
    screen.clear()
    pond.draw()

pgzrun.go()
