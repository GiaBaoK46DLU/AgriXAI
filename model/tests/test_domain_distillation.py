"""Teacher chỉ làm tham chiếu, không nhận gradient từ loss chưng cất."""

import torch
from src.training.rehearse_domain import distillation_loss


def test_distillation_is_zero_for_equal_logits_and_teacher_is_detached():
    logits = torch.tensor([[1.0, -2.0, 3.0], [0.0, 1.0, 2.0]], requires_grad=True)
    teacher = logits.detach().clone().requires_grad_(True)
    assert abs(float(distillation_loss(logits, teacher).detach())) < 1e-6
    teacher = (
        (teacher + torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])).detach().requires_grad_(True)
    )
    loss = distillation_loss(logits, teacher)
    assert loss > 0
    loss.backward()
    assert logits.grad is not None and torch.isfinite(logits.grad).all()
    assert teacher.grad is None
