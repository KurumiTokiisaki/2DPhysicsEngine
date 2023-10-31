# used for sin() and cos() functions
import math
# used for making fun shapes
import random
# used for clock speed
import time

# used for making the screen and everything on it
import pygame
# used for full screen
from pygame.locals import *

clothFile = open('testCloth.cloth', 'r')
devMode = False
running = True
specialRelativity = False
startNova = False
starBirth = False
loadFile = True
stairFalling = False
recording = False
clockSim = False

update = True
exploded = False
tempSnap = -1
trainSpeed = 0
spawned = False
maxSpeed = 0.84
rate = 0.1
stationaryTime = 0
movingTime = 0
countSTime = True
countMTime = True
bounce = 0

flags = DOUBLEBUF  # FULLSCREEN | DOUBLEBUF
pygame.init()
clock = pygame.time.Clock()
# gravitational field strength
if specialRelativity or starBirth or startNova or clockSim:
    gConst = 0
else:
    gConst = 9.81
areaUnits = 0.01
font = pygame.font.SysFont("Times New Roman", 20)
bigFont = pygame.font.SysFont("Times New Roman", 69)


def force(mass, acceleration):
    return mass * acceleration


def capVolume(height, radius):
    return (1 / 3) * math.pi * (height ** 2) * ((3 * radius) - height)


# returns the area of a cap in a sphere
def capArea(height, radius):
    return 2 * math.pi * radius * height


# returns the radius of a cap in a sphere
def capRadius(height, sphereRadius):
    return math.sqrt((sphereRadius ** 2) - ((sphereRadius - height) ** 2))


# gets the distance between 2 points using Pythagoras'
def distance(pOne, pTwo):
    return math.sqrt(((pOne['coordinates'][0] - pTwo['coordinates'][0]) ** 2) + ((pOne['coordinates'][1] - pTwo['coordinates'][1]) ** 2))


def lorentzFactor(speed):  # speed is in geometrized units
    return 1 / math.sqrt(1 - speed ** 2)


# game screen settings
gameWindow = pygame.display.set_mode([1920, 1080], flags)
gameWindow.fill((0, 0, 0))


# returns the properties of a point as a dictionary
def drawPoint(x, y, oldX, oldY, radius, stopState, density, forces, show):
    return {'coordinates': [x, y], 'oldCoordinates': [oldX, oldY], 'radius': radius, 'stopState': stopState, 'velocities': [0, 0], 'energies': [0, 0], 'drags': [0, 0], 'liquidDrags': [0, 0],
            'frictions': [0, 0], 'upthrusts': [0, 0], 'staticCords': [0, 0], 'selfPos': pygame.draw.circle(gameWindow, [255, 255, 255], (-69, -69), 0), 'rects': 0,
            'mass': ((4 / 3) * math.pi * ((radius * areaUnits) ** 3)) * density, 'weight': ((4 / 3) * math.pi * ((radius * areaUnits) ** 3)) * density * gConst, 'buffers': [0, 0],
            'forces': [forces[0], (((4 / 3) * math.pi * ((radius * areaUnits) ** 3)) * density * gConst) + forces[1]], 'momentum': [0, 0], 'collidingWith': -1, 'show': show, 'collided': 0,
            'bounciness': bounce}


def drawStaticPoint(x, y, radius):
    return {'coordinates': [x, y], 'radius': radius}


# class for sprite that points can collide with
class CollisionActor(pygame.sprite.Sprite):
    def __init__(self, centerX, centerY, width, height):
        # super(CollisionActor, self).__init__()
        pygame.sprite.Sprite.__init__(self)
        self.width = width
        self.height = height
        self.origWidth = width
        self.origHeight = height
        self.surf = pygame.Surface((self.width, self.height))
        self.surf.fill((255, 255, 0))
        self.centerX = centerX
        self.centerY = centerY
        self.rect = self.surf.get_rect(center=(self.centerX, self.centerY))
        self.velocity = [0, 0]
        self.buffer = [0, 0]
        self.workFunction = 1  # 0.5

    def contract(self, lf, wh):
        if wh == 'width':
            pygame.sprite.Sprite.__init__(self)
            self.width = self.origWidth / lf
            self.surf = pygame.Surface((self.width, self.height))
            self.surf.fill((255, 255, 0))
        if wh == 'height':
            pygame.sprite.Sprite.__init__(self)
            self.surf = pygame.Surface((self.width, self.height))
            self.height = self.origHeight / lf
            self.surf.fill((255, 255, 0))

    def simulateXY(self, type):
        if ((self.velocity[type] % 1) < 1) and (self.velocity[type] > 0):
            # variable used to make the sprite move even when speed % 1 < 1
            # done since object cannot move less than one pixel at a time
            self.buffer[type] += self.velocity[type] % 1
        elif ((self.velocity[type] % -1) > -1) and (self.velocity[type] < 0):
            self.buffer[type] += self.velocity[type] % -1

        # moves the sprite when the sum of velocities from previous frames exceed 1 (pixel)
        if self.buffer[type] >= 1:
            self.buffer[type] -= 1
            self.rect.centerx += 1
        # same in the opposite direction
        elif self.buffer[type] <= -1:
            self.buffer[type] += 1
            self.rect.centerx -= 1

    def move(self):
        self.rect.centerx += self.velocity[0]
        self.rect.centery += self.velocity[1]


# class for sprite in which points can undergo liquid physics
class LiquidActor(pygame.sprite.Sprite):
    def __init__(self, centerX, centerY, width, height):
        pygame.sprite.Sprite.__init__(self)
        self.surf = pygame.Surface((width, height))
        self.surf.fill((0, 0, 255))
        self.surf.set_alpha(100)
        self.centerX = centerX
        self.centerY = centerY
        self.rect = self.surf.get_rect(center=(self.centerX, self.centerY))
        self.viscosity = 0.1
        self.density = 1000 * (areaUnits ** 3)


soundFile = 'jixaw-metal-pipe-falling-sound.mp3'
pygame.mixer.init()
sounds = []
soundCount = 0


class Point(pygame.sprite.Sprite):
    def __init__(self, gasDensity, damping, showJoints):
        pygame.sprite.Sprite.__init__(self)
        self.mass = 0

        self.xVelocity = 0
        self.yVelocity = 0
        self.xBuffer = 0
        self.yBuffer = 0

        self.force = 0
        self.xForce = 0
        self.yForce = 0
        self.xDrag = 0
        self.yDrag = 0
        self.gasDensity = gasDensity
        self.dragConst = 1
        self.upthrust = 0
        self.xLiquidDrag = 0
        self.yLiquidDrag = 0
        self.xMomentum = 0
        self.yMomentum = 0
        self.xEnergyStored = 0
        self.yEnergyStored = 0
        self.xFriction = 0
        self.collisionTolerance = 30
        self.points = []
        self.staticPoints = []
        self.lengths = []
        self.constrainConst = damping
        self.elasticEfficiency = 0
        self.xFrictionConst = 0.5
        self.collidingWith = 0
        self.extraJointLength = 0
        self.showJoints = showJoints
        self.blackHole = False
        self.whiteHole = False

    def simulateXY(self, counter, type):
        # calculate horizontal velocity using on force, drag, friction, etc. using Euler's method of integration
        self.points[counter]['velocities'][type] += ((self.points[counter]['forces'][type] - self.points[counter]['drags'][type] - self.points[counter]['frictions'][type] -
                                                      self.points[counter]['liquidDrags'][type] - self.points[counter]['upthrusts'][type]) / self.points[counter]['mass']) / 144

        if self.points[counter]['velocities'][type] > 0:
            # used to make the sprite move even when velocity < 1
            # done since objects in Pygame can't move less than one pixel
            self.points[counter]['buffers'][type] += self.points[counter]['velocities'][type] % -1
        elif self.points[counter]['velocities'][type] < 0:
            self.points[counter]['buffers'][type] -= self.points[counter]['velocities'][type] % 1

        # moves the sprite when the sum of velocities from previous frames exceed 1 (pixel)
        if self.points[counter]['buffers'][type] >= 1:
            self.points[counter]['buffers'][type] -= 1
            self.points[counter]['oldCoordinates'][type] += 1
        # same in the opposite direction
        elif self.points[counter]['buffers'][type] <= -1:
            self.points[counter]['buffers'][type] += 1
            self.points[counter]['oldCoordinates'][type] -= 1
        self.points[counter]['momentum'][type] = self.points[counter]['mass'] * self.points[counter]['velocities'][type]
        # try-except statement used as velocity of particles somehow become >10^1000 after dragging them around in high-density air
        try:
            self.points[counter]['energies'][type] = 0.5 * self.points[counter]['mass'] * (abs(self.points[counter]['velocities'][type]) ** 2)
        except OverflowError:
            self.points[counter]['velocities'][type] = 0

    def move(self):
        if specialRelativity:
            for spo in range(len(self.staticPoints)):
                pygame.draw.circle(gameWindow, [255, 255, 255], self.staticPoints[spo]['coordinates'], self.staticPoints[spo]['radius'])

        for po in range(len(self.points)):
            if specialRelativity:
                self.drawPath(po)

            # prevents a point from moving if said point has been snapped
            if self.points[po]['stopState']:
                self.points[po]['coordinates'] = self.points[po]['staticCords']
                self.points[po]['oldCoordinates'] = self.points[po]['staticCords']
            else:
                self.points[po]['staticCords'] = self.points[po]['coordinates']

            if devMode:
                displayInfo = [f'V(X): {round(self.points[po]["velocities"][0], 3)}m/s', f'V(Y): {round(self.points[po]["velocities"][1], 3)}m/s', f'F(X): {round(self.xForce, 3)}N',
                               f'F(Y): {round(self.points[po]["weight"], 3)}', f'D(X): {round(self.points[po]["drags"][0], 3)}', f'LD(X): {round(self.points[po]["liquidDrags"][0], 3)}',
                               f'D(Y): {round(self.points[po]["drags"][1], 3)}', f'LD(Y): {round(self.points[po]["liquidDrags"][1], 3)}',
                               f'FF(X): {round(self.points[po]["frictions"][0], 3)}', f'U: {round(self.points[po]["upthrusts"][1], 3)}',
                               f'Center: {round(self.points[po]["coordinates"][0])}, {round(self.points[po]["coordinates"][1])}', f'Colliding With: {self.points[po]["collidingWith"]}',
                               f'Collisions: {self.points[po]["collided"]}']
                for info in range(len(displayInfo)):
                    # draws the information on the screen
                    gameWindow.blit(font.render(displayInfo[info], True, 'white'), (100 + (po * 200), 60 + (info * 20)))

            if self.points[po]['show']:
                self.points[po]['selfPos'] = pygame.draw.circle(gameWindow, [255, 255, 255], (self.points[po]['coordinates'][0], self.points[po]['coordinates'][1]),
                                                                self.points[po]['radius'])
            else:
                self.points[po]['selfPos'] = pygame.draw.circle(gameWindow, [0, 0, 0], (self.points[po]['coordinates'][0], self.points[po]['coordinates'][1]), 1)  # 0.1)
            # self.rects[po] = self.points[po].surf.get_rect(center=(self.points[po]['coordinates'][0], self.points[po]['coordinates'][1]))

            if not self.points[po]['stopState']:
                # detect for collisions with collision sprites (solid)
                for collisions in range(len(collisionSprites)):
                    if self.points[po]['selfPos'].colliderect(collisionSprites[collisions]):
                        # pygame.mixer.music.load(soundFile)
                        # pygame.mixer.music.play()
                        if abs(self.points[po]['coordinates'][0] - collisionSprites[collisions].rect.left) < self.collisionTolerance:
                            self.points[po]['coordinates'][0] = self.points[po]['oldCoordinates'][0]
                            # self.points[po]['coordinates'][0] = collisionSprites[collisions].rect.left - self.points[po]['radius']
                            # exit()
                            # self.points[po]['energies'][0] *= collisionSprites[collisions].workFunction
                            # self.points[po]['velocities'][0] = math.sqrt((self.points[po]['energies'][0] * 2) / self.points[po]['mass']) * self.points[po]['bounciness']
                            self.points[po]['oldCoordinates'][0] = self.points[po]['coordinates'][0] + self.points[po]['velocities'][0]
                            # used for applying friction
                            self.points[po]['collidingWith'] = collisions
                        elif abs(self.points[po]['coordinates'][0] - collisionSprites[collisions].rect.right) < self.collisionTolerance:
                            self.points[po]['coordinates'][0] = self.points[po]['oldCoordinates'][0]
                            # self.points[po]['coordinates'][0] = collisionSprites[collisions].rect.right + self.points[po]['radius']
                            # self.points[po]['energies'][0] *= collisionSprites[collisions].workFunction
                            # self.points[po]['velocities'][0] = -math.sqrt((self.points[po]['energies'][0] * 2) / self.points[po]['mass']) * self.points[po]['bounciness']
                            self.points[po]['oldCoordinates'][0] = self.points[po]['coordinates'][0] + self.points[po]['velocities'][0]
                            # used for applying friction
                            self.points[po]['collidingWith'] = collisions

                        if abs(self.points[po]['coordinates'][1] - collisionSprites[collisions].rect.top) < self.collisionTolerance:
                            self.points[po]['coordinates'][1] = self.points[po]['oldCoordinates'][1]
                            # self.points[po]['coordinates'][1] = collisionSprites[collisions].rect.top - self.points[po]['radius']
                            # self.points[po]['energies'][1] *= collisionSprites[collisions].workFunction
                            # self.points[po]['velocities'][1] = math.sqrt((self.points[po]['energies'][1] * 2) / self.points[po]['mass']) * self.points[po]['bounciness']
                            self.points[po]['oldCoordinates'][1] = self.points[po]['coordinates'][1] + self.points[po]['velocities'][1]
                            # used for applying friction
                            self.points[po]['collidingWith'] = collisions
                        elif abs(self.points[po]['coordinates'][1] - collisionSprites[collisions].rect.bottom) < self.collisionTolerance:
                            self.points[po]['coordinates'][1] = self.points[po]['oldCoordinates'][1]
                            # self.points[po]['coordinates'][1] = collisionSprites[collisions].rect.bottom + self.points[po]['radius']
                            # self.points[po]['energies'][1] *= collisionSprites[collisions].workFunction
                            # self.points[po]['velocities'][1] = -math.sqrt((self.points[po]['energies'][1] * 2) / self.points[po]['mass']) * self.points[po]['bounciness']
                            self.points[po]['oldCoordinates'][1] = self.points[po]['coordinates'][1] + self.points[po]['velocities'][1]
                            # used for applying friction
                            self.points[po]['collidingWith'] = collisions
                        self.points[po]['collided'] += 1

                for collision in range(len(self.points)):
                    if (distance(self.points[po], self.points[collision]) <= (self.points[po]['radius'] + self.points[collision]['radius'])) and (po != collision):
                        try:
                            alpha = math.atan((self.points[collision]['coordinates'][1] - self.points[po]['coordinates'][1]) / (self.points[collision]['coordinates'][0] - self.points[po]['coordinates'][0]))
                        except ZeroDivisionError:
                            alpha = 0
                        resultantVelocity = math.sqrt((self.points[po]['velocities'][0] ** 2) + (self.points[po]['velocities'][1] ** 2))
                        pointOne = self.points[po]['coordinates']
                        pointTwo = self.points[collision]['coordinates']
                        if pointOne[0] < pointTwo[0]:
                            self.points[po]['coordinates'][0] = self.points[po]['oldCoordinates'][0]
                            self.points[po]['oldCoordinates'][0] = self.points[po]['coordinates'][0] + (resultantVelocity * math.cos(alpha))
                            self.points[po]['coordinates'][1] = self.points[po]['oldCoordinates'][1]
                            self.points[po]['oldCoordinates'][1] = self.points[po]['coordinates'][1] + (resultantVelocity * math.sin(alpha))
                        else:
                            self.points[po]['coordinates'][0] = self.points[po]['oldCoordinates'][0]
                            self.points[po]['oldCoordinates'][0] = self.points[po]['coordinates'][0] - (resultantVelocity * math.cos(alpha))
                            self.points[po]['coordinates'][1] = self.points[po]['oldCoordinates'][1]
                            self.points[po]['oldCoordinates'][1] = self.points[po]['coordinates'][1] - (resultantVelocity * math.sin(alpha))
                        # self.points[po]['velocities'] = [resultantVelocity * math.cos(alpha), resultantVelocity * math.sin(alpha)]
                        # apply friction
                        if (self.points[po]['selfPos'].bottom <= collisionSprites[self.points[po]['collidingWith']].rect.top) and (self.points[po]['collidingWith'] != -1):
                            # self.updateFriction(po)
                            None
                        else:
                            self.points[po]['frictions'][0] = 0
                            self.points[po]['collidingWith'] = -1

                # detect for collisions with collision sprites (liquid)
                for liquids in range(len(liquidSprites)):
                    if self.points[po]['selfPos'].colliderect(liquidSprites[liquids]):
                        if 0 < (self.points[po]['selfPos'].bottom - liquidSprites[liquids].rect.top) < (self.points[po]["radius"]):
                            self.points[po]['upthrusts'][1] = liquidSprites[liquids].density * gConst * capVolume((self.points[po]['selfPos'].bottom - liquidSprites[liquids].rect.top),
                                                                                                                  self.points[po]['radius']) * areaUnits
                        elif 0 < (liquidSprites[liquids].rect.bottom - self.points[po]['selfPos'].top) < (self.points[po]["radius"]):
                            self.points[po]['upthrusts'][1] = liquidSprites[liquids].density * gConst * capVolume((liquidSprites[liquids].rect.bottom - self.points[po]['selfPos'].top),
                                                                                                                  self.points[po]['radius']) * areaUnits
                        else:
                            self.points[po]['upthrusts'][1] = liquidSprites[liquids].density * gConst * (4 / 3) * math.pi * ((self.points[po]['radius']) ** 3) * areaUnits
                        self.updateDrag('liquid', po, liquids)
                    else:
                        self.points[po]['upthrusts'][1] = 0
                        self.points[po]['liquidDrags'][1] = 0
                        self.points[po]['liquidDrags'][0] = 0

                # Verlet integration
                pos = self.points[po]['coordinates']
                oldPos = self.points[po]['oldCoordinates']

                # calculating velocity
                self.points[po]['velocities'][0] = pos[0] - oldPos[0]
                self.points[po]['velocities'][1] = pos[1] - oldPos[1]
                self.simulateXY(po, 0)
                self.simulateXY(po, 1)
                # moving the point

                self.points[po]['oldCoordinates'] = pos
                self.points[po]['coordinates'] = [pos[0] + self.points[po]['velocities'][0], pos[1] + self.points[po]['velocities'][1]]
                self.updateDrag('gas', po, None)
                if self.blackHole:
                    self.absorb(po, 0)
                if self.whiteHole:
                    self.repel(po, 0)

    def updateDrag(self, collisionType, counter, lCounter):
        if collisionType == 'liquid':
            # Stokes' Law
            if (self.points[counter]['selfPos'].left - liquidSprites[lCounter].rect.left) < 0:
                self.points[counter]['liquidDrags'][1] = 6 * math.pi * liquidSprites[lCounter].viscosity * (
                    capRadius((self.points[counter]['selfPos'].right - liquidSprites[lCounter].rect.left), self.points[counter]['radius'])) * self.points[counter]['velocities'][
                                                             1] * areaUnits
                self.points[counter]['liquidDrags'][0] = 6 * math.pi * liquidSprites[lCounter].viscosity * (
                    capRadius((self.points[counter]['selfPos'].right - liquidSprites[lCounter].rect.left), self.points[counter]['radius'])) * self.points[counter]['velocities'][
                                                             0] * areaUnits
                self.points[counter]['drags'][1] = 0.5 * math.pi * self.gasDensity * (abs(self.points[counter]['velocities'][1]) * self.points[counter]['velocities'][1]) * (
                        capRadius((liquidSprites[lCounter].rect.left - self.points[counter]['selfPos'].left), self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits
                self.points[counter]['drags'][0] = 0.5 * math.pi * self.gasDensity * (abs(self.points[counter]['velocities'][0]) * self.points[counter]['velocities'][0]) * (
                        capRadius((liquidSprites[lCounter].rect.left - self.points[counter]['selfPos'].left), self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits
            elif (self.points[counter]['selfPos'].right - liquidSprites[lCounter].rect.right) > 0:
                self.points[counter]['liquidDrags'][1] = 6 * math.pi * liquidSprites[lCounter].viscosity * (
                    capRadius((liquidSprites[lCounter].rect.right - self.points[counter]['selfPos'].left), self.points[counter]['radius'])) * self.points[counter]['velocities'][
                                                             1] * areaUnits
                self.points[counter]['liquidDrags'][0] = 6 * math.pi * liquidSprites[lCounter].viscosity * (
                    capRadius((liquidSprites[lCounter].rect.right - self.points[counter]['selfPos'].left), self.points[counter]['radius'])) * self.points[counter]['velocities'][
                                                             0] * areaUnits
                self.points[counter]['drags'][1] = 0.5 * math.pi * self.gasDensity * (abs(self.points[counter]['velocities'][1]) * self.points[counter]['velocities'][1]) * (
                        capRadius((self.points[counter]['selfPos'].right - liquidSprites[lCounter].rect.right), self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits
                self.points[counter]['drags'][0] = 0.5 * math.pi * self.gasDensity * (abs(self.points[counter]['velocities'][0]) * self.points[counter]['velocities'][0]) * (
                        capRadius((self.points[counter]['selfPos'].right - liquidSprites[lCounter].rect.right), self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits
            else:
                self.points[counter]['liquidDrags'][1] = 6 * liquidSprites[lCounter].viscosity * math.pi * (self.points[counter]['radius']) * self.points[counter]['velocities'][
                    1] * areaUnits
                self.points[counter]['drags'][1] = 0

            if (self.points[counter]['selfPos'].top - liquidSprites[lCounter].rect.top) < 0:
                self.points[counter]['liquidDrags'][0] = 6 * math.pi * liquidSprites[lCounter].viscosity * capRadius(
                    (self.points[counter]['selfPos'].bottom - liquidSprites[lCounter].rect.top), self.points[counter]['radius']) * self.points[counter]['velocities'][0] * areaUnits
                self.points[counter]['liquidDrags'][1] = 6 * math.pi * liquidSprites[lCounter].viscosity * capRadius(
                    (self.points[counter]['selfPos'].bottom - liquidSprites[lCounter].rect.top), self.points[counter]['radius']) * self.points[counter]['velocities'][1] * areaUnits
                self.points[counter]['drags'][0] = 0.5 * math.pi * self.gasDensity * (abs(self.points[counter]['velocities'][0]) * self.points[counter]['velocities'][0]) * (
                        capRadius((liquidSprites[lCounter].rect.top - self.points[counter]['selfPos'].top), self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits
                self.points[counter]['drags'][1] = 0.5 * math.pi * self.gasDensity * (abs(self.points[counter]['velocities'][1]) * self.points[counter]['velocities'][1]) * (
                        capRadius((liquidSprites[lCounter].rect.top - self.points[counter]['selfPos'].top), self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits
            elif (self.points[counter]['selfPos'].bottom - liquidSprites[lCounter].rect.bottom) > 0:
                self.points[counter]['liquidDrags'][0] = 6 * math.pi * liquidSprites[lCounter].viscosity * capRadius(
                    (liquidSprites[lCounter].rect.bottom - self.points[counter]['selfPos'].top), self.points[counter]['radius']) * self.points[counter]['velocities'][0] * areaUnits
                self.points[counter]['liquidDrags'][1] = 6 * math.pi * liquidSprites[lCounter].viscosity * capRadius(
                    (liquidSprites[lCounter].rect.bottom - self.points[counter]['selfPos'].top), self.points[counter]['radius']) * self.points[counter]['velocities'][1] * areaUnits
                self.points[counter]['drags'][0] = 0.5 * math.pi * self.gasDensity * (abs(self.points[counter]['velocities'][0]) * self.points[counter]['velocities'][0]) * (
                        capRadius((self.points[counter]['selfPos'].bottom - liquidSprites[lCounter].rect.bottom), self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits
                self.points[counter]['drags'][1] = 0.5 * math.pi * self.gasDensity * (abs(self.points[counter]['velocities'][1]) * self.points[counter]['velocities'][1]) * (
                        capRadius((self.points[counter]['selfPos'].bottom - liquidSprites[lCounter].rect.bottom), self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits
            else:
                self.points[counter]['liquidDrags'][0] = 6 * liquidSprites[lCounter].viscosity * math.pi * (self.points[counter]['radius']) * self.points[counter]['velocities'][
                    0] * areaUnits
                self.points[counter]['drags'][0] = 0
        else:
            # air resistance
            self.points[counter]['drags'][0] = 0.5 * self.gasDensity * (self.points[counter]['velocities'][0] * abs(self.points[counter]['velocities'][0])) * (
                    (2 * math.pi) * (self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits
            self.points[counter]['drags'][1] = 0.5 * self.gasDensity * (self.points[counter]['velocities'][1] * abs(self.points[counter]['velocities'][1])) * (
                    (2 * math.pi) * (self.points[counter]['radius']) ** 2) * self.dragConst * areaUnits

    def updateFriction(self, counter):
        # friction from the ground
        print('friction')
        if self.points[counter]['velocities'][0] > 0:
            self.points[counter]['frictions'][0] = self.xFrictionConst * self.points[counter]['weight']
        elif self.points[counter]['velocities'][0] < 0:
            self.points[counter]['frictions'][0] = -self.xFrictionConst * self.points[counter]['weight']

    def absorb(self, counter, absorber):
        if self.points[counter]['show'] and (self.points[absorber]['selfPos'].colliderect(self.points[counter]['selfPos'])):
            self.points[absorber]['radius'] += 0.125  # self.points[counter]['radius']
            if (self.points[absorber]['radius'] % 1) == 0:
                self.constrainConst += 0.0001
            self.points[counter]['show'] = False

    def repel(self, counter, absorber):
        if (not self.points[counter]['show']) and (not self.points[absorber]['selfPos'].colliderect(self.points[counter]['selfPos'])):
            self.points[absorber]['radius'] -= 0.125  # self.points[counter]['radius']
            if (self.points[absorber]['radius'] % 1) == 0:
                self.constrainConst -= 0.0001
            self.points[counter]['show'] = True

    def Shape(self, points, joints):
        # returns (in an organized way) the properties of a shape
        self.lengths = [distance(points[joints[j][0]], points[joints[j][1]]) + self.extraJointLength for j in range(len(joints))]
        return {'points': points, 'joints': joints, 'lengths': self.lengths}

    def constrainShape(self, shapeSprite):
        # increasing distance between points will cause them to retain their original lengths
        for i in range(len(shapeSprite['joints'])):
            l = shapeSprite['lengths'][i]
            if self.blackHole:
                l = 0
            dist = distance(shapeSprite['points'][shapeSprite['joints'][i][0]], shapeSprite['points'][shapeSprite['joints'][i][1]])
            diffX = shapeSprite['points'][shapeSprite['joints'][i][0]]['coordinates'][0] - shapeSprite['points'][shapeSprite['joints'][i][1]]['coordinates'][0]
            diffY = shapeSprite['points'][shapeSprite['joints'][i][0]]['coordinates'][1] - shapeSprite['points'][shapeSprite['joints'][i][1]]['coordinates'][1]
            try:
                updateX = self.constrainConst * diffX * ((l - dist) / dist)
                updateY = self.constrainConst * diffY * ((l - dist) / dist)
            except ZeroDivisionError:
                continue
            if not shapeSprite['points'][shapeSprite['joints'][i][0]]['stopState']:
                shapeSprite['points'][shapeSprite['joints'][i][0]]['coordinates'][0] += updateX
                shapeSprite['points'][shapeSprite['joints'][i][0]]['coordinates'][1] += updateY
            if not shapeSprite['points'][shapeSprite['joints'][i][1]]['stopState']:
                shapeSprite['points'][shapeSprite['joints'][i][1]]['coordinates'][0] -= updateX
                shapeSprite['points'][shapeSprite['joints'][i][1]]['coordinates'][1] -= updateY

    def drawPath(self, counter):
        self.staticPoints.append(drawStaticPoint(self.points[counter]['coordinates'][0], self.points[counter]['coordinates'][1], 1))

    def renderShape(self, shapeSprite, color=(255, 255, 255), thickness=3):
        for j in shapeSprite['joints']:
            start = shapeSprite['points'][j[0]]['coordinates'][0], shapeSprite['points'][j[0]]['coordinates'][1]
            end = shapeSprite['points'][j[1]]['coordinates'][0], shapeSprite['points'][j[1]]['coordinates'][1]
            if self.showJoints:
                pygame.draw.line(gameWindow, color, start, end, thickness)

    def box(self, points, joint):
        self.points = points
        joints = joint
        return self.Shape(self.points, joints)


def load(sprite):
    contents = clothFile.readlines()
    contents[0] = contents[0].replace('[', '')
    contents[0] = contents[0].replace(']', '')
    contents[1] = contents[1].replace('[', '')
    contents[1] = contents[1].replace(']', '')
    contents[3] = contents[3].replace('[', '')
    contents[3] = contents[3].replace(']', '')
    tempString = ''
    for _ in range(len(contents[2])):
        if 0 < _ < (len(contents[2]) - 3):
            tempString = f'{tempString}{contents[2][_]}'
    contents[2] = tempString
    contents[2] = f'{contents[2]}, '

    coordinates = list(map(str.strip, contents[0].split('), ')))
    for cordI in range(len(coordinates)):
        coordinates[cordI] = coordinates[cordI].replace('(', '')
    coordinates.pop(-1)
    for cordI in range(len(coordinates)):
        coordinates[cordI] = list(map(int, coordinates[cordI].split(', ')))

    radii = list(map(str.strip, contents[1].split(', ')))
    for radI in range(len(radii)):
        radii[radI] = float(radii[radI])

    joints = list(map(str.strip, contents[2].split('], ')))
    joints.pop(-1)
    for jointI in range(len(joints)):
        joints[jointI] = joints[jointI].replace('[', '')
        joints[jointI] = list(map(str.strip, joints[jointI].split(', ')))
        for jointII in range(len(joints[jointI])):
            joints[jointI][jointII] = int(joints[jointI][jointII])

    densities = list(map(str.strip, contents[3].split(', ')))

    for _ in range(len(coordinates)):
        x, y = coordinates[_][0], coordinates[_][1]
        sprite.points.append(drawPoint(x, y, x, y, radii[_], False, int(densities[_]), [0, 0], True))

    return {'coordinates': coordinates, 'radii': radii, 'joints': joints}


if clockSim:
    collisionSprites = []
    liquidSprites = []
    spinRate = 0
elif not specialRelativity:
    collisionSprites = [CollisionActor(centerX=1500, centerY=500, width=100, height=1000), CollisionActor(centerX=0, centerY=500, width=100, height=1000),
                        CollisionActor(centerX=750, centerY=1000, width=1500, height=100), CollisionActor(centerX=750, centerY=0, width=1500, height=100),
                        CollisionActor(centerX=750, centerY=870, width=300, height=200)]
    liquidSprites = [LiquidActor(centerX=1400, centerY=900, width=1500, height=300)]
elif specialRelativity:
    collisionSprites = [CollisionActor(centerX=925, centerY=100, width=1650, height=40), CollisionActor(centerX=120, centerY=280, width=40, height=400),
                        CollisionActor(centerX=925, centerY=500, width=1650, height=40), CollisionActor(centerX=1730, centerY=280, width=40, height=400),
                        CollisionActor(centerX=925, centerY=600, width=1650, height=40), CollisionActor(centerX=120, centerY=780, width=40, height=400),
                        CollisionActor(centerX=925, centerY=1000, width=1650, height=40), CollisionActor(centerX=1730, centerY=780, width=40, height=400),
                        CollisionActor(centerX=925, centerY=603, width=100, height=46), CollisionActor(centerX=925, centerY=103, width=100, height=46)]
    liquidSprites = []

testPoint = Point(showJoints=True, gasDensity=0.01293, damping=0.2)
testShape = Point(showJoints=True, gasDensity=0.01293, damping=0.2)
testCloth = Point(showJoints=True, gasDensity=0.01293, damping=0.2)
testReliever = Point(showJoints=True, gasDensity=0.01293, damping=0.2)
insane = Point(showJoints=True, gasDensity=0.01293, damping=0.6)
insane.extraJointLength = random.randint(50, 400)

# add a feature ask user which 'preset' they want to load: box, insane, their own custom box, etc.

box = testShape.box(points=[drawPoint(250, 100, 250, 100, 10, False, 8, [0, 0], True), drawPoint(250 + 50, 100, 250 + 50, 100, 10, False, 8, [0, 0], True),
                            drawPoint(250 + 50, 100 + 50, 250 + 50, 100 + 50, 10, False, 8, [0, 0], True), drawPoint(250, 100 + 50, 250, 100 + 50, 10, False, 8, [0, 0], True),
                            drawPoint(250 - 50, 100, 250 - 50, 100, 10, False, 8, [0, 0], True), drawPoint(250 - 50, 100 + 50, 250 - 50, 100 + 50, 10, False, 8, [0, 0], True)],
                    joint=[[0, 1], [1, 2], [2, 3], [3, 0], [1, 5], [2, 4], [0, 4], [3, 5], [4, 5]])

tempPoints = []
tempJoints = []
for x in range(10):
    for y in range(10):
        tempPoints.append(drawPoint(100 + (x * 25), 100 + (y * 25), 100 + (x * 25), 100 + (y * 25), 5, False, 8, [0, 0], True))
        tempJoints.append([(x * 10) + y - 1, (x * 10) + y])
    tempJoints.pop(-10)

for x in range(10 - 1):
    for y in range(10):
        tempJoints.append([(x * 10) + y, (x * 10) + y + 10])

cloth = testCloth.box(points=tempPoints, joint=tempJoints)
tempPoints = []
tempJoints = []

for x in range(20):
    tempPoints.append(drawPoint(100 + (x * 40), 100, 100 + (x * 40), 100, 20, False, 8, [0, 0], True))
    tempJoints.append([x - 1, x])
tempJoints.pop(0)

stressReliever = testReliever.box(points=tempPoints, joint=tempJoints)
tempPoints = []
tempJoints = []

for x in range(500):
    tempPoints.append(drawPoint(100, 100, random.uniform(80, 100), random.uniform(80, 100), random.uniform(5, 20), False, 8, [0, 0], True))
    tempJoints.append([random.randint(0, 499), random.randint(0, 499)])

insanity = insane.box(points=tempPoints, joint=tempJoints)

# for rs in range(10):
#    for rss in range(10):
#        rectSprites.append(RectActor(posX=100 + (rss * 70), posY=100 + (rs * 70), width=30, height=30, orientation=0, spin=0, xForce=1000))

clothFile = open('testCloth.cloth', 'r')

disable = False
objectList = {'objects': [testShape, testCloth, testReliever], 'sprites': [box, cloth, stressReliever], 'drags': [len(testShape.points), len(testCloth.points), len(testReliever.points)]}
# objectList = {'objects': [testShape], 'sprites': [box], 'drags': [len(testShape.points)]}
objectList = {'objects': [insane], 'sprites': [insanity], 'drags': [len(insane.points)]}

if starBirth:
    protostar = Point(showJoints=False, gasDensity=0, damping=0.001)
    protostar.blackHole = True

    pX, pY = 950, 550
    ranRange = 800
    protostarPoints = [drawPoint(pX, pY, pX, pY, 10, True, 1, [0, 0], True)]
    protostarPoints[0]['staticCords'] = [pX, pY]
    protostarJoints = []
    for x in range(500):
        xRan = random.randint(pX - ranRange, pX + ranRange)
        yRan = random.randint(pY - ranRange, pY + ranRange)
        xRanSpeed = random.randint(-30, 30)
        yRanSpeed = random.randint(-30, 30)
        radiusRan = random.randint(2, 5)
        protostarPoints.append(drawPoint(xRan, yRan, xRan + xRanSpeed, yRan + yRanSpeed, radiusRan, False, 0.08, [0, 0], True))
        protostarJoints.append([0, x + 1])

    protostarCloth = protostar.box(points=protostarPoints, joint=protostarJoints)
    objectList = {'objects': [protostar], 'sprites': [protostarCloth], 'drags': [len(protostar.points)]}

if loadFile:
    cFile = Point(gasDensity=0, showJoints=True, damping=0.1)
    if clockSim:
        cFile.constrainConst = 1
    try:
        stuff = load(cFile)
    except IndexError:
        exit(print('No file loaded!'))

    cFile.box(points=cFile.points, joint=stuff['joints'])
    objectList = {'objects': [cFile], 'sprites': [cFile.box(joint=stuff['joints'], points=cFile.points)], 'drags': [len(cFile.points)]}

if startNova:
    supernova = Point(showJoints=True, gasDensity=0, damping=0.001)
    pX, pY = 950, 550
    ranRange = 5
    ranSpeedRange = 4
    supernovaPoints = [drawPoint(pX, pY, pX, pY, 100, True, 10, [0, 0], True)]
    supernovaPoints[0]['staticCords'] = [pX, pY]
    supernovaJoints = []
    for x in range(500):
        xRan = random.randint(pX - ranRange, pX + ranRange)
        yRan = random.randint(pY - ranRange, pY + ranRange)
        xRanSpeed = random.randint(-ranSpeedRange, ranSpeedRange)
        yRanSpeed = random.randint(-ranSpeedRange, ranSpeedRange)
        supernovaPoints.append(drawPoint(xRan, yRan, xRan + xRanSpeed, yRan + yRanSpeed, 1, False, 0.08, [0, 0], False))
        supernovaJoints.append([0, x + 1])
    supernovaCloth = supernova.box(points=supernovaPoints, joint=supernovaJoints)
    supernova.whiteHole = True
    objectList = {'objects': [supernova], 'sprites': [supernovaCloth], 'drags': [len(supernova.points)]}
    radiusChangeRate = 1

if specialRelativity:
    point = Point(showJoints=True, damping=0, gasDensity=0)
    pointCloth = point.box(joint=[], points=point.points)
    objectList = {'objects': [point], 'sprites': [pointCloth], 'drags': [len(point.points)]}

if stairFalling:
    clothFile = open('testCloth.cloth', 'r')
    stairs = Point(showJoints=True, damping=0.4, gasDensity=0)
    try:
        stuff = load(stairs)
    except IndexError:
        exit(print('No file loaded!'))
    stairsCloth = stairs.box(joint=[[0, 1]], points=stairs.points)
    stairs.box(points=stairs.points, joint=stuff['joints'])
    objectList = {'objects': [stairs], 'sprites': [stairs.box(joint=stuff['joints'], points=stairs.points)], 'drags': [len(stairs.points)]}
    collisionSprites = []
    for c in range(6):
        collisionSprites.append(CollisionActor(centerX=10 + (c * 20), centerY=400 + (c * 100), width=300, height=100))
    collisionSprites.append(CollisionActor(centerX=gameWindow.get_width() / 2, centerY=400 + ((c + 1) * 100), width=gameWindow.get_width(),
                                           height=100))  # collisionSprites = [CollisionActor(centerX=200, centerY=1000, width=1000, height=100)]

if recording:
    time.sleep(10)

while running:
    if specialRelativity:
        lFactor = lorentzFactor(trainSpeed)
        collisionSprites[4].contract(lf=lFactor, wh='width')
        collisionSprites[6].contract(lf=lFactor, wh='width')
        if trainSpeed < maxSpeed:
            collisionSprites[7].rect = collisionSprites[7].surf.get_rect(
                center=(collisionSprites[7].centerX - (collisionSprites[4].origWidth - collisionSprites[4].width), collisionSprites[7].centerY))
            collisionSprites[8].rect = collisionSprites[8].surf.get_rect(
                center=(collisionSprites[8].centerX - ((collisionSprites[4].origWidth - collisionSprites[4].width) / 2), collisionSprites[8].centerY))
            rate *= 1.0354
            trainSpeed += 0.003 / rate  # rate at which length is contracted for animation purposes
        elif not spawned:
            point.points.append(drawPoint(collisionSprites[8].centerX - ((collisionSprites[4].origWidth - collisionSprites[4].width) / 2), 980,
                                          collisionSprites[8].centerX - ((collisionSprites[4].origWidth - collisionSprites[4].width) / 2), 980, 10, False, 100, [0, 0], True))
            point.points.append(drawPoint(925, 480, 925, 480, 10, False, 100, [0, 0], True))
            point.points[0]['coordinates'][1] += math.sqrt(1 - (maxSpeed ** 2))
            point.points[0]['coordinates'][0] += maxSpeed
            point.points[1]['coordinates'][1] += 1
            spawned = True
            countSTime = True
            countMTime = True
        else:
            for trainPart in range(4, 9):
                collisionSprites[trainPart].velocity[0] = maxSpeed
            if point.points[0]['collided'] >= 3:
                countMTime = False
            if point.points[1]['collided'] >= 3:
                countSTime = False
            if countMTime:
                movingTime += 1
            if countSTime:
                stationaryTime += 1
            gameWindow.blit(bigFont.render(f'Time: {stationaryTime}', True, 'white'), (175, collisionSprites[1].centerY - 25))
            gameWindow.blit(bigFont.render(f'Time: {movingTime}', True, 'white'), (175, collisionSprites[5].centerY - 25))
            gameWindow.blit(
                font.render(f'Lorentz Factor: {round(lFactor, 3)}, Length Contraction: {round((1 - (collisionSprites[0].width / lFactor) / collisionSprites[0].width) * 100, 2)}%', True,
                            'white'), (175, collisionSprites[5].centerY - collisionSprites[1].centerY + 37))

    if stairFalling:
        if stairs.points[0]['velocities'][1] >= 10:
            stairs.points[0]['velocities'][1] = 9.99
        elif stairs.points[0]['velocities'][1] <= -10:
            stairs.points[0]['velocities'][1] = -9.99
        # if abs(stairs.points[0]['velocities'][0]) >= 10:
        #     stairs.points[0]['velocities'][0] = 9.99
        # elif abs(stairs.points[0]['velocities'][0]) <= -10:
        #     stairs.points[0]['velocities'][0] = -9.99
        if stairs.points[4]['collided'] == 0:
            for c in range(len(collisionSprites)):
                collisionSprites[c].contract(1 / math.sqrt(1 - ((stairs.points[0]['velocities'][1] ** 2) / (10 ** 2))), 'height')
                collisionSprites[c].contract(1 / math.sqrt(1 - ((stairs.points[0]['velocities'][0] ** 2) / (10 ** 2))), 'width')
                collisionSprites[c].rect = collisionSprites[c].surf.get_rect(center=(collisionSprites[c].centerX - (collisionSprites[c].origWidth - collisionSprites[c].width) * (c + 4),
                                                                                     collisionSprites[c].centerY - (collisionSprites[c].origHeight - collisionSprites[c].height) * (c + 4)))

    if clockSim:
        spinRate += 0.1
        if (cFile.points[1]['coordinates'][0] <= (gameWindow.get_width() / 2)) and (cFile.points[1]['coordinates'][0] <= (gameWindow.get_height() / 2)):  # 2nd quartile
            cFile.points[1]['oldCoordinates'][0] -= spinRate
        elif (cFile.points[1]['coordinates'][0] <= (gameWindow.get_width() / 2)) and (cFile.points[1]['coordinates'][0] > (gameWindow.get_height() / 2)):  # 3rd quartile
            cFile.points[1]['oldCoordinates'][1] += spinRate
        elif (cFile.points[1]['coordinates'][0] >= (gameWindow.get_width() / 2)) and (cFile.points[1]['coordinates'][0] <= (gameWindow.get_height() / 2)):  # 1st quartile
            cFile.points[1]['oldCoordinates'][0] += spinRate
        elif (cFile.points[1]['coordinates'][0] >= (gameWindow.get_width() / 2)) and (cFile.points[1]['coordinates'][0] > (gameWindow.get_height() / 2)):  # 4th quartile
            cFile.points[1]['oldCoordinates'][1] -= spinRate
        cFile.points[0]['staticCords'] = (gameWindow.get_width() / 2, gameWindow.get_height() / 2)
        cFile.points[0]['stopState'] = True

    mousePos = pygame.mouse.get_pos()
    for CSprites in range(len(collisionSprites)):
        collisionSprites[CSprites].simulateXY(0)
        collisionSprites[CSprites].simulateXY(1)
        collisionSprites[CSprites].move()
        gameWindow.blit(collisionSprites[CSprites].surf, collisionSprites[CSprites].rect)
    # for RSprites in range(len(rectSprites)):
    # rectSprites[RSprites].draw()
    # rectSprites[RSprites].move()

    for objectIndex in range(len(objectList['objects'])):
        objectList['objects'][objectIndex].renderShape(objectList['sprites'][objectIndex])
        objectList['objects'][objectIndex].constrainShape(objectList['sprites'][objectIndex])
        objectList['objects'][objectIndex].move()

        if pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]:
            # rectSprites[0].p['coordinates'] = [mousePos[0], mousePos[1]]
            # rectSprites[0].xDrag, rectSprites[0].yDrag = 0, 0

            if (objectList['drags'][objectIndex] < len(objectList['objects'][objectIndex].points)) and pygame.mouse.get_pressed()[0] and \
                    objectList['objects'][objectIndex].points[objectList['drags'][objectIndex]]['stopState']:
                objectList['objects'][objectIndex].points[objectList['drags'][objectIndex]]['stopState'] = False
                tempSnap = objectIndex
                objectList['objects'][objectIndex].points[objectList['drags'][objectIndex]]['coordinates'] = [mousePos[0],
                                                                                                              mousePos[1]]  # sets last clicked point's cords to the pointer's cords
            elif (objectList['drags'][objectIndex] < len(objectList['objects'][objectIndex].points)) and pygame.mouse.get_pressed()[0]:
                objectList['objects'][objectIndex].points[objectList['drags'][objectIndex]]['coordinates'] = [mousePos[0],
                                                                                                              mousePos[1]]  # sets last clicked point's cords to the pointer's cords
            if (objectList['drags'][objectIndex] < len(objectList['objects'][objectIndex].points)) and pygame.mouse.get_pressed()[2] and (not disable):
                objectList['objects'][objectIndex].points[objectList['drags'][objectIndex]]['stopState'] = True
            if (objectList['drags'][objectIndex] < len(objectList['objects'][objectIndex].points)) and pygame.mouse.get_pressed()[2] and disable:
                objectList['objects'][objectIndex].points[objectList['drags'][objectIndex]]['stopState'] = False

            else:
                for _ in range(len(objectList['objects'][objectIndex].points)):
                    if (objectList['objects'][objectIndex].points[_]['coordinates'][0] <= (mousePos[0] + objectList['objects'][objectIndex].points[_]['radius'])) and (
                            objectList['objects'][objectIndex].points[_]['coordinates'][0] >= (mousePos[0] - objectList['objects'][objectIndex].points[_]['radius'])) and (
                            objectList['objects'][objectIndex].points[_]['coordinates'][1] <= (mousePos[1] + objectList['objects'][objectIndex].points[_]['radius'])) and (
                            objectList['objects'][objectIndex].points[_]['coordinates'][1] >= (mousePos[1] - objectList['objects'][objectIndex].points[_]['radius'])) and (
                            objectList['drags'][objectIndex] >= len(objectList['objects'][objectIndex].points)):  # determines whether the mouse pointer is in a point
                        if pygame.mouse.get_pressed()[0]:
                            objectList['objects'][objectIndex].points[_]['coordinates'] = [mousePos[0], mousePos[1]]  # sets the point's coordinates to the mouse pointer's coordinates
                            objectList['objects'][objectIndex].points[_]['drags'] = [0, 0]  # used to prevent infinite drag force between frames
                            objectList['drags'][objectIndex] = _  # temporary variable to allow dragging past the mouse pointer's range in a point
                        elif pygame.mouse.get_pressed()[2] and (not disable):
                            objectList['objects'][objectIndex].points[_]['stopState'] = False
                        elif pygame.mouse.get_pressed()[2] and disable:
                            objectList['objects'][objectIndex].points[_]['stopState'] = True

        elif pygame.mouse.get_rel()[0]:
            for _ in range(len(objectList['objects'])):
                if tempSnap >= 0:
                    objectList['objects'][tempSnap].points[objectList['drags'][tempSnap]]['stopState'] = True
                    tempSnap = -1
                objectList['drags'][_] = len(objectList['objects'][_].points)  # resets the temporary variable mentioned above

        if not pygame.mouse.get_pressed()[2]:
            disable = False  # used to allow points to be 'unstuck', ONLY after rclick is released

    for liquids in range(len(liquidSprites)):
        gameWindow.blit(liquidSprites[liquids].surf, liquidSprites[liquids].rect)

    # testPoint.draw()
    # testPoint.move()
    # testPoint.collision()
    if startNova:
        supernova.points[0]['radius'] += radiusChangeRate
        if supernova.points[0]['radius'] < 1:
            supernova.points[0]['radius'] = 0.9
            if (supernova.constrainConst > 0) and (not exploded):
                supernova.constrainConst = -0.01
                exploded = True
            else:
                supernova.constrainConst = 0.000001
        else:
            supernova.constrainConst += 0.00005
        radiusChangeRate -= 0.005

    if update:
        pygame.display.update()
    if stairFalling:
        clock.tick(144)
    else:
        clock.tick(144)
    gameWindow.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
