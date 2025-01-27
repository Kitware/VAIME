# -*- coding: utf-8 -*-
"""
Reimplementation of matlab algorithms for fishlength detection in python.
The next step is to move them into kwiver.

TODO:
    fix hard coded paths for doctests
"""
from __future__ import division, print_function
from collections import namedtuple, OrderedDict

import cv2
import itertools as it
import numpy as np
import ubelt as ub
import logging
import warnings

from os.path import splitext
from six.moves import zip

from .ocv_stereo_utils import (imscale, ensure_grayscale, from_homog, to_homog)
from .ocv_stereo_utils import minimum_weight_assignment

logger = logging.getLogger(__name__)


OrientedBBox = namedtuple('OrientedBBox', ('center', 'extent', 'angle'))


__OPENCV_VERSION_2__ = cv2.__version__.startswith('2')
if __OPENCV_VERSION_2__:
    warnings.warn('Using an old OpenCV version. '
                  'This may cause unexpected results. '
                  'Please update to 3.x')
    import skimage  # NOQA
    import skimage.measure  # NOQA


def dict_update_subset(dict_, other):
    """
    updates items in `dict_` based on `other`. `other` is not allowed to
    specify any keys that do not already exist in `dict_`.
    """
    for k, v in other.items():
        if k not in dict_:
            raise KeyError(k)
        dict_[k] = v


class ParamInfo(object):
    def __init__(self, name, default, doc=None):
        self.name = name
        self.default = default
        self.doc = doc


class BoundingBox(ub.NiceRepr):
    def __init__(bbox, coords):
        bbox.coords = coords

    def __nice__(self):
        return 'center={}, wh={}'.format(self.center, (self.width, self.height))

    @classmethod
    def from_coords(self, xmin, ymin, xmax, ymax):
        coords = np.array([xmin, ymin, xmax, ymax])
        return BoundingBox(coords)

    @property
    def xmin(bbox):
        return bbox.coords[0]

    @property
    def ymin(bbox):
        return bbox.coords[1]

    @property
    def xmax(bbox):
        return bbox.coords[2]

    @property
    def ymax(bbox):
        return bbox.coords[3]

    @property
    def width(bbox):
        return bbox.xmax - bbox.xmin

    @property
    def height(bbox):
        return bbox.ymax - bbox.ymin

    @property
    def center(self):
        if self.coords is None:
            return None
        (xmin, ymin, xmax, ymax) = self.coords
        cx = (xmax + xmin) / 2
        cy = (ymax + ymin) / 2
        return cx, cy

    def scale(self, factor):
        """
        inplace upscaling of bounding boxes and points
        (masks are not upscaled)
        """
        self.coords = np.array(self.coords) * factor


class DetectedObject(ub.NiceRepr):
    """
    Internal object for representing a detected object.

    Notes:
        not compatible with `vital.types.DetectedObject`

    Attributes:
        bbox (BoundingBox): bounding box in original image coordinates
        mask (ndarray): segmentation mask of the object
            (up to a scale and translation)
        bbox_factor (float): upsample factor that would transform mask
            into original image coordinates (up to a translation)
        special_keypoints (Dict[str, ndarray]):
            indicates a set of named special points that could be matched

    Example:
        >>> from viame.processes.opencv.algos import *
        >>> cc_mask = np.zeros((11, 11), dtype=np.uint8)
        >>> cc_mask[3:5, 2:7] = 1
        >>> self = DetectedObject.from_connected_component(cc_mask)
        >>> print(self)
        <DetectedObject(center=(4.0, 3.5), wh=(4, 1))>
    """

    def __init__(self, bbox, mask, special_keypoints=None):
        # bbox is kept in the image coordinate frame
        self.bbox = bbox
        # mask is kept in its own coordinate frame
        self.mask = mask
        # keep track of the scale factor from mask to bbox
        self.bbox_factor = 1.0
        self._special_pts = None

    def __nice__(self):
        return self.bbox.__nice__()

    def special_keypoints(self):
        """
        Return a set of ordered keypoints to be measured.

        If the _special_pts attriute is not explicitly set, the corners of the
        oriented bounding boxes are used as a proxy.
        """
        if self._special_pts is not None:
            special_pts = self._special_pts
        else:
            # This hack returns the corners of the bounding box as proxies for
            # special keypoints (e.g. the head and tail of a fish).
            box_pts = self.box_points()
            if False:
                # Use 4 corners and center to ensure matrix math is good
                # (hard to debug when ndims == npts, so make npts >> ndims)
                special_pts = {
                    'hacked_xy0': box_pts[0],  # will be the bottom right
                    'hacked_xy1': box_pts[1],  # next clockwise point
                    'hacked_xy2': box_pts[2],  # topmost point
                    'hacked_xy3': box_pts[4],
                    'hacked_center': self.oriented_bbox().center,
                }
            else:
                # Use only the corners of the bbox
                special_pts = {
                    'hacked_xy0': box_pts[0],  # bottom-most point
                    'hacked_xy2': box_pts[2],  # top-most point
                }
        return special_pts

    def center_keypoints(self):
        """
        Return a set of ordered keypoints to be measured.

        If the _special_pts attriute is not explicitly set, the corners of the
        oriented bounding boxes are used as a proxy.
        """
        # This hack returns the corners of the bounding box as proxies for
        # special keypoints (e.g. the head and tail of a fish).
        box_pts = self.box_points()

        # Use only the corners of the bbox
        centers = [ ( box_pts[0] + box_pts[1] ) / 2 ]

        centers.append( ( box_pts[1] + box_pts[2] ) / 2 )
        centers.append( ( box_pts[2] + box_pts[3] ) / 2 )
        centers.append( ( box_pts[3] + box_pts[0] ) / 2 )

        min_x = 1000000
        max_x = -1000000

        for pt in centers:
            if pt[0] < min_x:
                min_pt = pt
                min_x = pt[0]
            if pt[0] > max_x:
                max_pt = pt
                max_x = pt[0]

        return max_pt, min_pt

    def num_pixels(self):
        """
        Returns:
            int : area of the object in number of pixels (in original image
                space)

        Example:
            >>> from viame.processes.opencv.algos import *
            >>> cc_mask = np.zeros((11, 11), dtype=np.uint8)
            >>> cc_mask[3:5, 2:7] = 1
            >>> self = DetectedObject.from_connected_component(cc_mask)
            >>> print(str(self.num_pixels()))
            10
        """
        # number of pixels in the mask
        # scale to the number that would be in the original image
        n_pixels = int((self.mask > 0).sum() * (self.bbox_factor ** 2))
        return n_pixels

    def hull(self):
        """
        Returns points on the convex hull

        Returns:
            ndarray

        Example:
            >>> from viame.processes.opencv.algos import *
            >>> cc_mask = np.zeros((11, 11), dtype=np.uint8)
            >>> cc_mask[3:5, 2:7] = 1
            >>> self = DetectedObject.from_connected_component(cc_mask)
            >>> print(self.hull().tolist())
            [[[6, 4]], [[2, 4]], [[2, 3]], [[6, 3]]]
        """
        if self.mask is None:
            hull = []
            hull = hull + [[self.bbox.xmin, self.bbox.ymin]]
            hull = hull + [[self.bbox.xmax, self.bbox.ymin]]
            hull = hull + [[self.bbox.xmax, self.bbox.ymax]]
            hull = hull + [[self.bbox.xmin, self.bbox.ymax]]
        else:
            if self.mask.ndim > 2:
                self.mask = np.squeeze(self.mask, axis=2)
            cc_y, cc_x = np.where(self.mask)
            points = np.vstack([cc_x, cc_y]).T
            # Find a minimum oriented bounding box around the points
            hull = cv2.convexHull(points)
            # move points from mask coordinates to image coordinates
            if self.bbox_factor != 1.0:
                hull = hull * self.bbox_factor
            if hull is not None:
                hull = hull + [[self.bbox.xmin, self.bbox.ymin]]
            else:
                hull = [[self.bbox.xmin, self.bbox.ymin]]
        hull = np.round(hull).astype(np.int64)
        return hull

    def oriented_bbox(self):
        """
        Fits a minimum area oriented bounding box to the mask points.

        Returns:
            OrientedBBox

        Example:
            >>> from viame.processes.opencv.algos import *
            >>> cc_mask = np.zeros((11, 11), dtype=np.uint8)
            >>> cc_mask[3:5, 2:7] = 1
            >>> self = DetectedObject.from_connected_component(cc_mask)
            >>> print(str(self.oriented_bbox()))
            OrientedBBox(center=(4.0, 3.5), extent=(1.0, 4.0), angle=-90.0)
        """
        hull = self.hull()
        oriented_bbox = OrientedBBox(*cv2.minAreaRect(hull))
        return oriented_bbox

    def box_points(self):
        r"""
        Finds oriented box corner points of `self.oriented_bbox`

        CommandLine:
            python -m viame.processes.opencv.algos DetectedObject.box_points

        Returns:
            ndarray: pts: [4x2] matrix where each item pts[i] is in x,y
                coordinates in clockwise order starting from the bottom first,
                and then the right (if more than one point are at the bottom).
                (note: if the mask is a line of pixels points will be
                 duplicated)

        Example:
            >>> from viame.processes.opencv.algos import *
            >>> _, o = 0, 1
            >>> A = B = C = D = 1
            >>> cc_mask = np.array([             # Y
            >>>     [ _, _, _, _, _, _, _, _ ],  # 0
            >>>     [ _, _, _, C, _, _, _, _ ],  # 1
            >>>     [ _, _, o, o, o, _, _, _ ],  # 2
            >>>     [ _, B, o, o, o, o, _, _ ],  # 3
            >>>     [ _, _, o, o, o, o, D, _ ],  # 4
            >>>     [ _, _, _, o, o, o, _, _ ],  # 5
            >>>     [ _, _, _, _, A, _, _, _ ],  # 6
            >>>     [ _, _, _, _, _, _, _, _ ],  # 7
            >>> ])
            >>> # X:  0  1  2  3  4  5  6  7
            >>> self = DetectedObject.from_connected_component(cc_mask)
            >>> points = self.box_points()
            >>> print(ub.repr2(points.tolist(), precision=2, nl=0))
            [[4.00, 6.00], [1.00, 3.00], [3.00, 1.00], [6.00, 4.00]]

        Example:
            >>> from viame.processes.opencv.algos import *
            >>> _, o = 0, 1
            >>> A = B = C = D = 1
            >>> cc_mask = np.array([     # Y
            >>>     [ _, _, _, _, _, ],  # 0
            >>>     [ _, C, o, D, _, ],  # 1
            >>>     [ _, o, o, o, _, ],  # 2
            >>>     [ _, B, o, A, _, ],  # 3
            >>>     [ _, _, _, _, _, ],  # 4
            >>> ])
            >>> # X:  0  1  2  3  4
            >>> self = DetectedObject.from_connected_component(cc_mask)
            >>> points = self.box_points()
            >>> print(ub.repr2(points.tolist(), precision=2, nl=0))
            [[3.00, 3.00], [1.00, 3.00], [1.00, 1.00], [3.00, 1.00]]

        Example:
            >>> from viame.processes.opencv.algos import *
            >>> _, o = 0, 1
            >>> A = B = C = D = 1
            >>> cc_mask = np.array([        # Y
            >>>     [ _, _, _, o, _, _, ],  # 0
            >>>     [ _, _, o, o, o, _, ],  # 1
            >>>     [ _, o, o, o, o, o, ],  # 2
            >>>     [ o, o, o, o, o, _, ],  # 3
            >>>     [ _, o, o, o, _, _, ],  # 4
            >>>     [ _, _, o, o, _, _, ],  # 5
            >>> ])
            >>> # X:  0  1  2  3  4  5  6
            >>> self = DetectedObject.from_connected_component(cc_mask)
            >>> points = self.box_points()
            >>> print(ub.repr2(points.tolist(), precision=2, nl=0))
            [[2.50, 5.50], [0.00, 3.00], [3.00, 0.00], [5.50, 2.50]]
        """
        if __OPENCV_VERSION_2__:
            return np.array(cv2.cv.BoxPoints(self.oriented_bbox()),
                            dtype=float)
        else:
            return cv2.boxPoints(self.oriented_bbox())

    def scale(self, factor):
        """ inplace """
        if factor != 1.0:
            self.bbox_factor *= factor
            self.bbox.scale(factor)

    @classmethod
    def from_connected_component(DetectedObject, cc_mask):
        """
        Create a DetectedObject from connected components in a mask
        """
        # note, `np.where` returns coords in (r, c)
        ys, xs = np.where(cc_mask)
        xmin, xmax = xs.min(), xs.max()
        ymin, ymax = ys.min(), ys.max()
        bbox = BoundingBox.from_coords(xmin, ymin, xmax, ymax)
        yslice = slice(bbox.ymin, bbox.ymax + 1)
        xslice = slice(bbox.xmin, bbox.xmax + 1)
        mask = cc_mask[yslice, xslice]
        self = DetectedObject(bbox, mask)
        return self


class GMMForegroundObjectDetector(object):
    """
    Uses background subtraction and 4-way connected compoments algorithm to
    detect potential fish objects. Objects are filtered by size, aspect ratio,
    and closeness to the image border to remove bad detections.

    References:
        https://stackoverflow.com/questions/37300698/gaussian-mixture-model
        http://docs.opencv.org/trunk/db/d5c/tutorial_py_bg_subtraction.html
    """

    @staticmethod
    def default_params():
        default_params = {
            'preproc': [

                ParamInfo(name='factor', default=1.0,
                          doc='image downsample factor'),

                ParamInfo(name='smooth_ksize', default=(10, 10),
                          doc=('postprocessing filter size for noise removal '
                               '(wrt orig image size)'))

            ],

            'gmm': [

                ParamInfo(name='n_startup_frames', default=3,
                          doc=('number of frames before the background model '
                               'will wait before returning any detections')),

                ParamInfo(name='n_training_frames', default=300,
                          doc='number of frames to use for training'),

                ParamInfo(name='gmm_thresh', default=30,
                          doc='GMM variance threshold'),

            ],

            'filter': DetectionShapeFilter.default_params()['filter'],
        }
        return default_params

    def __init__(detector, **kwargs):
        # setup default config
        detector.config = {}
        default_params = detector.default_params()
        for pinfos in default_params.values():
            detector.config.update({pi.name: pi.default for pi in pinfos})
        # modify based on user args
        dict_update_subset(detector.config, kwargs)

        # Setup GMM background subtraction algorithm
        logger.debug('Using GMM from cv2.__version__ = {}'.format(cv2.__version__))
        if cv2.__version__.startswith('2'):
            # not sure about these params
            detector.background_model = cv2.BackgroundSubtractorMOG2(
                history=detector.config['n_training_frames'],
                varThreshold=detector.config['gmm_thresh'],
                bShadowDetection=False
            )
        else:
            detector.background_model = cv2.createBackgroundSubtractorMOG2(
                history=detector.config['n_training_frames'],
                varThreshold=detector.config['gmm_thresh'],
                detectShadows=False)

        # Setup detection filter algorithm
        filter_config = {
            pi.name: detector.config[pi.name]
            for pi in default_params['filter']
        }
        detector.filter = DetectionShapeFilter(**filter_config)

        detector.n_iters = 0
        # masks from previous iter are kept in memory for visualization
        detector._masks = {}

    def detect(detector, img):
        """
        Main algorithm step.
        Detects the objects in the image and update the background model.

        Args:
            img (ndarray): image to perform detection on

        Returns:
            detections : List[DetectedObjects]

        CommandLine:
            python -m viame.processes.opencv.algos GMMForegroundObjectDetector.detect

        Example:
            >>> # xdoctest: +SKIP
            >>> import matplotlib as mpl
            >>> mpl.use('agg')
            >>> from viame.processes.opencv.algos import *
            >>> from viame.processes.opencv.demo import *
            >>> detector, img = demodata_detections(
            >>>     target_step='detect', target_frame_num=7)
            >>> detections = detector.detect(img)
            >>> print('detections = {!r}'.format(detections))
            >>> masks = detector._masks
            >>> # xdoctest: REQUIRES(--show)
            >>> draw_img = DrawHelper.draw_detections(img, detections, masks)
            >>> fpath = ub.ensure_app_cache_dir('opencv') + '/GMMForegroundObjectDetector.detect.png'
            >>> cv2.imwrite(fpath, draw_img)
            >>> ub.startfile(fpath)
            >>> #from matplotlib import pyplot as plt
            >>> #plt.imshow(cv2.cvtColor(draw_img, cv2.COLOR_BGR2RGB))
            >>> #plt.gca().grid(False)
            >>> #plt.show()
        """

        detector._masks = {}

        # Downsample and convert to grayscale
        img_, upfactor = detector.preprocess_image(img)

        # Run detection / update background model
        logger.debug('detect background')
        mask = detector.background_model.apply(img_)
        detector._masks['orig'] = mask.copy()

        if detector.n_iters < detector.config['n_startup_frames']:
            # Skip the first few frames while the model is learning
            detections = []
        else:
            # Remove noise
            if detector.config['smooth_ksize'] is not None:
                mask = detector.postprocess_mask(mask)
                detector._masks['post'] = mask.copy()

            # Find detections using CC algorithm
            detectgen = detector.detections_in_mask(mask)

            # Filter detections by shape and size
            img_dsize = tuple(img.shape[0:2][::-1])
            detectgen = detector.filter.filter_detections(detectgen, img_dsize)

            # return detections in a list
            detections = list(detectgen)

        detector.n_iters += 1
        logger.debug('made {} detections'.format(len(detections)))
        return detections

    def preprocess_image(detector, img):
        """
        Preprocess image before subtracting background
        """
        logger.debug('preprocess image before detect')
        # Convert to grayscale
        img_ = ensure_grayscale(img)
        # Downsample image before running detection
        factor = detector.config['factor']
        if factor != 1.0:
            downfactor_ = 1 / factor
            img_, downfactor = imscale(img, downfactor_)
            upfactor = 1 / downfactor[0]
        else:
            upfactor = 1.0
            img_ = img
        return img_, upfactor

    def postprocess_mask(detector, mask):
        """ remove noise from detection intensity masks """
        logger.debug('postprocess mask')
        ksize = np.array(detector.config['smooth_ksize'])
        ksize = tuple(np.round(ksize / detector.config['factor']).astype(np.int64))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, ksize)
        # opening is erosion followed by dilation
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, dst=mask)
        # Do a second dilation
        mask = cv2.dilate(src=mask, kernel=kernel, dst=mask)
        return mask

    def detections_in_mask(detector, mask):
        """
        Find pixel locs of each cc and determine if its a valid detection

        Args:
            mask (ndarray): mask where non-zero pixels indicate all candidate
                objects

        Yields:
            DetectedObject

        Example:
            >>> from viame.processes.opencv.algos import *
            >>> detector = GMMForegroundObjectDetector()
            >>> detector.config['min_num_pixels'] = 2
            >>> x, y = np.indices((10, 10))
            >>> s = 2
            >>> mask = (((x // s) % s == 0) & ((y // s) % s == 0)).astype(np.uint8)
            >>> mask[0, -2:] = 0
            >>> mask[1, -1] = 0
            >>> mask[2, 2] = 1
            >>> mask[-1, 2] = 1
            >>> mask[-5:-1, -3] = 1
            >>> detections = list(detector.detections_in_mask(mask))
            >>> assert len(detections) == 7
        """
        # 4-way connected component algorithm
        if __OPENCV_VERSION_2__:
            # opencv2 doesnt have a builtin CC algo, need to use skimage
            cc_mask, n_ccs_sk = skimage.measure.label(mask, neighbors=8,
                                                      background=0,
                                                      return_num=True)
            # Be consistent with opencv, which always includes the background
            # label in the num (even if no background exists).
            n_ccs = n_ccs_sk + 1
        else:
            n_ccs, cc_mask = cv2.connectedComponents(mask, connectivity=8)

        factor = detector.config['factor']

        # Process only labels with enough points
        min_num_pixels = detector.config['min_num_pixels']
        if min_num_pixels is None:
            valid_labels = np.arange(1, n_ccs + 1)
        else:
            # speed optimization: quickly determine num pixels for each cc
            # using a histogram instead of checking in the filter func
            hist, bins = np.histogram(cc_mask[cc_mask > 0].ravel(),
                                      bins=np.arange(1, n_ccs + 1))
            min_num_pixels_ = min_num_pixels / (factor ** 2)
            # only consider large enough regions
            valid_labels = bins[0:-1][hist >= min_num_pixels_]

        # Filter ccs to generate only "good" detections
        # We may be able to speed this up using ndimage.find_objects
        for cc_label in valid_labels:
            cc = (cc_mask == cc_label)
            detection = DetectedObject.from_connected_component(cc)
            # Upscale back to input img coords (to agree with camera calib)
            detection.scale(factor)
            yield detection


class DetectionShapeFilter(object):
    """
    Filters masked detections based on their size and shape
    """

    @staticmethod
    def default_params():
        default_params = {
            'filter': [

                ParamInfo(name='min_num_pixels', default=800,
                          doc=('remove detections with fewer pixels '
                               'wrt original image size')),

                ParamInfo(name='edge_trim', default=(12, 12),
                          doc=('constrains acceptable targets to the region '
                               '[padx, pady, img_w - padx, img_h - pady]. '
                               'These are wrt the original image size')),

                ParamInfo(name='aspect_thresh', default=(3.5, 7.5,),
                          doc='range of valid aspect ratios for detections')

            ]
        }
        return default_params

    def __init__(self, **kwargs):
        # setup default config
        self.config = {}
        default_params = self.default_params()
        for pinfos in default_params.values():
            self.config.update({pi.name: pi.default for pi in pinfos})
        # modify based on user args
        dict_update_subset(self.config, kwargs)

    def filter_detections(self, detections, img_dsize=None):
        logger.debug('filter detections')
        for detection in detections:
            if self.is_valid(detection, img_dsize):
                yield detection

    def is_valid(self, detection, img_dsize=None):
        """
        Checks if the detection passes filtering constraints

        Args:
            detection (DetectedObject): mask where non-zero pixels indicate a
                single candidate object
            img_dsize (tuple): w/h of the original image

        Returns:
            bool: True if the detection is valid else False
        """
        if self.config['min_num_pixels'] is not None:
            # Remove small regions
            if detection.num_pixels() < self.config['min_num_pixels']:
                return False

        if self.config['edge_trim'] is not None:
            # Define thresholds to filter edges
            img_width, img_height = img_dsize
            xmin_lim, ymin_lim = self.config['edge_trim']
            xmax_lim = img_width - (xmin_lim)
            ymax_lim = img_height - (ymin_lim)

            # Filter objects detected on the edge of the image region
            (xmin, ymin, xmax, ymax) = detection.bbox.coords
            if any([xmin < xmin_lim, xmax > xmax_lim,
                    ymin < ymin_lim, ymax > ymax_lim]):
                return None

        # Find a minimum oriented bounding box around the points
        w, h = detection.oriented_bbox().extent
        if w == 0 or h == 0:
            # assert w == 0 or h == 0, 'detection has no width or height'
            return False

        # Filter objects without fishy aspect ratios
        ar = max([(w / h), (h / w)])
        min_aspect, max_aspect = self.config['aspect_thresh']
        if any([ar < min_aspect, ar > max_aspect]):
            return False
        return True


class StereoLengthMeasurments(object):
    """
    Algo for matching detections in left and right camera and determining the
    fish length in millimeters.
    """

    @staticmethod
    def default_params():
        default_params = {
            'thresholds': [
                ParamInfo('max_err', (6, 14), doc=(
                    'Threshold for errors between before & after projected '
                    'points to make matches between left and right')),

                ParamInfo('small_len', 150, doc=(
                    'length (in millimeters) to switch between high and low '
                    'max error thresholds ')),
            ]
        }
        return default_params

    def __init__(self, **kwargs):
        # setup default config
        self.config = {}
        default_params = self.default_params()
        for pinfos in default_params.values():
            self.config.update({pi.name: pi.default for pi in pinfos})
        # modify based on user args
        dict_update_subset(self.config, kwargs)

    def find_matches(self, cal, detections1, detections2):
        """
        Match detections from the left camera to detections in the right camera

        Args:
            cal (StereoCalibration):
            detections1 (List[DetectedObject]):
            detections2 (List[DetectedObject]):

        Returns:
            Tuple: assignment, assign_data, cand_errors

        Example:
            >>> # Rows are detections in img1, cols are detections in img2
            >>> from viame.processes.opencv.algos import *
            >>> from viame.processes.opencv.demo import *
            >>> cal, detections1, detections2 = demodata_detections2()
            >>> self = StereoLengthMeasurments()
            >>> _tup  = self.find_matches(cal, detections1, detections2)
            >>> assignment, assign_data, cand_errors = _tup
        """
        logger.debug('find matches')
        n_detect1, n_detect2 = len(detections1), len(detections2)
        cand_data = {}

        # Initialize matrix of reprojection errors
        cost_errors = np.full((n_detect1, n_detect2), fill_value=np.inf)
        cand_errors = np.full((n_detect1, n_detect2), fill_value=np.inf)

        # Find the liklihood that each pair of detections matches by
        # triangulating and then measuring the reprojection error.
        for (i, det1), (j, det2) in it.product(enumerate(detections1),
                                               enumerate(detections2)):
            # Triangulate assuming det1 and det2 match, but return the
            # reprojection error so we can check if this assumption holds
            pts1 = det1.special_keypoints()
            pts2 = det2.special_keypoints()

            if len(pts1) != 2:
                raise NotImplementedError('cant handle > 2 points yet')
            elif len(pts2) != 2:
                raise NotImplementedError('cant handle > 2 points yet')
            else:
                fishlen_key = tuple(sorted(pts2.keys()))
                key_pairs = [fishlen_key]

            _tup = self.triangulate(cal, pts1, pts2, key_pairs=key_pairs)
            keys, pts1_3d, pts2_3d, errors, lengths = _tup
            error = errors.mean()

            fishlen = lengths[fishlen_key]

            # Mark the pair (i, j) as a potential candidate match
            cand_errors[i, j] = error

            # Record information about this candidate match
            cand_data[(i, j)] = {
                'world_pts': pts1_3d,
                'error': error,
                'fishlen': fishlen,
                'range': pts1_3d.T[2].mean(),
                'dz': np.abs(np.diff(pts1_3d.T[2]))[0],
                'box_pts1': det1.box_points(),
                'box_pts2': det2.box_points(),
            }

            # Check chirality
            # Both Z-coordinates must be positive (i.e. in front the cameras)
            z_coords1 = pts1_3d.T[2]
            z_coords2 = pts2_3d.T[2]
            both_in_front = np.all(z_coords1 > 0) and np.all(z_coords2 > 0)
            if not both_in_front:
                # Ignore out-of-view correspondences
                continue

            # Check if reprojection error is too high
            max_error = self.config['max_err']
            small_len = self.config['small_len']  # hardcoded to 15cm in matlab
            if len(max_error) == 2:
                error_thresh = max_error[0] if fishlen <= small_len else max_error[1]
            else:
                error_thresh = max_error[0]

            if error  >= error_thresh:
                # Ignore correspondences with high reprojection error
                continue

            cost_errors[i, j] = error

        # Find the matching with minimum reprojection error, such that each
        # detection in one camera can match at most one detection in the other.
        # Finds optimal assignment of left-camera to right-camera detections
        assignment = minimum_weight_assignment(cost_errors)

        # get associated data with each assignment
        assign_data = []
        for i, j in assignment:
            data = {'ij': (i, j)}
            data.update(cand_data[(i, j)])
            assign_data.append(data)
        return assignment, assign_data, cand_errors

    def triangulate(self, cal, pts1, pts2, key_pairs=None):
        """
        Assuming, points in pts1 match pts2, we determine 3d-coordinates of
        each detection and measure the reprojection error. Measure the lengths
        between specified keys.

        Args:
            pts1 (Dict[str, ndarray[2]]): named x,y keypoints
            pts2 (Dict[str, ndarray[2]]): named x,y keypoints
            key_pairs (List[Tuple[str, str]]):
                unordered pairs of named keypoints to measure the length
                between. Errors if not specified unless the points only contain
                two points.

        Returns:
            Tuple:
                keys (List[str]): common special keys between pts1 and pts2
                pts1_3d (ndarray): pts1 in world coords (order corresponds to keys)
                pts2_3d (ndarray): pts2 in world coords (order corresponds to keys)
                errors (ndarray): reprojection error between world points
                lengths (Dict[Tuple[str, str], float]): measured length between
                    specified key pairs.

        References:
            http://answers.opencv.org/question/117141
            https://gist.github.com/royshil/7087bc2560c581d443bc
            https://stackoverflow.com/a/29820184/887074

        Example:
            >>> # Rows are detections in img1, cols are detections in img2
            >>> from viame.processes.opencv.algos import *
            >>> from viame.processes.opencv.demo import *
            >>> cal = demodata_calibration()
            >>> pts1 = {'head': [0, 0], 'tail': [1, 1]}
            >>> pts2 = {'head': [1, 0], 'tail': [2, 1]}
            >>> key_pairs = [('head', 'tail')]
            >>> self = StereoLengthMeasurments()
            >>> _tup = self.triangulate(cal, pts1, pts2, key_pairs)
            >>> keys, pts1_3d, pts2_3d, errors, lengths = _tup
            >>> print('lengths = ' + ub.repr2(lengths, nl=1, sk=1, precision=2))
            lengths = {
                ('head', 'tail'): 13.23,
            }
        """
        logger.debug('triangulate')

        keys = sorted(set(pts1.keys()) & set(pts2.keys()))
        key_to_index = {k: i for i, k in enumerate(keys)}
        if len(keys) < 2:
            raise ValueError('Must have at least 2 corresponding points')

        if key_pairs is None:
            if len(keys) == 2:
                key_pairs = [keys]
            else:
                raise ValueError(
                    'Must specify key_pairs when using more than two points')

        # Move into opencv point format (num x 1 x dim)
        pts1_cv = np.array([pts1[k] for k in keys]).reshape(-1, 1, 2)
        pts2_cv = np.array([pts2[k] for k in keys]).reshape(-1, 1, 2)
        pts1_cv = pts1_cv.astype(float)
        pts2_cv = pts2_cv.astype(float)

        # Grab camera parameters
        K1, K2 = cal.intrinsic_matrices()
        kc1, kc2 = cal.distortions()
        rvec1, tvec1, rvec2, tvec2 = cal.extrinsic_vecs()

        # Make extrinsic matrices
        R1 = cv2.Rodrigues(rvec1)[0]
        R2 = cv2.Rodrigues(rvec2)[0]
        T1 = tvec1[:, None]
        T2 = tvec2[:, None]
        RT1 = np.hstack([R1, T1])
        RT2 = np.hstack([R2, T2])

        # Undistort points
        # This puts points in "normalized camera coordinates" making them
        # independent of the intrinsic parameters. Moving to world coordinates
        # can now be done using only the RT transform.
        unpts1_cv = cv2.undistortPoints(pts1_cv, K1, distCoeffs=kc1)
        unpts2_cv = cv2.undistortPoints(pts2_cv, K2, distCoeffs=kc2)

        # note: trinagulatePoints docs say that it wants a 3x4 projection
        # matrix (ie K.dot(RT)), but we only need to use the RT extrinsic
        # matrix because the undistorted points already account for the K
        # intrinsic matrix.
        world_pts_homog = cv2.triangulatePoints(RT1, RT2, unpts1_cv, unpts2_cv)
        world_pts = from_homog(world_pts_homog)

        # Compute distance between key pairs of 3D bounding box points
        lengths = OrderedDict()
        for key1, key2 in key_pairs:
            corner1 = world_pts.T[key_to_index[key1]]
            corner2 = world_pts.T[key_to_index[key2]]
            # Length is in millimeters
            lengths[(key1, key2)] = np.linalg.norm(corner1 - corner2)

        # Reproject points
        world_pts_cv = world_pts.T[:, None, :]
        proj_pts1_cv = cv2.projectPoints(world_pts_cv, rvec1, tvec1, K1, kc1)[0]
        proj_pts2_cv = cv2.projectPoints(world_pts_cv, rvec2, tvec2, K2, kc2)[0]

        # Check error
        err1 = ((proj_pts1_cv - pts1_cv)[:, 0, :] ** 2).sum(axis=1)
        err2 = ((proj_pts2_cv - pts2_cv)[:, 0, :] ** 2).sum(axis=1)
        errors = np.hstack([err1, err2])

        # Get 3d points in each camera's reference frame
        # Note RT1 is the identity and RT are 3x4, so no need for `from_homog`
        # Return points in with shape (N,3)
        pts1_3d = RT1.dot(to_homog(world_pts)).T
        pts2_3d = RT2.dot(to_homog(world_pts)).T
        return keys, pts1_3d, pts2_3d, errors, lengths


class StereoCalibration(object):
    """
    Helper class for reading / accessing stereo camera calibration params

    """
    def __init__(cal, data=None):
        cal.data = data
        cal.unit = 'millimeters'

    def __str__(cal):
        return '{}({})'.format(cal.__class__.__name__, cal.data)

    def extrinsic_vecs(cal):
        rvec1 = cal.data['left']['extrinsic']['om']
        tvec1 = cal.data['right']['extrinsic']['om']

        rvec2 = cal.data['right']['extrinsic']['om']
        tvec2 = cal.data['right']['extrinsic']['T']
        return rvec1, tvec1, rvec2, tvec2

    def distortions(cal):
        kc1 = cal.data['right']['intrinsic']['kc']
        kc2 = cal.data['left']['intrinsic']['kc']
        return kc1, kc2

    def intrinsic_matrices(cal):
        K1 = cal._make_intrinsic_matrix(cal.data['left']['intrinsic'])
        K2 = cal._make_intrinsic_matrix(cal.data['right']['intrinsic'])
        return K1, K2

    @staticmethod
    def _make_intrinsic_matrix(intrin):
        """ convert intrinsic dict to matrix """
        fc = intrin['fc']
        cc = intrin['cc']
        alpha_c = intrin['alpha_c']
        KK = np.array([
            [fc[0], alpha_c * fc[0], cc[0]],
            [    0,           fc[1], cc[1]],
            [    0,               0,     1],
        ])
        return KK

    @staticmethod
    def _make_intrinsic_params(K):
        """ convert intrinsic matrix to dict """
        intrin = {}
        fc = intrin['fc'] = np.zeros(2)
        cc = intrin['cc'] = np.zeros(2)
        [[fc[0], alpha_c_fc0, cc[0]],
         [    _,       fc[1], cc[1]],
         [    _,           _,     _]] = K
        intrin['alpha_c'] = np.array([alpha_c_fc0 / fc[0]])
        return intrin

    @classmethod
    def from_file(StereoCalibration, cal_fpath):
        """
        Loads a camera calebration from a .mat or .npz file

        SeeAlso:
            from_npzfile
            from_matfile

        Example:
            >>> # xdoctest: +SKIP
            >>> from viame.processes.opencv.algos import *
            >>> cal_fpath = ub.expandpath('~/data/opencv_stereo_sample_data/201608_calibration_data/selected/Camtrawl_2016.npz')
            >>> cal = StereoCalibration.from_file(cal_fpath)
        """
        ext = splitext(cal_fpath)[1].lower()
        if ext == '.mat':
            return StereoCalibration.from_matfile(cal_fpath)
        elif ext == '.npz':
            return StereoCalibration.from_npzfile(cal_fpath)
        else:
            raise ValueError('unknown extension {}'.format(ext))

    @classmethod
    def from_npzfile(StereoCalibration, cal_fpath):
        """
        For the npz file the root object should be a dict with the following
        keys and values:
            R: extrinsic rotation matrix
            T: extrinsic translation
            cameraMatrixL: dict of intrinsict parameters for the left camera
                fc: focal length
                cc: principle point
                alpha_c: skew
            cameraMatrixR: dict of intrinsict parameters for the right camera
                fc: focal length
                cc: principle point
                alpha_c: skew
            distCoeffsL: distortion coefficients for the left camera
            distCoeffsR: distortion coefficients for the right camera
        """
        logger.debug('Loading npzfile {}'.format(cal_fpath))
        data = dict(np.load(cal_fpath))
        flat_dict = {}
        flat_dict['om'] = cv2.Rodrigues(data['R'])[0].ravel()
        flat_dict['T'] = data['T'].ravel()

        K1 = data['cameraMatrixL']
        intrin1 = StereoCalibration._make_intrinsic_params(K1)
        flat_dict['fc_left'] = intrin1['fc']
        flat_dict['cc_left'] = intrin1['cc']
        flat_dict['alpha_c_left'] = intrin1['alpha_c']
        flat_dict['kc_left'] = data['distCoeffsL'].ravel()

        K2 = data['cameraMatrixR']
        intrin2 = StereoCalibration._make_intrinsic_params(K2)
        flat_dict['fc_right'] = intrin2['fc']
        flat_dict['cc_right'] = intrin2['cc']
        flat_dict['alpha_c_right'] = intrin2['alpha_c']
        flat_dict['kc_right'] = data['distCoeffsR'].ravel()
        return StereoCalibration._from_flat_dict(flat_dict)

    def from_cameras(StereoCalibration, camera1, camera2):
        pass

    @classmethod
    def from_matfile(StereoCalibration, cal_fpath):
        """
        Loads a matlab camera calibration file from disk

        For the mat file, the root structure should be a dict with the key
        `Cal` whose value is a dict with the following items:
            om: extrinsic rotation vector (note rotation matrix is rodrigues(om))
            T: extrinsic translation
            fc_left: focal length of the left camera
            cc_left: principle point
            alpha_c_left: skew
            kc_left: distortion coefficients for the left camera
            fc_right: focal length of the right camera
            cc_right: principle point
            alpha_c_right: skew
            kc_right: distortion coefficients for the right camera

        References:
            http://www.vision.caltech.edu/bouguetj/calib_doc/htmls/parameters.html
            http://www.vision.caltech.edu/bouguetj/calib_doc/htmls/example5.html

        Example:
            >>> # xdoctest: +SKIP
            >>> from viame.processes.opencv.algos import *
            >>> from viame.processes.opencv.demo import *
            >>> cal_fpath = ub.expandpath('~/data/autoprocess_test_set/cal_201608.mat')
            >>> cal = StereoCalibration.from_matfile(cal_fpath)
            >>> print('cal = {}'.format(cal))
        """
        import scipy.io
        logger.debug('Loading matfile {}'.format(cal_fpath))
        cal_data = scipy.io.loadmat(cal_fpath)
        keys = ['om', 'T', 'fc_left', 'fc_right', 'cc_left', 'cc_right',
                'kc_left', 'kc_right', 'alpha_c_left', 'alpha_c_right']

        if isinstance(cal_data, dict) and 'Cal' in cal_data:
            vals = cal_data['Cal'][0][0]
            flat_dict = {k: v.ravel() for k, v in zip(keys, vals)}
        else:
            flat_dict = {key: cal_data[key].ravel() for key in keys}
        return StereoCalibration._from_flat_dict(flat_dict)

    @classmethod
    def _from_flat_dict(StereoCalibration, flat_dict):
        """ helper used by matlab and numpy readers """
        data = {
            'left': {
                'extrinsic': {
                    # Center wold on the left camera
                    'om': np.zeros(3),  # rotation vector
                    'T': np.zeros(3),  # translation vector
                },
                'intrinsic': {
                    'fc': flat_dict['fc_left'],  # focal point
                    'cc': flat_dict['cc_left'],  # principle point
                    'alpha_c': flat_dict['alpha_c_left'][0],  # skew
                    'kc': flat_dict['kc_left'],  # distortion
                }
            },

            'right': {
                'extrinsic': {
                    'om': flat_dict['om'],  # rotation vector
                    'T': flat_dict['T'],  # translation vector
                },
                'intrinsic': {
                    'fc': flat_dict['fc_right'],  # focal point
                    'cc': flat_dict['cc_right'],  # principle point
                    'alpha_c': flat_dict['alpha_c_right'][0],  # skew
                    'kc': flat_dict['kc_right'],  # distortion
                }
            },
        }
        # Cast to appropriate types
        for cam in [data['left'], data['right']]:
            in_mat = cam['intrinsic']
            ex_mat = cam['extrinsic']
            ex_mat['om'] = np.array(ex_mat['om'], dtype=float)
            ex_mat['T'] = np.array(ex_mat['T'], dtype=float)
            in_mat['fc'] = np.array(in_mat['fc'], dtype=float)
            in_mat['cc'] = np.array(in_mat['cc'], dtype=float)
            in_mat['kc'] = np.array(in_mat['kc'], dtype=float)

        cal = StereoCalibration()
        cal.data = data
        return cal


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m viame.processes.opencv.algos

        xdoctest ~/code/VIAME/plugins/opencv/python/viame/processes/opencv/algos.py

    Ignore:
        workon_py2
        source ~/code/VIAME/build/install/setup_viame.sh
        export SPROKIT_PYTHON_MODULES=opencv_processes:kwiver.processes:viame.processes
        export PYTHONPATH=$(pwd):$PYTHONPATH
        python ~/code/VIAME/plugins/opencv/python/opencv_demo.py
        ffmpeg -y -f image2 -i out_haul83/%*.png -vcodec mpeg4 -vf "setpts=10*PTS" haul83-results.avi
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
