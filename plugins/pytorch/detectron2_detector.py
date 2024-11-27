"""

Key Issues / Questions:

    * Detectron2 itself needs to be installed. I am using a fork in geowatch,
      but I don't think it matters unless you are doing training.

    * kwiver on pypi only goes up to Python 3.8, what version of Python is
      VIAME primarily targeting?

    * Base detectron2 models dont have any indication of what the classes are,
      only the number. This is a common problem, we need to enrich the
      checkpoint and model configuration with class name information.

Dependency issues:

    # Workaround
    python -m pip install --verbose https://github.com/facebookresearch/fairscale/files/5783203/fairscale-0.1.4.tar.gz
    pip install fvcore --no-cache

"""

from kwiver.vital.algo import ImageObjectDetector
from kwiver.vital.types import (
    BoundingBox, DetectedObject, DetectedObjectSet, DetectedObjectType
)
import os
import numpy as np
import ubelt as ub


class Detectron2Detector(ImageObjectDetector):
    """
    Implementation of ImageObjectDetector class

    CommandLine:
        xdoctest -m plugins/pytorch/detectron2_detector.py Detectron2Detector --show

    Example:
        >>> import sys, ubelt
        >>> sys.path.append(ubelt.expandpath('~/code/VIAME/plugins'))
        >>> from pytorch.detectron2_detector import *  # NOQA
        >>> self = Detectron2Detector()
        >>> image_data = self.demo_image()
        >>> cfg_in = dict(
        >>>     checkpoint_fpath='COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml',
        >>>     base='COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml',
        >>> )
        >>> self.set_configuration(cfg_in)
        >>> self._kwiver_config.update(cfg_in)  # HACK
        >>> detected_objects = self.detect(image_data)
    """

    def __init__(self):
        ImageObjectDetector.__init__(self)

        # kwiver configuration variables
        self._kwiver_config = {
            'checkpoint_fpath': "noop",
            'nms_thresh': 0.00,
            'base': 'auto',
            'cfg': '',
            'score_thresh': 0.0,
        }

        self.predictor = None

    def demo_image(self):
        """
        Returns an image which can be run through the detector

        Returns:
            ImageContainer: an image of sea lions
        """
        from PIL import Image as PILImage
        from kwiver.vital.util import VitalPIL
        from kwiver.vital.types import ImageContainer
        url = 'https://data.kitware.com/api/v1/file/6011a5ae2fa25629b919fe6c/download'
        image_fpath = ub.grabdata(
            url, fname='sealion2010.jpg', appname='viame',
            hash_prefix='f016550faa2c96ef4fdca', hasher='sha512')
        pil_img = PILImage.open(image_fpath)
        image_data = ImageContainer(VitalPIL.from_pil(pil_img))
        return image_data

    def get_configuration(self):
        # Inherit from the base class
        cfg = super(ImageObjectDetector, self).get_configuration()
        for key, value in self._kwiver_config.items():
            cfg.set_value(key, str(value))
        return cfg

    def set_configuration(self, cfg_in):
        cfg = self.get_configuration()

        # HACK: merge config doesn't support dictionary input
        _vital_config_update(cfg, cfg_in)

        for key in self._kwiver_config.keys():
            self._kwiver_config[key] = str(cfg.get_value(key))

        if os.name == 'nt':
            os.environ["KWIMAGE_DISABLE_TORCHVISION_NMS"] = "1"

        import geowatch_tpl
        detectron2 = geowatch_tpl.import_submodule('detectron2')  # NOQA

        # Hack for development: TODO: fixme
        from geowatch.tasks.detectron2 import predict as d2pred
        # import .detectron2.predict as d2pred
        config = d2pred.DetectronPredictCLI()
        config['checkpoint_fpath'] = self._kwiver_config['checkpoint_fpath']
        config['base'] = self._kwiver_config['base']
        self.predictor = d2pred.Detectron2Predictor(config)
        self.predictor.prepare_config_backend()

        return True

    def check_configuration(self, cfg):
        if not cfg.has_value("deployed"):
            print("A network deploy file must be specified!")
            return False
        return True

    def detect(self, image_data):
        import einops
        import torch
        full_rgb = image_data.asarray().astype('uint8')
        im_chw = torch.Tensor(einops.rearrange(full_rgb, 'h w c -> c h w'))

        predictor = self.predictor
        detections = predictor.predict_image(im_chw)

        # apply threshold
        flags = detections.scores >= self._kwiver_config['score_thresh']
        detections = detections.compress(flags)

        # convert to kwiver format
        output = _kwimage_to_kwiver_detections(detections)
        return output


def _vital_config_update(cfg, cfg_in):
    """
    Treat a vital Config object like a python dictionary

    Args:
        cfg (kwiver.vital.config.config.Config): config to update
        cfg_in (dict | kwiver.vital.config.config.Config): new values

    Returns:
        kwiver.vital.config.config.Config
    """
    # vital cfg.merge_config doesnt support dictionary input
    if isinstance(cfg_in, dict):
        for key, value in cfg_in.items():
            if cfg.has_value(key):
                cfg.set_value(key, str(value))
            else:
                raise KeyError('cfg has no key={}'.format(key))
    else:
        cfg.merge_config(cfg_in)
    return cfg


def _kwiver_to_kwimage_detections(detected_objects):
    """
    Convert vital detected object sets to kwimage.Detections

    Args:
        detected_objects (kwiver.vital.types.DetectedObjectSet)

    Returns:
        kwimage.Detections
    """
    import ubelt as ub
    import kwimage
    boxes = []
    scores = []
    class_idxs = []

    classes = []
    if len(detected_objects) > 0:
        obj = ub.peek(detected_objects)
        classes = obj.type.all_class_names()

    for obj in detected_objects:
        box = obj.bounding_box
        tlbr = [box.min_x(), box.min_y(), box.max_x(), box.max_y()]
        score = obj.confidence
        cname = obj.type.get_most_likely_class()
        cidx = classes.index(cname)
        boxes.append(tlbr)
        scores.append(score)
        class_idxs.append(cidx)

    dets = kwimage.Detections(
        boxes=kwimage.Boxes(np.array(boxes), 'tlbr'),
        scores=np.array(scores),
        class_idxs=np.array(class_idxs),
        classes=classes,
    )
    return dets


def _kwimage_to_kwiver_detections(detections):
    """
    Convert kwimage detections to kwiver deteted object sets

    Args:
        detected_objects (kwimage.Detections)

    Returns:
        kwiver.vital.types.DetectedObjectSet
    """
    from kwiver.vital.types.types import ImageContainer, Image

    segmentations = None
    # convert segmentation masks
    if 'segmentations' in detections.data:
        segmentations = detections.data['segmentations']

    boxes = detections.boxes.to_tlbr()
    scores = detections.scores
    class_idxs = detections.class_idxs

    if not segmentations:
        # Placeholders
        segmentations = (None,) * len(boxes)

    # convert to kwiver format, apply threshold
    detected_objects = DetectedObjectSet()

    for tlbr, score, cidx, seg in zip(boxes.data, scores, class_idxs, segmentations):
        class_name = detections.classes[cidx]

        bbox_int = np.round(tlbr).astype(np.int32)
        bounding_box = BoundingBox(
            bbox_int[0], bbox_int[1], bbox_int[2], bbox_int[3])

        detected_object_type = DetectedObjectType(class_name, score)
        detected_object = DetectedObject(
            bounding_box, score, detected_object_type)
        if seg:
            mask = seg.to_relative_mask().numpy().data
            detected_object.mask = ImageContainer(Image(mask))

        detected_objects.add(detected_object)
    return detected_objects


def __vital_algorithm_register__():
    from kwiver.vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "detector_detectron2"

    if algorithm_factory.has_algorithm_impl_name(Detectron2Detector.static_type_name(), implementation_name):
        return

    algorithm_factory.add_algorithm(implementation_name, "Detectron2 detection routine", Detectron2Detector)

    algorithm_factory.mark_algorithm_as_loaded(implementation_name)
