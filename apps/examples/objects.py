from pepper.framework import *
from pepper import config

from time import time


class ObjectApplication(AbstractApplication, ObjectDetectionComponent, TextToSpeechComponent):

    OBJECT_TIMEOUT = 15

    def __init__(self, backend):
        """Tells about the objects it sees"""

        super(ObjectApplication, self).__init__(backend)
        self.objecttime = {}

    def on_object(self, image, objects):
        """
        On Object Event.
        Called every time one or more objects are detected in a camera frame.
        """
        for obj in objects:
            if self.is_object_recognition_appropriate(obj.name):
                self.say("I see a {}".format(obj.name))

    def is_object_recognition_appropriate(self, name):
        """Returns True if telling about objects is appropriate and updates Object Time"""
        if name not in self.objecttime or (time() - self.objecttime[name] > self.OBJECT_TIMEOUT):
            self.objecttime[name] = time()
            return True


if __name__ == "__main__":
    ObjectApplication(config.get_backend()).run()
