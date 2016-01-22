#!/usr/bin/env python

import os
import uuid

import pygame
import pygame.camera
import pygame.locals

import RPi.GPIO as GPIO


class Photobooth (object):
    def __init__(self):
        """Create photobooth instance."""

        # our custom pygame events
        self.events = {'capture_event': pygame.locals.USEREVENT + 1}

        # setup pygame
        pygame.init()
        pygame.camera.init()
        self.size = (1920, 1080)
        self.running = True

        # create a display surface
        self.display = pygame.display.set_mode(self.size, pygame.FULLSCREEN)

        # grab a list of cameras and set the first to our camera.
        self.clist = pygame.camera.list_cameras()
        if not self.clist:
            raise ValueError("Sorry, no cameras detected.")
        self.cam = pygame.camera.Camera(self.clist[1], self.size)
        self.cam.start()

        # create a surface to capture to.
        self.snapshot = pygame.surface.Surface(self.size, 0, self.display)

    def _get_and_display(self):
        """Query the camera for an imgae and update the screen with it."""

        # Check for new images and grab if there.
        if self.cam.query_image():
            self.snapshot = self.cam.get_image(self.snapshot)

        # blit it to the display surface.
        self.display.blit(self.snapshot, (0, 0))
        pygame.display.flip()

    def _get_and_save(self, img_dir=None):
        """Get an image from the camera and save it to disk."""

        if not img_dir:
            base_dir = os.path.dirname(os.path.realpath(__file__))
            img_dir = os.path.join(base_dir, "saved_images")

        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        image = self.cam.get_image()
        filename = '%s.png' % str(uuid.uuid4())
        pygame.image.save(image, os.path.join(img_dir, filename))

    def capture(self, channel):
        """Create a pygame event of type capture_event and post it to the
        queue.
        """

        ce = pygame.event.Event(self.events['capture_event'])
        pygame.event.post(ce)

    def exit(self, channel):
        """Create a pygame event of type QUIT and post it to the queue."""

        quit = pygame.event.Event(pygame.locals.QUIT)
        pygame.event.post(quit)

    def run(self):
        """Read events of the pygame event queue and handle them."""

        while self.running:
            self._get_and_display()

            for event in pygame.event.get():
                if event.type == pygame.locals.QUIT:
                # close the camera safely and quit the pygame
                    self.cam.stop()
                    pygame.quit()
                    self.running = False
                elif event.type == self.events['capture_event']:
                    self._get_and_save()


def main():
    # GPIO pin assignemnts
    pins = {'quit': 4,
            'capture': 21}

    # Create or photobooth object
    photobooth = Photobooth()

    # Setup GPIO
    GPIO.setmode(GPIO.BCM)

    # Pin to gracefully exit the app.
    GPIO.setup(pins['quit'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(pins['quit'], GPIO.BOTH, bouncetime=300)
    GPIO.add_event_callback(pins['quit'], photobooth.exit)

    # Pin to capture a piture
    GPIO.setup(pins['capture'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(pins['capture'], GPIO.BOTH, bouncetime=300)
    GPIO.add_event_callback(pins['capture'], photobooth.capture)

    # start the app
    photobooth.run()

if __name__ == "__main__":
    main()
