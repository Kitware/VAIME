"""
Copied from: ~/code/geowatch/geowatch/tasks/detectron2/predict.py
"""
#!/usr/bin/env python3
import os
import scriptconfig as scfg
import ubelt as ub


class DetectronPredictCLI(scfg.DataConfig):
    # TODO: scriptconfig Value classes should have tags for mlops pipelines
    # Something like tags ⊆ {in_path,out_path, algo_param, perf_param, primary, primary_in_path, primary_out_path}
    checkpoint_fpath = scfg.Value(None, help='path to the weights')
    model_fpath = scfg.Value(None, help='path to a model file: todo: bundle with weights')

    src_fpath = scfg.Value(None, help='input kwcoco file')
    dst_fpath = scfg.Value(None, help='output kwcoco file')
    write_heatmap = scfg.Value(False, help='if True, also write masks as heatmaps')
    nms_thresh = scfg.Value(0.0, help='nonmax supression threshold')
    workers = 4
    device = scfg.Value('cuda:0', help='device to predict on')

    base = scfg.Value('auto', help=ub.paragraph(
        '''
        Specify the detectron config that corresponds to the model.
        If "auto" attempts to introspect from the checkpoint fpath, which is
        currently only possible if the model was written as a sidecar file.

        Could be something like:
            * COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml
            * COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml
            * new_baselines/mask_rcnn_regnety_4gf_dds_FPN_400ep_LSJ.py
        '''))

    cfg = scfg.Value(ub.codeblock(
        '''
        '''),
        help=ub.paragraph(
            '''
            Overlaid config on top of whatever base config path is specified.
            Typically this is not needed at test time, but it provided just in
            case.
            '''))

    @classmethod
    def main(cls, cmdline=1, **kwargs):
        """
        Example:
            >>> # xdoctest: +SKIP
            >>> cmdline = 0
            >>> kwargs = dict()
            >>> cls = DetectronPredictCLI
            >>> cls.main(cmdline=cmdline, **kwargs)
        """
        import rich
        from rich.markup import escape
        config = cls.cli(cmdline=cmdline, data=kwargs, strict=True)
        rich.print('config = ' + escape(ub.urepr(config, nl=1)))
        detectron_predict(config)

__cli__ = DetectronPredictCLI


class OldStyleConfigBackend:
    """
    Handle configuration for old-style detectron2 configs
    """
    def __init__(backend, cfg, config):
        backend.cfg = cfg
        backend.config = config
        backend.oldstyle_predictor = None
        backend.model = None

    def load_model(backend):
        # NEED to call detectron2 more efficiently
        from detectron2.engine import DefaultPredictor
        backend.oldstyle_predictor = DefaultPredictor(backend.cfg)
        backend.model = backend.oldstyle_predictor.model

    def preprocess(backend, im_hwc):
        image = backend.oldstyle_predictor.aug.get_transform(im_hwc).apply_image(im_hwc)
        return image

    @classmethod
    def from_config(cls, config):
        # FIXME: remove hard coding
        from detectron2.config import get_cfg
        from detectron2 import model_zoo
        from detectron2.config import CfgNode
        import kwutil
        cfg = get_cfg()
        base_cfg = model_zoo.get_config_file(config.base)
        cfg.merge_from_file(base_cfg)

        # cfg.DATASETS.TRAIN = (dataset_infos['train']['name'],)
        # cfg.DATASETS.TEST = (dataset_infos['vali']['name'],)
        # cfg.DATASETS.TEST = ()
        # cfg.DATALOADER.NUM_WORKERS = 2
        # cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url('COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml')  # Let training initialize from model zoo
        # cfg.SOLVER.IMS_PER_BATCH = 2   # This is the real 'batch size' commonly known to deep learning people
        # cfg.SOLVER.BASE_LR = 0.00025   # pick a good LR
        # cfg.SOLVER.MAX_ITER = 120_000  # 300 iterations seems good enough for this toy dataset; you will need to train longer for a practical dataset
        # cfg.SOLVER.STEPS = []          # do not decay learning rate
        # cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128   # The 'RoIHead batch size'. 128 is faster, and good enough for this toy dataset (default: 512)
        # cfg.MODEL.ROI_HEADS.NUM_CLASSES = 46  # only has one class (ballon). (see https://detectron2.readthedocs.io/tutorials/datasets.html#update-the-config-for-new-datasets)
        # cfg.MODEL.ROI_HEADS.NUM_CLASSES = 3  # only has one class (ballon). (see https://detectron2.readthedocs.io/tutorials/datasets.html#update-the-config-for-new-datasets)
        # NOTE: this config means the number of classes, but a few popular unofficial tutorials incorrect uses num_classes+1 here.
        # cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.1  # set threshold for this model

        ckpt_path = config.checkpoint_fpath
        if ckpt_path is not None or ckpt_path != 'noop':
            if not os.path.exists(ckpt_path) and ckpt_path.endswith('yaml'):
                # Checkpoint is likely given as a model zoo resource
                ckpt_path = model_zoo.get_checkpoint_url(ckpt_path)
            cfg.MODEL.WEIGHTS = os.fspath(ckpt_path)

        backend = cls(cfg, config)

        cfg_final_layer = kwutil.Yaml.coerce(config.cfg, backend='pyyaml')
        if cfg_final_layer:
            cfg2 = CfgNode(cfg_final_layer)
            print(ub.urepr(cfg2, nl=-1))
            cfg.merge_from_other_cfg(cfg2)
        print(ub.urepr(cfg, nl=-1))

        backend.device = backend.cfg.MODEL.DEVICE
        return backend


class NewStyleConfigBackend:
    """
    Handle configuration for new-style "lazy" detectron2 configs
    """
    def __init__(backend, cfg, config):
        backend.cfg = cfg
        backend.config = config
        backend.model = None
        backend.device = None

    def preprocess(backend, im_hwc):
        return im_hwc

    def load_model(backend):
        from detectron2.config import instantiate
        from detectron2.checkpoint import DetectionCheckpointer
        import torch
        model = instantiate(backend.cfg.model)
        checkpointer = DetectionCheckpointer(model)
        info = checkpointer.load(backend.config.checkpoint_fpath)  # NOQA
        model.eval()
        backend.device = torch.device(backend.config.device)
        model.to(backend.device)
        backend.model = model

    @classmethod
    def from_train_dpath(cls, train_dpath, config):
        import kwutil
        yaml_files = list(train_dpath.glob('*.yaml'))
        if len(yaml_files) == 0:
            raise Exception('no yaml files')
        elif len(yaml_files) > 1:
            raise NotImplementedError('need to find the right yaml')
        config_path = yaml_files[0]
        candidate_pkl = config_path.augment(tail='.pkl')
        # If a pickle file exists as a yaml sidecar we likely need to use that
        # instead as the yaml likely wont fully resolve.
        if candidate_pkl.exists():
            import pickle
            with open(candidate_pkl, 'rb') as fp:
                cfg = pickle.load(fp)
        else:
            cfg = kwutil.Yaml.load(config_path)
        backend = cls(cfg, config)

        # Override config values
        cfg_final_layer = kwutil.Yaml.coerce(config.cfg, backend='pyyaml')
        if cfg_final_layer:
            walker = ub.IndexableWalker(cfg)
            to_set_walker = ub.IndexableWalker(cfg_final_layer)
            for p, v in to_set_walker:
                if not isinstance(v, dict):
                    walker[p] = v
        return backend


class Detectron2Predictor:

    def __init__(predictor, config):
        predictor.config = config
        predictor.backend = None
        predictor.dset = None

    def prepare_config_backend(predictor):
        config = predictor.config
        if config.base == 'auto':
            # Attempt to find the model configuration file based on the
            # checkpoint path.
            checkpoint_fpath = ub.Path(config.checkpoint_fpath)
            train_dpath = checkpoint_fpath.parent
            backend = NewStyleConfigBackend.from_train_dpath(train_dpath, config)
        else:
            backend = OldStyleConfigBackend.from_config(config)
        predictor.backend = backend
        predictor.backend.load_model()

    def prepare_dataset(predictor):
        import kwcoco
        dset = kwcoco.CocoDataset(predictor.config.src_fpath)
        keep_annots = 0
        if not keep_annots:
            dset.clear_annotations()
        dset.reroot(absolute=True)

        # import geowatch
        from geowatch.tasks.fusion.datamodules.kwcoco_dataset import KWCocoVideoDataset
        dataset = KWCocoVideoDataset(
            dset,
            window_space_dims='full',
            channels='blue|green|red',
            time_dims=1,
            mode='test',
            # todo: enhance reduce item size to remove most information, but do
            # keep the image id.
            # reduce_item_size=True,
        )
        # batch_item = dataset[0]
        dset.reroot(absolute=True)
        bundle_dpath = ub.Path(predictor.config.dst_fpath).parent.ensuredir()
        dset.fpath = predictor.config.dst_fpath

        predictor.dset = dset
        predictor.dataset = dataset
        predictor.bundle_dpath = bundle_dpath

    def prepare_sticher(predictor):
        """
        """
        config = predictor.config
        if config.write_heatmap:
            from geowatch.tasks.fusion.coco_stitcher import CocoStitchingManager
            from kwutil import util_parallel
            writer_queue = util_parallel.BlockingJobQueue(
                mode='thread',
                # mode='serial',
                max_workers=2,
            )
            stitcher_common_kw = dict(
                stiching_space='image',
                device='numpy',
                write_probs=True,
                expected_minmax=(0, 1),
                writer_queue=writer_queue,
                assets_dname='_assets',
            )
            stitcher = CocoStitchingManager(
                predictor.dset,
                chan_code='salient',
                short_code='salient',
                num_bands=1,
                **stitcher_common_kw,
            )
        else:
            stitcher = None
            writer_queue = None
        predictor.stitcher = stitcher
        predictor.writer_queue = writer_queue

    def run_prediction(predictor):
        """
        batch prediction on the kwcoco file
        """
        # import kwimage
        # import kwarray
        import torch
        # import einops
        import numpy as np
        import rich
        # TODO: could be much more efficient
        # torch_impl = kwarray.ArrayAPI.coerce('torch')()
        # config = predictor.config

        # FIXME: We need a method to know what classes the detectron2 model was
        # trained with.
        # classes = predictor.dset.object_categories()
        dset = predictor.dset
        print(f'dset={dset}')

        loader = predictor.dataset.make_loader(
            batch_size=1,
            num_workers=4,  # config.workers
        )
        # images = dset.images()
        bundle_dpath = predictor.bundle_dpath
        rich.print(f'Pred Dpath: [link={bundle_dpath}]{bundle_dpath}[/link]')

        batch_iter = ub.ProgIter(loader, total=len(loader), desc='predict')
        with torch.no_grad():  # https://github.com/sphinx-doc/sphinx/issues/4258
            for batch in batch_iter:
                assert len(batch) == 1
                batch_item = batch[0]
                image_id = batch_item['target']['gids'][0]
                im_chw = batch_item['frames'][0]['modes']['blue|green|red']

                dets = predictor.predict_image(im_chw)

                for ann in dets.to_coco(style='new'):
                    ann['image_id'] = image_id
                    catname = ann.pop('category_name')
                    ann['category_id'] = dset.ensure_category(catname)
                    ann['role'] = 'prediction'
                    dset.add_annotation(**ann)

                if predictor.stitcher is not None:
                    frame_info = batch_item['frames'][0]
                    output_image_dsize = frame_info['output_image_dsize']
                    output_space_slice = frame_info['output_space_slice']
                    scale_outspace_from_vid = frame_info['scale_outspace_from_vid']

                    sorted_dets = dets.take(dets.scores.argsort())
                    probs = np.zeros(output_image_dsize[::-1], dtype=np.float32)
                    for sseg, score in zip(sorted_dets.data['segmentations'], sorted_dets.scores):
                        sseg.data.fill(probs, value=float(score), assert_inplace=True)

                    predictor.stitcher.accumulate_image(
                        image_id, output_space_slice, probs,
                        asset_dsize=output_image_dsize,
                        scale_asset_from_stitchspace=scale_outspace_from_vid,
                        # weights=output_weights,
                        # downweight_edges=downweight_edges,
                    )
                    # hack / fixme: this is ok, when batches correspond with
                    # images but not if we start to window.
                    predictor.stitcher.submit_finalize_image(image_id)

        if predictor.stitcher is not None:
            predictor.writer_queue.wait_until_finished()  # hack to avoid race condition
            # Prediction is completed, finalize all remaining images.
            print(f"Finalizing stitcher for {predictor.stitcher}")
            for gid in predictor.stitcher.managed_image_ids():
                predictor.stitcher.submit_finalize_image(gid)
            predictor.writer_queue.wait_until_finished()

    def predict_image(predictor, im_chw):
        import torch
        import kwimage
        import kwarray
        import einops

        # TODO: ensure references are not costly to access
        classes = COCO_CLASSES  # TODO: grab from config
        config = predictor.config
        torch_impl = kwarray.ArrayAPI.coerce('torch')()

        im_hwc = einops.rearrange(im_chw, 'c h w -> h w c').numpy()

        # Preprocess the inputs
        height, width = im_chw.shape[1:3]
        image = predictor.backend.preprocess(im_hwc)
        image = torch.as_tensor(image.astype("float32").transpose(2, 0, 1))
        image = image.to(predictor.backend.device)

        inputs = {"image": image, "height": height, "width": width}
        outputs = predictor.backend.model([inputs])[0]

        instances = outputs['instances']
        if len(instances):
            boxes = instances.pred_boxes
            scores = instances.scores
            boxes = kwimage.Boxes(boxes.tensor, format='ltrb').numpy()
            scores = torch_impl.numpy(instances.scores)
            pred_class_indexes = torch_impl.numpy(instances.pred_classes)

            detkw = {
                'boxes': boxes,
                'scores': scores,
                'class_idxs': pred_class_indexes,
                'classes': classes,
            }
            if hasattr(instances, 'pred_masks'):
                pred_masks = torch_impl.numpy(instances.pred_masks)
                segmentations = []
                for cmask in pred_masks:
                    mask = kwimage.Mask.coerce(cmask)
                    poly = mask.to_multi_polygon()
                    segmentations.append(poly)
                detkw['segmentations'] = segmentations
            else:
                # detkw['segmentations'] = None
                ...

            dets = kwimage.Detections(**detkw)
            if config.nms_thresh and config.nms_thresh > 0:
                dets = dets.non_max_supress(thresh=config.nms_thresh)
        else:
            dets = kwimage.Detections.random(0)
            dets.data['segmentations'] = []
        return dets


def detectron_predict(config):
    import geowatch_tpl
    detectron2 = geowatch_tpl.import_submodule('detectron2')  # NOQA
    import kwutil
    import rich

    proc_context = kwutil.ProcessContext(
        name='geowatch.tasks.detectron2.predict',
        config=kwutil.Json.ensure_serializable(dict(config)),
        track_emissions=True,
    )
    proc_context.start()
    print(f'proc_context.obj = {ub.urepr(proc_context.obj, nl=3)}')

    predictor = Detectron2Predictor(config)
    predictor.prepare_dataset()
    predictor.prepare_config_backend()
    predictor.prepare_sticher()
    predictor.run_prediction()

    # Write final results
    predictor.dset.dataset.setdefault('info', [])
    proc_context.stop()
    print(f'proc_context.obj = {ub.urepr(proc_context.obj, nl=3)}')
    predictor.dset.dataset['info'].append(proc_context.obj)
    predictor.dset.dump()
    bundle_dpath = predictor.bundle_dpath
    rich.print(f'Wrote to: [link={bundle_dpath}]{bundle_dpath}[/link]')


COCO_CLASSES = ['__background__', 'person', 'bicycle', 'car', 'motorcycle',
                'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
                'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
                'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
                'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
                'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
                'kite', 'baseball bat', 'baseball glove', 'skateboard',
                'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
                'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
                'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
                'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
                'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
                'keyboard', 'cell phone', 'microwave', 'oven', 'toaster',
                'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
                'teddy bear', 'hair drier', 'toothbrush']

if __name__ == '__main__':
    """

    CommandLine:
        python -m geowatch.tasks.detectron2.predict
    """
    __cli__.main()
