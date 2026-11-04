"""Hiệu chỉnh BN không được lén học trọng số hay bật dropout."""

import torch
from src.evaluation.recalibrate_domain_bn import update_statistics
from torch.utils.data import DataLoader, TensorDataset


def test_statistics_change_without_parameter_or_dropout_changes():
    model = torch.nn.Sequential(
        torch.nn.Conv2d(3, 4, 1),
        torch.nn.BatchNorm2d(4),
        torch.nn.Dropout(0.9),
        torch.nn.AdaptiveAvgPool2d(1),
    )
    before = {k: v.detach().clone() for k, v in model.named_parameters()}
    mean = model[1].running_mean.clone()
    dropout_modes = []
    hook = model[2].register_forward_pre_hook(
        lambda layer, args: dropout_modes.append(layer.training)
    )
    data = DataLoader(TensorDataset(torch.full((8, 3, 6, 6), 5.0), torch.zeros(8)), batch_size=4)
    update_statistics(model, data, torch.device("cpu"))
    hook.remove()
    assert not torch.equal(mean, model[1].running_mean)
    assert int(model[1].num_batches_tracked) == 2
    assert all(torch.equal(before[k], v) for k, v in model.named_parameters())
    assert dropout_modes == [False, False]
    assert model[1].momentum == 0.1 and not model.training
