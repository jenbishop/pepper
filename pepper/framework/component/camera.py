from pepper.framework import AbstractComponent
import numpy as np


class CameraComponent(AbstractComponent):
    def __init__(self, backend):
        super(CameraComponent, self).__init__(backend)
        self.backend.camera.callbacks += [self.on_image]

    def on_image(self, image):
        # type: (np.ndarray) -> None
        """
        On Image Event. Called every time an image was taken by Backend

        Parameters
        ----------
        image: np.ndarray
            Camera Frame
        """
        pass
