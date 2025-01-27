# Copyright (c) OpenMMLab. All rights reserved.
import os.path as osp
import sys

import mmcv
import numpy as np

from torch_liberator.deployer import DeployedModel

# ----------------------------------------------
def get_dummy_imputs_metas(net_shape):
    """Get dummy inputs metas.
    Args:
        net_shape (tuple): (width, height, number_of_channels).
    Returns:
        dict: A dictionary containing dummy inputs metadata.
    """
    img_norm_cfg = {'img_norm_cfg': {'mean': np.array([0.248, 0.219 , 0.202]),
                                    'std': np.array([0.297, 0.405 , 0.372]),
                                    'to_rgb': True}}
    input_metas_ = {}
    input_metas_['ori_filename'] = ""
    input_metas_['ori_shape'] = net_shape
    input_metas_['img_shape'] = net_shape
    input_metas_['pad_shape'] = net_shape
    input_metas_['scale_factor'] =  np.array([1.0, 1.0, 1.0, 1.0])
    input_metas_['flip'] = False
    input_metas_['flip_direction'] = None
    input_metas_['img_norm_cfg'] = img_norm_cfg

    return {'img_metas':[[input_metas_]]}

# ----------------------------------------------
def crcnn2onnx(path_torch_liberator_bioharn_model,
               net_shape,
               batch_size,
               output_prefix):
    """Convert PyTorch model to ONNX model.
    Args:
        path_torch_liberator_bioharn_model (str): path to torch liberator bioharn
            zip file.
        net_shape (tuple): (width, height, number_of_channels).
        batch_size (int): batch size.
        output_prefix (str): path to onnx output prefix.
    """
    import torch

    from mmdeploy.apis.core.pipeline_manager import no_mp
    from mmdeploy.utils import (Backend, get_backend, get_dynamic_axes,
                                get_input_shape, get_onnx_config, load_config)
    from mmdeploy.codebase import import_codebase
    from mmdeploy.utils import get_codebase

    from  mmdeploy.apis.onnx import export

    import importlib.util
    module_name = 'mmdeploy'
    module_spec = importlib.util.find_spec(module_name)
    deploy_cfg_path = ""
    if module_spec is not None:
        module_path = module_spec.origin
        deploy_cfg_path = osp.join(osp.dirname(module_path), "configs/mmdet/detection/detection_onnxruntime_static.py")
    else:
        print("Cannot find mmdeploy to perform onnx conversion", file=sys.stderr)
        sys.exit(1)
    deploy_cfg = mmcv.Config.fromfile(deploy_cfg_path)

    # Load torch model
    loader = DeployedModel(path_torch_liberator_bioharn_model)
    bioharn_model = loader.load_model()
    bioharn_model.eval()
    torch_model = bioharn_model.detector

    # Import code base
    codebase_type = get_codebase(deploy_cfg)
    import_codebase(codebase_type)

    # Export to onnx
    context_info = dict()
    context_info['deploy_cfg'] = deploy_cfg
    backend = get_backend(deploy_cfg).value
    onnx_cfg = get_onnx_config(deploy_cfg)
    opset_version = onnx_cfg.get('opset_version', 11)
    input_names = onnx_cfg['input_names']
    output_names = onnx_cfg['output_names']
    axis_names = input_names + output_names
    dynamic_axes = get_dynamic_axes(deploy_cfg, axis_names)
    verbose = not onnx_cfg.get('strip_doc_string', True) or onnx_cfg.get(
        'verbose', False)
    keep_initializers_as_inputs = onnx_cfg.get('keep_initializers_as_inputs',
                                               True)
    optimize = onnx_cfg.get('optimize', False)
    if backend == Backend.NCNN.value:
        """NCNN backend needs a precise blob counts, while using onnx optimizer
        will merge duplicate initilizers without reference count."""
        optimize = False

    model_inputs = torch.randn((batch_size, net_shape[2], net_shape[1], net_shape[0]), requires_grad=True)
    input_metas = get_dummy_imputs_metas(net_shape)

    with no_mp():
        export(
            torch_model,
            model_inputs,
            input_metas=input_metas,
            output_path_prefix=output_prefix,
            backend=backend,
            input_names=input_names,
            output_names=output_names,
            context_info=context_info,
            opset_version=opset_version,
            dynamic_axes=dynamic_axes,
            verbose=verbose,
            keep_initializers_as_inputs=keep_initializers_as_inputs,
            optimize=optimize)