# ckwg +29
# Copyright 2024 by Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#  this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
#  * Neither name of Kitware, Inc. nor the names of any contributors may be used
#  to endorse or promote products derived from this software without specific
#  prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from kwiver.vital.algo import RefineDetections
from kwiver.vital.types import DetectedObjectSet
from kwiver.vital.types import DetectedObjectType
from kwiver.vital.util import VitalPIL
from kwiver.vital.types import ImageContainer
from kwiver.vital.types import DetectedObject
from PIL import Image as PILImage
import numpy as np
import math


class Sam2Refiner(RefineDetections):
    """
    Full-Frame Classifier around Detection Sets

    CommandLine:
        xdoctest -m plugins/pytorch/sam2_refiner.py Sam2Refiner

    Example:
        >>> import torch
        >>> import kwimage
        >>> import ubelt as ub
        >>> print(torch.cuda.is_available())
        >>> sam2_checkpoint = ub.grabdata(
        >>>     'https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt',
        >>>     hash_prefix='0c4f89b91f1f951b95246f9544'
        >>> )
        >>> cfg_in = dict(
        >>>     sam2_checkpoint=sam2_checkpoint,
        >>>     sam2_cfg="configs/sam2.1/sam2.1_hiera_b+.yaml",  # needs to be relative to the modpath. Yuck.
        >>>     hole_policy="remove",
        >>>     multipolygon_policy='largest',
        >>>     #multipolygon_policy='convex_hull',
        >>>     #multipolygon_policy='allow',
        >>> )
        >>> # Create the refiner and init SAM2
        >>> self = Sam2Refiner()
        >>> self.set_configuration(cfg_in)
        >>> # Generate demo data to refine
        >>> import kwcoco
        >>> dset = kwcoco.CocoDataset.demo()
        >>> image_id = 1
        >>> coco_image = dset.coco_image(image_id)
        >>> dets = coco_image.annots()[0:2].detections
        >>> imdata = coco_image.imdelay().finalize()
        >>> # Convert raw data structures to vital
        >>> image_data = vital_image_container_from_ndarray(imdata)
        >>> detections = kwimage_detections_to_vital(dets)
        >>> #
        >>> output = self.refine(image_data, detections)
        >>> # xdoctest: +REQUIRES(--show)
        >>> import kwplot
        >>> kwplot.autompl()
        >>> refined_dets = vital_detections_to_kwimage(output)
        >>> canvas1 = dets.draw_on(imdata.copy())
        >>> canvas2 = refined_dets.draw_on(imdata.copy())
        >>> canvas1 = kwimage.draw_header_text(canvas1, 'Input Image / Detections')
        >>> canvas2 = kwimage.draw_header_text(canvas2, 'Refined Detections')
        >>> canvas = kwimage.stack_images([canvas1, canvas2], axis=1, pad=10)
        >>> kwplot.imshow(canvas)
        >>> kwplot.show_if_requested()
        >>> kwimage.imwrite('sam2_refined.jpg', canvas)  # For debugging

    Ignore:
        docker container cp amazing_boyd:/home/sam2_refined.jpg sam2_refined.jpg && eog sam2_refined.jpg
    """

    def __init__(self):
        RefineDetections.__init__(self)

        # kwiver configuration variables
        self._kwiver_config = {
            'sam2_cfg': "configs/sam2.1/sam2.1_hiera_b+.yaml",
            'sam2_checkpoint': 'https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt',
            'device': "cuda",

            'hole_policy': 'allow',  # can be allow or discard
            'multipolygon_policy': 'allow',  # can be allow, convex_hull, or largest
        }

        # netharn variables
        self._thresh = None
        self.predictor = None

    def get_configuration(self):
        # Inherit from the base class
        cfg = super(RefineDetections, self).get_configuration()
        for key, value in self._kwiver_config.items():
            cfg.set_value(key, str(value))
        return cfg

    def set_configuration(self, cfg_in):
        cfg = self.get_configuration()
        _vital_config_update(cfg, cfg_in)

        for key in self._kwiver_config.keys():
            self._kwiver_config[key] = str(cfg.get_value(key))

        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor
        hydra_overrides_extra = [
            # "++model.fill_hole_area=8",
        ]
        model = build_sam2(
            config_file=self._kwiver_config['sam2_cfg'],
            ckpt_path=self._kwiver_config['sam2_checkpoint'],
            device=self._kwiver_config['device'],
            mode='eval',
            hydra_overrides_extra=hydra_overrides_extra,
            apply_postprocessing=True,
        )
        self.predictor = SAM2ImagePredictor(model)
        return True

    def check_configuration(self, cfg):
        if not cfg.has_value("sam2_cfg"):
            print("Requires a path to a config file (relative to the repo")
        if not cfg.has_value("sam2_checkpoint"):
            print("A checkpoint path to the weights needs to be specified!")
            return False
        return True

    def refine(self, image_data, detections) -> DetectedObjectSet:
        """
        Args:
            image_data (ImageContainer): image data corresponding to detections
            detections (DetectedObjectSet): input detections

        Returns:
            DetectedObjectSet: refined detections
        """
        import torch
        import kwimage
        import numpy as np
        from shapely.geometry import Polygon
        from shapely.geometry import MultiPolygon

        if len(detections) == 0:
            return DetectedObjectSet()

        imdata = image_data.asarray().astype('uint8')
        predictor = self.predictor

        if predictor.device.type == 'cuda':
            autocast_context = torch.autocast(predictor.device.type, dtype=torch.bfloat16)
        else:
            import contextlib
            autocast_context = contextlib.nullcontext()

        # Convert input vital types into kwimage
        kw_dets: kwimage.Detections = vital_detections_to_kwimage(detections)

        # TODO: can use more than boxes as prompts
        prompts = {}
        prompts['box'] = kw_dets.boxes.toformat('xyxy').data
        prompts['multimask_output'] = False

        with torch.inference_mode(), autocast_context:
            predictor.set_image(imdata)
            masks, scores, lowres_masks = predictor.predict(**prompts)
            masks = masks.astype(np.uint8)

        FIX_SQUEEZE_ISSUE = True
        if FIX_SQUEEZE_ISSUE:
            # Dont squeeze singleton dimensions, it breaks loop logic :'(
            if len(masks.shape) == 3:
                masks = masks[None, :, :, :]

        hole_policy = self._kwiver_config['hole_policy']
        mpoly_policy = self._kwiver_config['multipolygon_policy']

        # TODO: we may like to make these configrable
        # Area requires rasterio
        # pixels_are = 'areas'
        # origin_convention = 'corner'

        pixels_are = 'points'
        origin_convention = 'center'

        needs_polygon_postprocess = not (
            (hole_policy == 'allow') and
            (mpoly_policy == 'allow')
        )
        print(f'hole_policy={hole_policy}')
        print(f'mpoly_policy={mpoly_policy}')

        # Insert modified detections into a new DetectedObjectSet
        output = DetectedObjectSet()
        for vital_det, binmask in zip(detections, masks[:, 0, :, :]):

            # Extract the new mask info relative to the vital box
            box = vital_box_to_kwiamge(vital_det.bounding_box)
            sl = box.quantize().to_slice()
            relative_submask: np.ndarray = binmask[sl]
            submask_dims: tuple = relative_submask.shape[0:2]

            if needs_polygon_postprocess:
                # Depending on the configuration we convert the mask to a
                # multipolygon postprocess it, and then convert back.
                kw_mask = kwimage.Mask.coerce(relative_submask)
                kw_mpoly = kw_mask.to_multi_polygon(
                    pixels_are=pixels_are,
                    origin_convention=origin_convention,
                )
                # print(f'kw_mpoly.data={kw_mpoly.data}')
                # print(f'kw_mpoly={kw_mpoly}')
                # kw_mpoly = kw_mpoly.fix()

                try:
                    shape = kw_mpoly.to_shapely()
                except ValueError:
                    # Workaround issue that can happen with not enough
                    # coordinates for a linearring
                    new_parts = []
                    for kw_poly in kw_mpoly.data:
                        try:
                            new_part = kw_poly.to_shapely()
                        except ValueError:
                            ...
                        else:
                            new_parts.append(new_part)
                    shape = MultiPolygon(new_parts)

                assert shape.type == 'MultiPolygon'
                if len(shape.geoms) > 1:
                    if mpoly_policy == 'convex_hull':
                        shape = shape.convex_hull
                    elif mpoly_policy == 'largest':
                        shape = max(shape.geoms, key=lambda p: p.area)
                    elif mpoly_policy == 'allow':
                        ...
                    else:
                        raise KeyError(mpoly_policy)
                    if shape.type == 'Polygon':
                        shape = MultiPolygon([shape])

                assert shape.type == 'MultiPolygon'
                if hole_policy == 'remove':
                    shape = MultiPolygon([Polygon(p.exterior) for p in shape.geoms])
                elif hole_policy == 'allow':
                    ...
                else:
                    raise KeyError(hole_policy)

                # Convert the polygon back to a mask
                new_mpoly = kwimage.MultiPolygon.from_shapely(shape)
                # import ubelt as ub
                # print(f'new_mpoly = {ub.urepr(new_mpoly, nl=1)}')
                new_mask = new_mpoly.to_mask(
                    dims=submask_dims,
                    pixels_are=pixels_are,
                    origin_convention=origin_convention,
                )
                relative_submask = new_mask.data

            new_vital_mask = vital_image_container_from_ndarray(relative_submask)
            # Create a new detected object (should we modify inplace?)
            new_det = DetectedObject(
                bbox=vital_det.bounding_box,
                classifications=vital_det.type,
                mask=new_vital_mask,
            )
            output.add(new_det)

        return output


def _vital_config_update(cfg, cfg_in):
    """
    Treat a vital Config object like a python dictionary

    Args:
        cfg (kwiver.vital.config.config.Config): config to update
        cfg_in (dict | kwiver.vital.config.config.Config): new values
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


def kwimage_boxes_to_vital(boxes):
    """
    Converts kwimage box data structures to vital.

    Args:
        boxes (kwimage.Boxes): input kwimage boxes

    Returns:
        List[BoundingBoxI | BoundingBoxF | BoundingBoxD]:
            The vital bbox objects

    Example:
        >>> # xdoctest: +REQUIRES(module:kwiver.vital)
        >>> boxes = kwimage.Boxes.random(10)
        >>> kwimage_boxes_to_vital(boxes.scale(100).astype(np.int8))
        >>> kwimage_boxes_to_vital(boxes.scale(100).astype(np.int32))
        >>> kwimage_boxes_to_vital(boxes.scale(100).astype(np.int64))
        >>> kwimage_boxes_to_vital(boxes.scale(100).astype(np.float32))
        >>> kwimage_boxes_to_vital(boxes.scale(100).astype(np.float64))
        >>> kwimage_boxes_to_vital(boxes.scale(100).astype(float))
        >>> kwimage_boxes_to_vital(boxes.scale(100).astype(int))
    """
    from kwiver.vital.types import BoundingBoxI
    # from kwiver.vital.types import BoundingBoxF
    from kwiver.vital.types import BoundingBoxD

    # Determine which bbox type is needed
    if boxes.data.dtype.kind == 'f':
        # not sure if using BoundingBoxF makes sense or works with other classes
        # if boxes.data.dtype.itemsize == 4:
        #     box_cls = BoundingBoxF
        # elif boxes.data.dtype.itemsize == 8:
        box_cls = BoundingBoxD
        # else:
        #     raise TypeError(boxes.data.dtype)
    elif boxes.data.dtype.kind == 'i':
        box_cls = BoundingBoxI
    else:
        raise TypeError(boxes.data.dtype)

    # Convert to the bbox format vital likes and make the objects
    xyxy_data = boxes.to_ltrb().data
    vital_boxes = [
        box_cls(xmin, ymin, xmax, ymax)
        for xmin, ymin, xmax, ymax in xyxy_data]
    return vital_boxes


def kwimage_detections_to_vital(kwimage_dets):
    """
    Convert kwimage Detection data structures to vital.

    Args:
        kwimage_dets (kwimage.Detections):

    Returns:
        DetectedObjectSet: converted detections

    Example:
        >>> # xdoctest: +REQUIRES(module:kwiver.vital)
        >>> # Test with everything
        >>> dets = kwimage.Detections.random(10, segmentations=True).scale(64)
        >>> vital_dets = kwimage_detections_to_vital(dets)
        >>> # Test without segmentations
        >>> dets.data.pop('segmentations')
        >>> vital_dets = kwimage_detections_to_vital(dets)
        >>> # Test without classes
        >>> dets.meta.pop('classes')
        >>> dets.data.pop('class_idxs')
        >>> vital_dets = kwimage_detections_to_vital(dets)
        >>> # Test without scores
        >>> dets.data.pop('scores')
        >>> vital_dets = kwimage_detections_to_vital(dets)
    """

    dets = kwimage_dets

    boxes = dets.boxes  # required
    scores = dets.data.get('scores', None)
    class_idxs = dets.data.get('class_idxs', None)
    segmentations = dets.data.get('segmentations', None)
    classes = dets.meta.get('classes', None)

    if scores is None:
        scores = np.ones(len(dets))
    if class_idxs is None:
        class_idxs = [None] * len(dets)
    if segmentations is None:
        segmentations = [None] * len(dets)

    vital_boxes = kwimage_boxes_to_vital(boxes)

    vital_dets = []
    for bbox, score, class_idx, sseg in zip(vital_boxes, scores, class_idxs, segmentations):
        detobjkw = {
            'bbox': bbox,
        }
        if score is not None:
            detobjkw['confidence'] = score

        if sseg is not None:
            # Convert the segmentation to vital
            # Convert whatever type of kwimage segmenation it is into a mask
            # This might be incorrect... is there a way to determine
            # if the masks are relative to the bbox or relative to the image?
            # for float bboxes the second doesn't make much sense, but the
            # first takes much more data.
            # TODO: in kwimage to denote which space masks belong to.
            if hasattr(sseg, 'to_relative_mask'):
                # sseg is a Polygon, and has this method
                offset = [int(math.ceil(bbox.min_x())), int(math.ceil(bbox.min_y()))]
                bottom = [int(math.floor(bbox.max_x())), int(math.floor(bbox.max_y()))]
                dsize = np.array(bottom) - np.array(offset)
                dims = tuple(map(int, dsize[::-1]))
                mask = kwimage_new_to_relative_mask(sseg, offset=offset, dims=dims)
                # If mask is not relative use:
                # x1, y1, x2, y2 = sseg.to_boxes().to_ltrb().data[0]
                # image_dims = (int(math.ceil(y2)), int(math.ceil(x2)))
                # mask = sseg.to_mask(dims=image_dims)
            else:
                # sseg is probably a mask already
                # TODO: handle relativeness
                mask = sseg.data.to_c_mask()
                print('case2')
                raise NotImplementedError('implement correctly if needed')

            nd_mask = mask.to_c_mask().data
            vital_mask = vital_image_container_from_ndarray(nd_mask)
            detobjkw['mask'] = vital_mask

        if classes is not None and class_idx is not None:
            label = classes[class_idx]
            detobjkw['classifications'] = DetectedObjectType(label, score)

        obj = DetectedObject(**detobjkw)
        vital_dets.append(obj)

    vital_dets = DetectedObjectSet(vital_dets)
    return vital_dets


def kwimage_new_to_relative_mask(self, offset=None, dims=None, return_offset=False):
    """
    Returns a translated mask such the mask dimensions are minimal.

    In other words, we move the polygon all the way to the top-left and
    return a mask just big enough to fit the polygon.

    Args:
        offset (None):
            if specified, return the mask relative to this xy location.
            If unspecified, it uses the corner of the segmentation.

        dims (None):
            the h, w of the new mask, relative to the offset

    Returns:
        kwimage.Mask
    """
    x, y, w, h = self.to_boxes().quantize().to_xywh().data[0]
    if offset is None:
        offset = (x, y)

    if dims is None:
        dims = (
            x - offset[0] + w,
            x - offset[1] + h
        )
    translation = tuple(-p for p in offset)
    mask = self.translate(translation).to_mask(dims=dims)
    if return_offset:
        offset = (x, y)
        return mask, offset
    else:
        return mask


def vital_detections_to_kwimage(vital_dets):
    """
    Convert vital detection objects into kwimage

    Args:
        detections (List[kwiver.vital.types.DetectedObject] | DetectedObjectSet)

    Returns:
        kwimage.Detections

    Example:
        >>> # xdoctest: +REQUIRES(module:kwiver.vital)
        >>> kwimage_dets = kwimage.Detections.random(10, segmentations=True).scale(256)
        >>> vital_dets = kwimage_detections_to_vital(kwimage_dets)
        >>> # Do some round trips
        >>> recon_kwimage_dets1 = vital_detections_to_kwimage(vital_dets)
        >>> recon_vital_dets1 = kwimage_detections_to_vital(recon_kwimage_dets1)
        >>> recon_kwimage_dets2 = vital_detections_to_kwimage(recon_vital_dets1)
        >>> # should be the same
        >>> print([p.area for p in kwimage_dets.data['segmentations']])
        >>> print([p.to_multi_polygon().area for p in recon_kwimage_dets1.data['segmentations']])
        >>> print([p.to_multi_polygon().area for p in recon_kwimage_dets2.data['segmentations']])
        >>> for i in range(10):
        >>>     print(recon_kwimage_dets1.data['segmentations'][i].data.to_c_mask().data.sum())
        >>>     print(recon_kwimage_dets2.data['segmentations'][i].data.to_c_mask().data.sum())
    """
    import kwimage
    boxes = []
    scores = []
    masks = []
    catnames = []

    detkw = {}

    all_catnames = set()
    for obj in vital_dets:
        bbox = obj.bounding_box
        xyxy = [bbox.min_x(), bbox.min_y(), bbox.max_x(), bbox.max_y()]
        offset = xyxy[0:2]
        boxes.append(xyxy)
        scores.append(obj.confidence)
        if obj.mask is not None:
            vital_mask = obj.mask.image()
            nd_mask = vital_mask.asarray()
            if len(nd_mask.shape) == 3:
                assert nd_mask.shape[2] == 1
                nd_mask = nd_mask[:, :, 0]
            # In vital, we assume the mask is relative to the top left of the box
            # Compute the offset and "effective" shape for kwimage.
            x, y = offset
            h, w = nd_mask.shape[0:2]
            h += y
            w += x
            shape = (int(h), int(w))
            kw_mask = kwimage.Mask.from_mask(nd_mask, offset=offset, shape=shape)
        else:
            kw_mask = None

        if 0:
            # is this necessary?
            all_catnames.update(set(obj.type.all_class_names()))

        catname = obj.type.get_most_likely_class()
        all_catnames.add(catname)
        catnames.append(catname)
        # obj.type.get_most_likely_score()  # not handled
        masks.append(kw_mask)

    if len(masks):
        detkw['segmentations'] = kwimage.SegmentationList(masks)

    classes = sorted(all_catnames)
    if len(classes):
        catname_to_idx = {name: idx for idx, name in enumerate(classes)}
        class_idxs = np.array([catname_to_idx[cname] for cname in catnames])
        detkw['class_idxs'] = class_idxs
        detkw['classes'] = classes

    detkw['boxes'] = kwimage.Boxes(np.array(boxes), format='ltrb')
    detkw['scores'] = np.array(scores)

    dets = kwimage.Detections(**detkw)
    return dets


def vital_box_to_kwiamge(vital_bbox):
    import kwimage
    bbox = vital_bbox
    xyxy = [bbox.min_x(), bbox.min_y(), bbox.max_x(), bbox.max_y()]
    kw_bbox = kwimage.Box.coerce(xyxy, format='ltrb')
    return kw_bbox


def vital_image_container_from_ndarray(ndarray_img):
    """
    Args:
        ndarray_img (np.ndarray): input image as an ndarray

    Returns:
        kwiver.vital.types.ImageContainer
    """
    pil_img = PILImage.fromarray(ndarray_img)
    vital_img = ImageContainer(VitalPIL.from_pil(pil_img))
    return vital_img


def __vital_algorithm_register__():
    from kwiver.vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "sam2_refiner"

    if not algorithm_factory.has_algorithm_impl_name(
            Sam2Refiner.static_type_name(), implementation_name):
        algorithm_factory.add_algorithm(
            implementation_name, "PyTorch Netharn refiner routine",
            Sam2Refiner)

        algorithm_factory.mark_algorithm_as_loaded(implementation_name)
