import time

import pygame
import math
from pygame.locals import *
import keyboard

running = True
devMode = False

flags = FULLSCREEN | DOUBLEBUF
pygame.init()
clock = pygame.time.Clock()

# game screen settings
gameWindow = pygame.display.set_mode([1920 * 2, 1080 * 2], flags)
gameWindow.fill((0, 0, 0))
font = pygame.font.SysFont("Times New Roman", 18)

minRadius = 10
defaultRadius = 10


def distance(pOne, pTwo):
    return math.sqrt((pOne ** 2) + (pTwo ** 2))


def drawPoint(x, y):
    return {'coordinates': [x, y], 'radius': defaultRadius, 'density': 8}


def button(text):
    if text == 'off':
        return False
    else:
        surface = pygame.Surface([100, 50])
        surface.fill([255, 0, 125])
        rect = surface.get_rect(center=(60, gameWindow.get_height() / 2))
        gameWindow.blit(surface, rect)
        gameWindow.blit(font.render(text, True, 'white'), (10, 530))
        return True


class Cloth(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.points = []
        self.joints = []
        self.lengths = []
        self.extraJointLength = 0

    def shape(self, points, joints):
        # returns (in an organized way) the properties of a shape
        self.lengths = [distance(points[joints[j][0]], points[joints[j][1]]) + self.extraJointLength for j in range(len(joints))]
        return {'points': points, 'joints': joints, 'lengths': self.lengths}

    def createPoint(self, point):
        self.points.append(point)

    def renderShape(self, color=(255, 255, 255), thickness=3):
        for j in self.joints:
            start = self.points[j[0]]['coordinates'][0], self.points[j[0]]['coordinates'][1]
            end = self.points[j[1]]['coordinates'][0], self.points[j[1]]['coordinates'][1]
            pygame.draw.line(gameWindow, color, start, end, thickness)


testCloth = Cloth()
pressed = False
rPressed = False
dragging = False
tempSnap = 0
dragPoint = -1
step = 0
tempJoint = [-1, -1]
textBoxes = []
textBoxContents = []
showButton = False
buttonPressed = False
buttonClicked = False
editBox = -1
boxHover = False
hoverBox = -1
keyboardPressed = False
pointHover = -1
tutorialText = [['Press the SPACEBAR to continue with the program at any time, and press ESC to quit.'],
                ['Left-click on the screen to make/drag a point', 'Right-click+drag points to edit their radii'],
                ['Drag between points to create joints', "Press 'd' to delete attached joints while hovering over a point", "Otherwise, press 'd' to undo"], ["Edit points' densities"]]

while running:
    if not devMode:
        try:
            for tTexts in range(len(tutorialText[step])):
                gameWindow.blit(font.render(tutorialText[step][tTexts], True, 'white'), (20, 20 + (20 * tTexts)))
        except IndexError:
            print('Please run conceptEngine.py')
            running = False

    # ends the program when escape pressed
    if keyboard.is_pressed('escape'):
        running = False

    # displays additional information if devmode is true
    if devMode:
        displayInfo = [f'{tempJoint}', f'{editBox}', f'{boxHover}', f'{pointHover}']
        for info in range(len(displayInfo)):
            # draws the information on the screen
            gameWindow.blit(font.render(displayInfo[info], True, 'white'), (100, 60 + (info * 20)))

    # general variable that holds the mouse pointer's position
    mousePos = pygame.mouse.get_pos()

    # checks to see if the pointer is in the purple button on the left of the screen, and if it's being clicked, and if the button is shown on the screen
    if (mousePos[0] < 110) and (mousePos[0] > 10) and (mousePos[1] < ((gameWindow.get_height() / 2) + 25)) and (mousePos[1] > ((gameWindow.get_height() / 2) - 25)) and \
            pygame.mouse.get_pressed()[0] and showButton:

        # general variable that holds the state of the button (whether it is on/off)
        if not buttonClicked:
            buttonClicked = True
            if not buttonPressed:
                buttonPressed = True
            elif buttonPressed:
                buttonPressed = False
    elif not pygame.mouse.get_pressed()[0]:
        buttonClicked = False

    for _ in range(len(testCloth.points)):
        pygame.draw.circle(gameWindow, [255, 255, 255], (testCloth.points[_]['coordinates'][0], testCloth.points[_]['coordinates'][1]), testCloth.points[_]['radius'])

    # goes to the next step of sprite creation upon pressing the spacebar
    if keyboard.is_pressed('space') and (not rPressed):
        step += 1
        rPressed = True
        buttonPressed = False
        editBox = -1
    elif not keyboard.is_pressed('space'):
        rPressed = False

    # first step of sprite creation that is point creation and changing radii
    if step == 1:
        # renders the button on the left side of the screen
        showButton = button('Edit Radius')
        if not boxHover:
            if (not dragging) and (dragPoint == -1):
                for po in range(len(testCloth.points)):
                    if (testCloth.points[po]['coordinates'][0] <= (mousePos[0] + testCloth.points[po]['radius'])) and (
                            testCloth.points[po]['coordinates'][0] >= (mousePos[0] - testCloth.points[po]['radius'])) and (
                            testCloth.points[po]['coordinates'][1] <= (mousePos[1] + testCloth.points[po]['radius'])) and (
                            testCloth.points[po]['coordinates'][1] >= (mousePos[1] - testCloth.points[po]['radius'])):
                        if pygame.mouse.get_pressed()[0]:
                            testCloth.points[po]['coordinates'] = pygame.mouse.get_pos()
                            dragPoint = po
                            dragging = True
                        elif pygame.mouse.get_pressed()[2]:
                            testCloth.points[po]['radius'] = distance(abs(mousePos[0] - testCloth.points[po]['coordinates'][0]),
                                                                      abs(mousePos[1] - testCloth.points[po]['coordinates'][1])) + minRadius
                    textBoxContents[po] = int(testCloth.points[po]['radius'])

            if dragging and pygame.mouse.get_pressed()[0] and (dragPoint != -1):
                testCloth.points[dragPoint]['coordinates'] = pygame.mouse.get_pos()

            if pygame.mouse.get_pressed()[0]:
                if (not pressed) and (not dragging) and (not buttonClicked):
                    testCloth.points.append(drawPoint(mousePos[0], mousePos[1]))
                    textBoxes.append([pygame.Surface((50, 20))])
                    textBoxes[-1][0].fill([255, 0, 125])
                    textBoxes[-1].append(textBoxes[-1][0].get_rect(center=(0, 0)))
                    textBoxContents.append(0)
                pressed = True
            elif not pygame.mouse.get_pressed()[0]:
                dragPoint = -1
                pressed = False
                dragging = False

    if step == 2:
        showButton = button('off')
        for po in range(len(testCloth.points)):
            if (testCloth.points[po]['coordinates'][0] <= (mousePos[0] + testCloth.points[po]['radius'])) and (
                    testCloth.points[po]['coordinates'][0] >= (mousePos[0] - testCloth.points[po]['radius'])) and (
                    testCloth.points[po]['coordinates'][1] <= (mousePos[1] + testCloth.points[po]['radius'])) and (
                    testCloth.points[po]['coordinates'][1] >= (mousePos[1] - testCloth.points[po]['radius'])):
                pointHover = po
                if pygame.mouse.get_pressed()[0] and (not pressed):
                    pressed = True
                    count = True
                    tempJoint[0] = po
                elif (not pygame.mouse.get_pressed()[0]) and (tempJoint[0] != -1):
                    pressed = False
                    tempJoint[1] = po
                if keyboard.is_pressed('d'):
                    for joints in range(len(testCloth.joints)):
                        for joint in range(len(testCloth.joints[joints])):
                            if testCloth.joints[joints][joint] == po:
                                testCloth.joints[joints] = ['', '']
                    try:
                        for _ in range(len(testCloth.joints)):
                            testCloth.joints.remove(['', ''])
                    except ValueError:
                        continue

            if (testCloth.points[pointHover]['coordinates'][0] >= (mousePos[0] + testCloth.points[pointHover]['radius'])) or (
                    testCloth.points[pointHover]['coordinates'][0] <= (mousePos[0] - testCloth.points[pointHover]['radius'])) or (
                    testCloth.points[pointHover]['coordinates'][1] >= (mousePos[1] + testCloth.points[pointHover]['radius'])) or (
                    testCloth.points[pointHover]['coordinates'][1] <= (mousePos[1] - testCloth.points[pointHover]['radius'])) and (pointHover != -1):
                pointHover = -1

            if pointHover == -1:
                if keyboard.is_pressed('d') and (len(testCloth.joints) > 0) and (not keyboardPressed):
                    keyboardPressed = True
                    testCloth.joints.pop(-1)
                elif (not keyboard.is_pressed('d')) and keyboardPressed:
                    keyboardPressed = False

        if pygame.mouse.get_pressed()[0] and (tempJoint[0] != -1):
            pygame.draw.line(gameWindow, [255, 255, 255], testCloth.points[tempJoint[0]]['coordinates'], mousePos, 3)
        elif not pygame.mouse.get_pressed()[0]:
            pressed = False

        if (tempJoint[0] != -1) and (tempJoint[1] != -1):
            testCloth.joints.append(tempJoint)
            tempJoint = [-1, -1]

    if step == 3:
        showButton = button('off')
        # enables text editing for density of each particle
        buttonPressed = True
        for po in range(len(testCloth.points)):
            textBoxContents[po] = testCloth.points[po]['density']

    for boxes in range(len(textBoxes)):
        if (mousePos[0] < textBoxes[boxes][1].center[0] + (50 / 2)) and (mousePos[0] > textBoxes[boxes][1].center[0] - (50 / 2)) and (
                mousePos[1] < textBoxes[boxes][1].center[1] + (20 / 2)) and (mousePos[1] > textBoxes[boxes][1].center[1] - (20 / 2)) and buttonPressed:
            boxHover = True
            hoverBox = boxes
            if pygame.mouse.get_pressed()[0]:
                editBox = boxes
        if (mousePos[0] > textBoxes[hoverBox][1].center[0] + (50 / 2)) or (mousePos[0] < textBoxes[hoverBox][1].center[0] - (50 / 2)) or (
                mousePos[1] > textBoxes[hoverBox][1].center[1] + (20 / 2)) or (mousePos[1] < textBoxes[hoverBox][1].center[1] - (20 / 2)) and (hoverBox != -1):
            boxHover = False
            hoverBox = -1

    testCloth.renderShape()

    if buttonPressed:
        for boxes in range(len(textBoxes)):
            textBoxes[boxes][1].center = (testCloth.points[boxes]['coordinates'][0], testCloth.points[boxes]['coordinates'][1])
            gameWindow.blit(textBoxes[boxes][0], textBoxes[boxes][1])
            gameWindow.blit(font.render(f'{textBoxContents[boxes]}', True, 'white'), (textBoxes[boxes][1].center[0] - 20, textBoxes[boxes][1].center[1] - 10))

    if (editBox != -1) and buttonPressed:
        if not keyboardPressed:
            for num in range(10):
                if keyboard.is_pressed(f'{num}'):
                    keyboardPressed = True
                    textBoxContents[editBox] = f'{(textBoxContents[editBox])}{num}'
                    break
            if keyboard.is_pressed('backspace'):
                keyboardPressed = True
                if len(str(textBoxContents[editBox])) > 1:
                    tempString = []
                    for chars in range(len(str(textBoxContents[editBox]))):
                        tempString.append(str(textBoxContents[editBox])[chars])
                    tempString.pop(-1)
                    textBoxContents[editBox] = ''
                    for chars_ in range(len(tempString)):
                        textBoxContents[editBox] = f'{textBoxContents[editBox]}{tempString[chars_]}'
                    textBoxContents[editBox] = int(textBoxContents[editBox])
                else:
                    textBoxContents[editBox] = 0

        if not (keyboard.is_pressed(f'{num}') or keyboard.is_pressed('backspace')):
            keyboardPressed = False
        if step == 1:
            testCloth.points[editBox]['radius'] = int(textBoxContents[editBox])
        if step == 3:
            testCloth.points[editBox]['density'] = int(textBoxContents[editBox])
        if keyboard.is_pressed('return'):
            if textBoxContents[editBox] == 0:
                testCloth.points.pop(editBox)
                textBoxes.pop(editBox)
                textBoxContents.pop(editBox)

                # the pop() function takes too long to process. so long in fact, that the program runs into an error when re-running the while loop when trying to find a location in memory that doesn't exist! this error will only occur if the mouse remains hovered over the text box from the most recently made point, as position -1 means the final position in the list.

                # p.s., I won't wanna fix this right now since I wanna show it to the class, since I think it's very interesting. to think that removing data from a list took so much processing power!
            editBox = -1  # time.sleep(1)

    pygame.display.update()
    clock.tick(144)
    gameWindow.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

f = open('testCloth.cloth', 'w')

writeCords = []
writeRadii = []
writeDensities = []
writeJoints = []
for things in range(len(testCloth.points)):
    writeCords.append(testCloth.points[things]['coordinates'])
    writeRadii.append(testCloth.points[things]['radius'])
    writeDensities.append(testCloth.points[things]['density'])
for joints in range(len(testCloth.joints)):
    writeJoints.append(testCloth.joints[joints])

tempStr = str(writeCords)
writeCords = ''
for _ in range(len(tempStr)):
    if _ < (len(tempStr) - 1):
        writeCords = f'{writeCords}{tempStr[_]}'
writeCords = f'{writeCords}, ]'

f.write(f'{writeCords} \n')
f.write(f'{writeRadii} \n')
f.write(f'{writeJoints} \n')
f.write(f'{writeDensities} \n')
f.close()
