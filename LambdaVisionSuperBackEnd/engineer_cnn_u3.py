"""
Engineer CNN U3
Residual U-Net for 64x64 station segmentation.

PyTorch shape convention: [B, C, H, W]

Input:
    [B, 4, 64, 64] = RGB + Valid

Outputs:
    final logits  : [B, 1, 64, 64]
    coarse logits : [B, 1, 16, 16]  (auxiliary training head)

Architecture:
    [B,4,64,64]
      -> Stem 4->32
      -> Res32                     = E0 [B,32,64,64]
      -> Down s2 32->64 -> Res64  = E1 [B,64,32,32]
      -> Down s2 64->128 -> Res128= E2 [B,128,16,16]
      -> Down s2 128->256
      -> Res256 -> Res256          = B  [B,256,8,8]

    B  -> 1x1 256->128 -> bilinear x2 -> concat E2
       -> 3x3 256->128 -> Res128   = D2 [B,128,16,16]
       -> coarse 1x1 128->1        = [B,1,16,16]

    D2 -> 1x1 128->64 -> bilinear x2 -> concat E1
       -> 3x3 128->64 -> Res64     = D1 [B,64,32,32]

    D1 -> 1x1 64->32 -> bilinear x2 -> concat E0
       -> 3x3 64->32 -> Res32      = D0 [B,32,64,64]

    D0 -> 1x1 32->1                = final [B,1,64,64]

Valid-mask policy:
- Valid is the fourth input channel.
- Invalid RGB should be neutral-filled before entering the model.
- Intermediate feature maps are NOT hard-masked.
- Loss is masked by Valid.
- Inference probability may be multiplied by Valid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class EngineerCNNU3Config:
    input_channels: int = 4
    output_channels: int = 1
    input_size: int = 64

    c0: int = 32
    c1: int = 64
    c2: int = 128
    c3: int = 256

    group_norm_groups: int = 8
    dropout: float = 0.0

    dice_weight: float = 1.0
    coarse_weight: float = 0.20


def make_group_norm(channels: int, requested_groups: int = 8) -> nn.GroupNorm:
    groups = min(channels, requested_groups)
    while channels % groups != 0:
        groups -= 1
    return nn.GroupNorm(groups, channels)


class ConvNormAct(nn.Module):
    def __init__(
        self,
        in_ch: int,
        out_ch: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: Optional[int] = None,
        groups: int = 8,
    ):
        super().__init__()
        if padding is None:
            padding = kernel_size // 2

        self.net = nn.Sequential(
            nn.Conv2d(
                in_ch,
                out_ch,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                bias=False,
            ),
            make_group_norm(out_ch, groups),
            nn.GELU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ResidualBlock(nn.Module):
    """
    x -> Conv3x3 -> GN -> GELU -> [Dropout]
      -> Conv3x3 -> GN
    output = GELU(x + residual)
    """

    def __init__(
        self,
        channels: int,
        groups: int = 8,
        dropout: float = 0.0,
    ):
        super().__init__()

        layers = [
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            make_group_norm(channels, groups),
            nn.GELU(),
        ]

        if dropout > 0:
            layers.append(nn.Dropout2d(dropout))

        layers += [
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            make_group_norm(channels, groups),
        ]

        self.branch = nn.Sequential(*layers)
        self.out_act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.out_act(x + self.branch(x))


class DownsampleStage(nn.Module):
    """
    Learned downsampling with strided convolution, NOT MaxPool.

    [B,Cin,H,W]
      -> Conv3x3 stride=2, Cin->Cout
      -> GN -> GELU
      -> ResidualBlock(Cout)
    [B,Cout,H/2,W/2]
    """

    def __init__(
        self,
        in_ch: int,
        out_ch: int,
        groups: int = 8,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.down = ConvNormAct(
            in_ch,
            out_ch,
            kernel_size=3,
            stride=2,
            padding=1,
            groups=groups,
        )
        self.res = ResidualBlock(
            out_ch,
            groups=groups,
            dropout=dropout,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.res(self.down(x))


class DecoderStage(nn.Module):
    """
    Decoder stage:
        1) project channels with Conv1x1
        2) bilinear upsample to skip resolution
        3) concatenate skip along channel dimension
        4) Conv3x3 fusion
        5) ResidualBlock

    Example:
        x    [B,256,8,8]
        skip [B,128,16,16]

        project -> [B,128,8,8]
        up      -> [B,128,16,16]
        concat  -> [B,256,16,16]
        merge   -> [B,128,16,16]
    """

    def __init__(
        self,
        in_ch: int,
        skip_ch: int,
        out_ch: int,
        groups: int = 8,
        dropout: float = 0.0,
    ):
        super().__init__()

        self.project = nn.Conv2d(
            in_ch,
            out_ch,
            kernel_size=1,
            bias=False,
        )

        self.merge = ConvNormAct(
            out_ch + skip_ch,
            out_ch,
            kernel_size=3,
            stride=1,
            padding=1,
            groups=groups,
        )

        self.res = ResidualBlock(
            out_ch,
            groups=groups,
            dropout=dropout,
        )

    def forward(
        self,
        x: torch.Tensor,
        skip: torch.Tensor,
    ) -> torch.Tensor:

        x = self.project(x)

        x = F.interpolate(
            x,
            size=skip.shape[-2:],
            mode="bilinear",
            align_corners=False,
        )

        x = torch.cat([x, skip], dim=1)
        x = self.merge(x)
        x = self.res(x)
        return x


class EngineerCNNU3(nn.Module):
    def __init__(
        self,
        cfg: EngineerCNNU3Config = EngineerCNNU3Config(),
    ):
        super().__init__()
        self.cfg = cfg
        g = cfg.group_norm_groups

        if cfg.input_channels != 4:
            raise ValueError("U3 expects 4 input channels: RGB + Valid")

        if cfg.input_size != 64:
            raise ValueError("U3 baseline expects 64x64 station input")

        # Encoder -------------------------------------------------------------
        self.stem = ConvNormAct(
            cfg.input_channels,
            cfg.c0,
            3,
            1,
            1,
            g,
        )
        self.enc0 = ResidualBlock(cfg.c0, g, cfg.dropout)

        self.enc1 = DownsampleStage(
            cfg.c0, cfg.c1, g, cfg.dropout
        )

        self.enc2 = DownsampleStage(
            cfg.c1, cfg.c2, g, cfg.dropout
        )

        self.bottleneck_down = ConvNormAct(
            cfg.c2,
            cfg.c3,
            3,
            2,
            1,
            g,
        )
        self.bottleneck_res1 = ResidualBlock(
            cfg.c3, g, cfg.dropout
        )
        self.bottleneck_res2 = ResidualBlock(
            cfg.c3, g, cfg.dropout
        )

        # Decoder -------------------------------------------------------------
        self.dec2 = DecoderStage(
            cfg.c3,
            cfg.c2,
            cfg.c2,
            g,
            cfg.dropout,
        )
        self.coarse_head = nn.Conv2d(
            cfg.c2,
            cfg.output_channels,
            kernel_size=1,
        )

        self.dec1 = DecoderStage(
            cfg.c2,
            cfg.c1,
            cfg.c1,
            g,
            cfg.dropout,
        )

        self.dec0 = DecoderStage(
            cfg.c1,
            cfg.c0,
            cfg.c0,
            g,
            cfg.dropout,
        )

        self.final_head = nn.Conv2d(
            cfg.c0,
            cfg.output_channels,
            kernel_size=1,
        )

    def _validate_input(self, x: torch.Tensor) -> None:
        if x.ndim != 4:
            raise ValueError(
                f"Expected [B,C,H,W], got {tuple(x.shape)}"
            )

        if x.shape[1] != self.cfg.input_channels:
            raise ValueError(
                f"Expected {self.cfg.input_channels} channels, "
                f"got {x.shape[1]}"
            )

        if x.shape[-2:] != (
            self.cfg.input_size,
            self.cfg.input_size,
        ):
            raise ValueError(
                f"Expected 64x64 input, got {tuple(x.shape[-2:])}"
            )

    def forward(
        self,
        x: torch.Tensor,
        return_intermediates: bool = False,
    ):
        self._validate_input(x)

        # Encoder
        e0 = self.enc0(self.stem(x))             # [B,32,64,64]
        e1 = self.enc1(e0)                       # [B,64,32,32]
        e2 = self.enc2(e1)                       # [B,128,16,16]

        b = self.bottleneck_down(e2)             # [B,256,8,8]
        b = self.bottleneck_res1(b)
        b = self.bottleneck_res2(b)              # [B,256,8,8]

        # Decoder
        d2 = self.dec2(b, e2)                    # [B,128,16,16]
        coarse_logits = self.coarse_head(d2)     # [B,1,16,16]

        d1 = self.dec1(d2, e1)                   # [B,64,32,32]
        d0 = self.dec0(d1, e0)                   # [B,32,64,64]

        logits = self.final_head(d0)             # [B,1,64,64]

        if not return_intermediates:
            return logits

        return {
            "logits": logits,
            "coarse_logits": coarse_logits,
            "encoder64": e0,
            "encoder32": e1,
            "encoder16": e2,
            "bottleneck": b,
            "decoder16": d2,
            "decoder32": d1,
            "decoder64": d0,
        }

    @torch.no_grad()
    def predict_probability(
        self,
        x: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:

        prob = torch.sigmoid(self.forward(x))

        if valid_mask is not None:
            if valid_mask.ndim == 3:
                valid_mask = valid_mask.unsqueeze(1)

            if valid_mask.shape != prob.shape:
                raise ValueError(
                    f"valid mask shape {tuple(valid_mask.shape)} "
                    f"!= probability shape {tuple(prob.shape)}"
                )

            prob = prob * valid_mask.float()

        return prob

    @torch.no_grad()
    def predict_mask(
        self,
        x: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
        threshold: float = 0.5,
    ) -> torch.Tensor:

        prob = self.predict_probability(
            x,
            valid_mask=valid_mask,
        )

        return (prob >= threshold).to(torch.uint8)


def _b1hw(x: torch.Tensor, name: str) -> torch.Tensor:
    if x.ndim == 3:
        x = x.unsqueeze(1)

    if x.ndim != 4 or x.shape[1] != 1:
        raise ValueError(
            f"{name} must be [B,1,H,W] or [B,H,W], "
            f"got {tuple(x.shape)}"
        )

    return x


def masked_bce_loss(
    logits: torch.Tensor,
    target: torch.Tensor,
    valid: torch.Tensor,
    eps: float = 1e-6,
) -> torch.Tensor:

    target = _b1hw(target, "target").float()
    valid = _b1hw(valid, "valid").float()

    loss_map = F.binary_cross_entropy_with_logits(
        logits,
        target,
        reduction="none",
    )

    return (
        (loss_map * valid).sum()
        / (valid.sum() + eps)
    )


def masked_dice_loss(
    logits: torch.Tensor,
    target: torch.Tensor,
    valid: torch.Tensor,
    eps: float = 1e-6,
) -> torch.Tensor:

    target = _b1hw(target, "target").float()
    valid = _b1hw(valid, "valid").float()

    prob = torch.sigmoid(logits)

    prob = prob * valid
    target = target * valid

    dims = (1, 2, 3)

    intersection = (prob * target).sum(dim=dims)
    denominator = prob.sum(dim=dims) + target.sum(dim=dims)

    dice = (
        2.0 * intersection + eps
    ) / (
        denominator + eps
    )

    return 1.0 - dice.mean()


def engineer_cnn_u3_loss(
    outputs: Dict[str, torch.Tensor],
    gt_mask_64: torch.Tensor,
    valid_mask_64: torch.Tensor,
    dice_weight: float = 1.0,
    coarse_weight: float = 0.20,
) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    """
    L_total = L_fine + coarse_weight * L_coarse

    L_fine   = masked_BCE + dice_weight * masked_Dice
    L_coarse = masked_BCE + dice_weight * masked_Dice

    GT coarse    : nearest 64->16
    Valid coarse : area    64->16

    Coarse logits are auxiliary only and are NOT added to final logits.
    """

    logits = outputs["logits"]
    coarse_logits = outputs["coarse_logits"]

    gt = _b1hw(gt_mask_64, "gt_mask_64").float()
    valid = _b1hw(valid_mask_64, "valid_mask_64").float()

    gt = gt * valid

    fine_bce = masked_bce_loss(logits, gt, valid)
    fine_dice = masked_dice_loss(logits, gt, valid)
    fine_total = fine_bce + dice_weight * fine_dice

    coarse_size = coarse_logits.shape[-2:]

    coarse_gt = F.interpolate(
        gt,
        size=coarse_size,
        mode="nearest",
    )

    coarse_valid = F.interpolate(
        valid,
        size=coarse_size,
        mode="area",
    )

    coarse_bce = masked_bce_loss(
        coarse_logits,
        coarse_gt,
        coarse_valid,
    )

    coarse_dice = masked_dice_loss(
        coarse_logits,
        coarse_gt,
        coarse_valid,
    )

    coarse_total = (
        coarse_bce
        + dice_weight * coarse_dice
    )

    total = (
        fine_total
        + coarse_weight * coarse_total
    )

    parts = {
        "total": total.detach(),
        "fine_bce": fine_bce.detach(),
        "fine_dice": fine_dice.detach(),
        "fine_total": fine_total.detach(),
        "coarse_bce": coarse_bce.detach(),
        "coarse_dice": coarse_dice.detach(),
        "coarse_total": coarse_total.detach(),
    }

    return total, parts


def count_parameters(model: nn.Module) -> Dict[str, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )
    return {
        "total": total,
        "trainable": trainable,
    }


@torch.no_grad()
def architecture_sanity_check(batch_size: int = 2) -> None:
    model = EngineerCNNU3()
    model.eval()

    x = torch.randn(batch_size, 4, 64, 64)
    x[:, 3:4] = (
        torch.rand(batch_size, 1, 64, 64) > 0.1
    ).float()

    out = model(x, return_intermediates=True)

    expected = {
        "encoder64": (batch_size, 32, 64, 64),
        "encoder32": (batch_size, 64, 32, 32),
        "encoder16": (batch_size, 128, 16, 16),
        "bottleneck": (batch_size, 256, 8, 8),
        "decoder16": (batch_size, 128, 16, 16),
        "decoder32": (batch_size, 64, 32, 32),
        "decoder64": (batch_size, 32, 64, 64),
        "coarse_logits": (batch_size, 1, 16, 16),
        "logits": (batch_size, 1, 64, 64),
    }

    print("=" * 68)
    print("Engineer CNN U3")
    print("=" * 68)

    for name, shape in expected.items():
        actual = tuple(out[name].shape)
        print(f"{name:16s}: {actual}")

        if actual != shape:
            raise RuntimeError(
                f"{name}: expected {shape}, got {actual}"
            )

    params = count_parameters(model)

    print()
    print(f"Total parameters    : {params['total']:,}")
    print(f"Trainable parameters: {params['trainable']:,}")

    gt = (
        torch.rand(batch_size, 1, 64, 64) > 0.7
    ).float()

    valid = x[:, 3:4]

    loss, _ = engineer_cnn_u3_loss(
        out,
        gt,
        valid,
    )

    if not torch.isfinite(loss):
        raise RuntimeError("Non-finite dummy loss")

    print(f"Dummy loss          : {float(loss):.6f}")
    print("[OK] sanity check passed")


if __name__ == "__main__":
    architecture_sanity_check()
