import math
import random
import pygame

from .config import (
    VENOM_BLACK, VENOM_EDGE, VENOM_GLOSS, VENOM_GLOSS_HOT,
    RIM_A, RIM_B, BODY_RIM, LIT_FILL,
    DOT_COLOR, DOT_DIM, DOT_NEAR_RADIUS,
    VENOM_SPEED, VENOM_IDLE_SPEED,
    GRID_SPACING, GRID_OFFSET, BODY_RADIUS,
    N_THICK, N_THIN, TENDRIL_POINTS,
)
from .utils import clamp

WHITE = (255, 255, 255)

def chaikin(pts):

    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
        out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
    out.append(pts[-1])
    return out


def normals(pts):
    res = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        d = math.hypot(tx, ty) or 1.0
        res.append((-ty / d, tx / d))
    return res


def lerp_color(a, b, k):
    k = clamp(k, 0.0, 1.0)
    return (int(a[0] + (b[0] - a[0]) * k),
            int(a[1] + (b[1] - a[1]) * k),
            int(a[2] + (b[2] - a[2]) * k))


_glow_cache = {}



def glow_sprite(radius, v):
  
    key = (radius, v)
    spr = _glow_cache.get(key)
    if spr is None:
        spr = pygame.Surface((radius * 2, radius * 2))
        spr.fill((0, 0, 0))
        for r in range(radius, 0, -2):
            k = (1.0 - r / radius) ** 2
            c = int(v * k)
            pygame.draw.circle(spr, (c, c, c), (radius, radius), r)
        _glow_cache[key] = spr
    return spr


def add_glow(surface, x, y, radius, v):
    if v <= 0:
        return
    spr = glow_sprite(radius, v)
    surface.blit(spr, (int(x) - radius, int(y) - radius), special_flags=pygame.BLEND_RGB_ADD)


class Tendril:
    def __init__(self, body, thick):
        self.thick = thick
        self.n = TENDRIL_POINTS
        self.reach = random.uniform(170, 270) if thick else random.uniform(120, 260)
        self.width = random.uniform(6.5, 10.5) if thick else random.uniform(1.8, 4.0)
        seg = self.reach / (self.n - 1) * (1.0 if thick else 1.12)
        self.lengths = [seg] * (self.n - 1)
        self.base_angle = random.uniform(0, math.tau)
        self.base_r = BODY_RADIUS * random.uniform(0.05, 0.22)
        self.spread = random.uniform(-1.9, 1.9)
        self.phase = random.uniform(0, math.tau)
        self.wave_amp = random.uniform(5, 14) if thick else random.uniform(10, 26)
        self.wave_speed = random.uniform(1.6, 3.0)
        self.points = [[body[0], body[1]] for _ in range(self.n)]
        self.tip = [body[0], body[1]]
        self.grip = None        
        self.grip_t = 0.0
        self.lit = 0.0           
        self.cooldown = random.uniform(0, 0.8)
        self.rim = random.choice([-1, 1])
        self.rim_power = random.uniform(0.6, 1.0)
        self.glints = []
        for _ in range(random.randint(1, 3)):
            s = random.randint(1, self.n - 5)
            self.glints.append((s, random.randint(2, 5), random.choice([-1, 1])))
        self.smooth = []


    def solve(self, anchor, target):
        p, L = self.points, self.lengths
        for _ in range(3):
            p[-1][0], p[-1][1] = target
            for i in range(self.n - 2, -1, -1):
                dx, dy = p[i][0] - p[i + 1][0], p[i][1] - p[i + 1][1]
                d = math.hypot(dx, dy) or 0.001
                p[i][0] = p[i + 1][0] + dx / d * L[i]
                p[i][1] = p[i + 1][1] + dy / d * L[i]
            p[0][0], p[0][1] = anchor
            for i in range(1, self.n):
                dx, dy = p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]
                d = math.hypot(dx, dy) or 0.001
                p[i][0] = p[i - 1][0] + dx / d * L[i - 1]
                p[i][1] = p[i - 1][1] + dy / d * L[i - 1]

    def update(self, dt, t, creature):
        bx, by = creature.x, creature.y
        h = creature.heading
        a = self.base_angle + h * 0.5
        anchor = (bx + math.cos(a) * self.base_r, by + math.sin(a) * self.base_r)


        if self.grip is not None:
            self.grip_t += dt
            gx, gy = creature.dot_pos(*self.grip)
            to_dot = (gx - bx, gy - by)
            dist = math.hypot(*to_dot)
            ahead = to_dot[0] * math.cos(h) + to_dot[1] * math.sin(h)
            if dist > self.reach * 0.97 or ahead < -self.reach * 0.35:
                creature.release(self.grip)
                self.grip = None
                self.cooldown = random.uniform(0.1, 0.35) * (1.0 - 0.6 * creature.rage)
            else:
                self.tip[0] += (gx - self.tip[0]) * min(1.0, dt * 18)
                self.tip[1] += (gy - self.tip[1]) * min(1.0, dt * 18)
        if self.grip is None:
            sway = math.sin(t * 1.1 + self.phase) * 0.55
            ang = h + self.spread + sway
            r = self.reach * (0.55 + 0.35 * math.sin(t * 1.6 + self.phase))
            tx = bx + math.cos(ang) * r
            ty = by + math.sin(ang) * r + 12  
            self.tip[0] += (tx - self.tip[0]) * min(1.0, dt * (5 + 4 * creature.rage))
            self.tip[1] += (ty - self.tip[1]) * min(1.0, dt * (5 + 4 * creature.rage))
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.try_grab(creature, h)
                self.cooldown = random.uniform(0.1, 0.35) * (1.0 - 0.6 * creature.rage)


        if self.grip is not None:
            target = 1.0 if self.grip_t < 0.7 else 0.4
            rate = 2.6
        else:
            target = 0.0
            rate = 1.6
        self.lit += (target - self.lit) * min(1.0, dt * rate)

        self.solve(anchor, self.tip)

        amp = self.wave_amp * (0.35 if self.grip else 1.0)
        pts = []
        nrm = normals(self.points)
        for i, (p, nv) in enumerate(zip(self.points, nrm)):
            u = i / (self.n - 1)
            off = math.sin(t * self.wave_speed + self.phase - i * 0.55) * amp * (u ** 1.2)
            if self.grip is not None and i == self.n - 1:
                off = 0
            pts.append((p[0] + nv[0] * off, p[1] + nv[1] * off))
        self.smooth = chaikin(chaikin(pts))

    def try_grab(self, creature, h):
        ax = creature.x + math.cos(h) * BODY_RADIUS
        ay = creature.y + math.sin(h) * BODY_RADIUS
        best = None
        for _ in range(6):
            ang = h + random.uniform(-1.25, 1.25)
            r = random.uniform(0.6, 0.95) * self.reach
            px, py = creature.x + math.cos(ang) * r, creature.y + math.sin(ang) * r
            ix = round((px - GRID_OFFSET) / GRID_SPACING)
            iy = round((py - GRID_OFFSET) / GRID_SPACING)
            if not creature.valid_dot(ix, iy) or (ix, iy) in creature.taken:
                continue
            gx, gy = creature.dot_pos(ix, iy)
            d = math.hypot(gx - creature.x, gy - creature.y)
            if d > self.reach * 0.92 or d < 40:
                continue
            score = (gx - ax) * math.cos(h) + (gy - ay) * math.sin(h)
            if best is None or score > best[0]:
                best = (score, ix, iy)
        if best:
            self.grip = (best[1], best[2])
            self.grip_t = 0.0
            creature.taken.add(self.grip)

    def draw(self, surface, t):
        pts = self.smooth
        if len(pts) < 3:
            return
        lit = self.lit
        nrm = normals(pts)
        n = len(pts)
        left, right = [], []
        for i, (p, nv) in enumerate(zip(pts, nrm)):
            u = i / (n - 1)
            w = self.width * (1 - u) ** 0.85 + 0.9
            left.append((p[0] + nv[0] * w, p[1] + nv[1] * w))
            right.append((p[0] - nv[0] * w, p[1] - nv[1] * w))
        poly = left + right[::-1]


        fill = lerp_color(VENOM_BLACK, LIT_FILL, lit * 0.85) if lit > 0.02 else VENOM_BLACK
        pygame.draw.polygon(surface, fill, poly)

        rim, other = (left, right) if self.rim > 0 else (right, left)

        oc = lerp_color(VENOM_EDGE, (235, 236, 242), lit * 0.8)
        pygame.draw.lines(surface, oc, False, other, 1)

        for i in range(n - 1):
            u = i / (n - 1)
            col = lerp_color(RIM_A, RIM_B, u)
            f = self.rim_power * (1.0 - 0.5 * u)
            col = (int(col[0] * f), int(col[1] * f), int(col[2] * f))
            if lit > 0.02:
                col = lerp_color(col, WHITE, lit * (1.0 - 0.25 * u))
            wd = 2 if (self.thick and u < 0.6) else 1
            pygame.draw.line(surface, col, rim[i], rim[i + 1], wd)

        # لمعان زجاجي رفيع
        for s, ln, side in self.glints:
            a = int(s * (n - 1) / self.n)
            b = min(n - 1, a + ln * 2)
            hl = []
            for i in range(a, b + 1):
                u = i / (n - 1)
                w = (self.width * (1 - u) ** 0.85 + 0.9) * 0.4 * side
                hl.append((pts[i][0] + nrm[i][0] * w, pts[i][1] + nrm[i][1] * w))
            if len(hl) > 1:
                pygame.draw.lines(surface, VENOM_GLOSS, False, hl, 1)
                if len(hl) > 3 and self.thick:
                    pygame.draw.lines(surface, VENOM_GLOSS_HOT, False, hl[1:-1], 1)

    
        if lit > 0.04:
            cc = lerp_color(VENOM_BLACK, (240, 241, 247), lit * 0.65)
            pygame.draw.lines(surface, cc, False, pts, 2 if self.thick else 1)
            v = int(lit * 6) * 7
            rad = 18 if self.thick else 12
            for i in range(2, n, 7):
                add_glow(surface, pts[i][0], pts[i][1], rad, v)


class VenomCreature:


    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = width / 2.0
        self.y = height / 2.0
        self.vx = self.vy = 0.0
        self.heading = 0.0
        self.time = 0.0
        self.speed = 0.0
        self.taken = set()
        self.rage = 0.0          
        self.holding = False     
        self.rings = []       
        self.flash = {}     
        body = (self.x, self.y)
        self.thin = [Tendril(body, False) for _ in range(N_THIN)]
        self.thick = [Tendril(body, True) for _ in range(N_THICK)]


    def valid_dot(self, ix, iy):
        x, y = GRID_OFFSET + ix * GRID_SPACING, GRID_OFFSET + iy * GRID_SPACING
        return 0 <= x < self.width and 0 <= y < self.height

    @staticmethod
    def dot_pos(ix, iy):
        return GRID_OFFSET + ix * GRID_SPACING, GRID_OFFSET + iy * GRID_SPACING

    def release(self, key):
        self.taken.discard(key)
        self.flash[key] = 0.6

    def provoke(self, pos):
    
        self.rage = 1.0
        self.rings.append([pos[0], pos[1], 0.0])


    def update(self, dt, mouse, chasing):
        self.time += dt
        dx, dy = mouse[0] - self.x, mouse[1] - self.y
        dist = math.hypot(dx, dy)
        if self.holding:
            self.rage = 1.0
        else:
            self.rage = max(0.0, self.rage - dt / 2.5)
        for r in self.rings:
            r[2] += dt
        self.rings = [r for r in self.rings if r[2] < 0.7]
        top = (VENOM_SPEED if (chasing or self.rage > 0) else VENOM_IDLE_SPEED) * (1.0 + 0.8 * self.rage)

        want_vx = want_vy = 0.0
        if dist > 20:
            s = top * min(1.0, dist / 220.0)
            want_vx, want_vy = dx / dist * s, dy / dist * s

     
        px = py = 0.0
        k = 0
        for tn in self.thick + self.thin:
            if tn.grip is not None:
                gx, gy = self.dot_pos(*tn.grip)
                d = math.hypot(gx - self.x, gy - self.y) or 1.0
                px += (gx - self.x) / d
                py += (gy - self.y) / d
                k += 1
        if k and dist > 20:
            pl = math.hypot(px, py) or 1.0
            pull = min(1.0, k / 5.0)
            want_vx = want_vx * (1 - 0.35 * pull) + px / pl * top * 0.35 * pull
            want_vy = want_vy * (1 - 0.35 * pull) + py / pl * top * 0.35 * pull
        elif k == 0:
            want_vx *= 0.65
            want_vy *= 0.65

       
        pulse = 0.78 + 0.22 * math.sin(self.time * 4.2)
        self.vx += (want_vx * pulse - self.vx) * min(1.0, dt * (5.0 + 4.0 * self.rage))
        self.vy += (want_vy * pulse - self.vy) * min(1.0, dt * (5.0 + 4.0 * self.rage))
        self.x = clamp(self.x + self.vx * dt, 40, self.width - 40)
        self.y = clamp(self.y + self.vy * dt, 40, self.height - 40)
        self.speed = math.hypot(self.vx, self.vy)

        if self.speed > 12:
            target = math.atan2(self.vy, self.vx)
        else:
            target = math.atan2(dy, dx) if dist > 5 else self.heading
        diff = (target - self.heading + math.pi) % math.tau - math.pi
        self.heading += diff * min(1.0, dt * 4.5)

        for tn in self.thick + self.thin:
            tn.update(dt, self.time, self)

        for key in list(self.flash):
            self.flash[key] -= dt
            if self.flash[key] <= 0:
                del self.flash[key]

    def draw_near_dots(self, surface):
    
        R = DOT_NEAR_RADIUS
        ix0 = int((self.x - R - GRID_OFFSET) // GRID_SPACING)
        ix1 = int((self.x + R - GRID_OFFSET) // GRID_SPACING) + 1
        iy0 = int((self.y - R - GRID_OFFSET) // GRID_SPACING)
        iy1 = int((self.y + R - GRID_OFFSET) // GRID_SPACING) + 1
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                if not self.valid_dot(ix, iy) or (ix, iy) in self.taken:
                    continue
                gx, gy = self.dot_pos(ix, iy)
                d = math.hypot(gx - self.x, gy - self.y)
                if d >= R:
                    continue
                k = (1.0 - d / R) ** 2
                col = lerp_color(DOT_DIM, DOT_COLOR, k * 0.7)
                pygame.draw.circle(surface, col, (gx, gy), 2 if k > 0.3 else 1)

    def draw(self, surface):
        t = self.time

        self.draw_near_dots(surface)

    
        for (ix, iy), life in self.flash.items():
            gx, gy = self.dot_pos(ix, iy)
            k = 1.0 - life / 0.6
            r = int(4 + 12 * k)
            col = lerp_color((150, 150, 158), DOT_DIM, k)
            pygame.draw.circle(surface, col, (gx, gy), r, 1)

        for rx, ry, age in self.rings:
            k = age / 0.7
            col = lerp_color((235, 235, 242), (0, 0, 0), k)
            rad = int(8 + 230 * (1.0 - (1.0 - k) ** 2))
            pygame.draw.circle(surface, col, (int(rx), int(ry)), rad, 2 if k < 0.5 else 1)

        for tn in self.thin:
            tn.draw(surface, t)
        for tn in self.thick:
            tn.draw(surface, t)

        for tn in self.thick + self.thin:
            if tn.grip is not None:
                gx, gy = self.dot_pos(*tn.grip)
                col = lerp_color((120, 120, 128), WHITE, tn.lit)
                pygame.draw.circle(surface, col, (gx, gy), 2 + (1 if tn.lit > 0.5 else 0))