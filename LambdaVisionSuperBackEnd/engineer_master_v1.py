"""
Engineer Master Fusion V1
=========================

A five-stream knowledge-fusion network sitting on top of two frozen Engineers:

    Flow 1  MLP telemetry concat : [B, 1728]
    Flow 2  MLP latent           : [B,  256]
    Flow 3  CNN bottleneck       : [B,256, 8, 8]
    Flow 4  CNN decoder D0       : [B, 32,64,64]
    Flow 5  MLP/CNN disagreement : built from both final logits + Valid

The Master does NOT see raw RGB. It is intentionally forced to reason from the
internal states and responses of the two Engineers.

Output
------
The Master predicts per-pixel expert weights and a bounded correction:

    Z_master = W_mlp * Z_mlp + W_cnn * Z_cnn + DeltaZ

where:
    W_mlp + W_cnn = 1  (softmax across expert dimension)
    DeltaZ = residual_logit_max * tanh(raw_residual)

This makes the final decision interpretable while still allowing a limited
correction when both frozen Engineers are wrong.

PyTorch tensor convention: [B, C, H, W]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# =============================================================================
# CONFIG
# =============================================================================

@dataclass
class EngineerMasterV1Config:
    # -------------------------------------------------------------------------
    # Five-stream input dimensions
    # -------------------------------------------------------------------------
    mlp_concat_dim: int = 1728
    mlp_latent_dim: int = 256

    cnn_bottleneck_channels: int = 256
    cnn_bottleneck_size: int = 8

    cnn_d0_channels: int = 32
    output_size: int = 64

    # -------------------------------------------------------------------------
    # Flow 1 - MLP wide telemetry
    # -------------------------------------------------------------------------
    flow1_hidden_dim: int = 768
    flow1_out_dim: int = 256

    # Flow 2 - MLP latent
    flow2_hidden_dim: int = 256
    flow2_out_dim: int = 128

    # Global knowledge fusion
    global_knowledge_dim: int = 256

    # -------------------------------------------------------------------------
    # Flow 3 - CNN bottleneck interpreter
    # -------------------------------------------------------------------------
    flow3_c0: int = 128
    flow3_c1: int = 96
    flow3_out_channels: int = 64

    # Flow 4 - CNN D0 interpreter
    flow4_channels: int = 48

    # Flow 5 - disagreement interpreter
    # Inputs: probability disagreement, bounded logit disagreement, valid
    disagreement_input_channels: int = 3
    flow5_c0: int = 16
    flow5_out_channels: int = 32

    # -------------------------------------------------------------------------
    # Spatial fusion
    # -------------------------------------------------------------------------
    spatial_fusion_channels: int = 96
    master_map_channels: int = 64

    # -------------------------------------------------------------------------
    # Numerical behavior
    # -------------------------------------------------------------------------
    group_norm_groups: int = 8
    dropout: float = 0.0

    # D_z = tanh(|Z_cnn - Z_mlp| / logit_diff_scale)
    logit_diff_scale: float = 4.0

    # DeltaZ is bounded to [-residual_logit_max, +residual_logit_max]
    residual_logit_max: float = 2.0

    # -------------------------------------------------------------------------
    # Default loss weights
    # -------------------------------------------------------------------------
    dice_weight: float = 1.0
    residual_penalty_weight: float = 0.01
    gate_supervision_weight: float = 0.05
    gate_target_temperature: float = 0.15


# =============================================================================
# BUILDING BLOCKS
# =============================================================================

def make_group_norm(
    channels: int,
    requested_groups: int = 8,
) -> nn.GroupNorm:
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
        padding: int | None = None,
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


class ResidualConvBlock(nn.Module):
    """Residual 3x3 CNN block: y = GELU(x + F(x))."""

    def __init__(
        self,
        channels: int,
        groups: int = 8,
        dropout: float = 0.0,
    ):
        super().__init__()

        layers = [
            nn.Conv2d(
                channels,
                channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            make_group_norm(channels, groups),
            nn.GELU(),
        ]

        if dropout > 0.0:
            layers.append(nn.Dropout2d(dropout))

        layers.extend([
            nn.Conv2d(
                channels,
                channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            make_group_norm(channels, groups),
        ])

        self.branch = nn.Sequential(*layers)
        self.out_act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.out_act(x + self.branch(x))


class VectorProjector(nn.Module):
    """Linear -> LN -> GELU -> [Dropout] -> Linear -> LN -> GELU."""

    def __init__(
        self,
        in_dim: int,
        hidden_dim: int,
        out_dim: int,
        dropout: float = 0.0,
    ):
        super().__init__()

        layers = [
            nn.Linear(in_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
        ]

        if dropout > 0.0:
            layers.append(nn.Dropout(dropout))

        layers.extend([
            nn.Linear(hidden_dim, out_dim),
            nn.LayerNorm(out_dim),
            nn.GELU(),
        ])

        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# =============================================================================
# FIVE STREAM INTERPRETERS
# =============================================================================

class MLPWideFlow(nn.Module):
    """Flow 1: [B,1728] -> [B,256]."""

    def __init__(self, cfg: EngineerMasterV1Config):
        super().__init__()
        self.project = VectorProjector(
            cfg.mlp_concat_dim,
            cfg.flow1_hidden_dim,
            cfg.flow1_out_dim,
            cfg.dropout,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.project(x)


class MLPLatentFlow(nn.Module):
    """Flow 2: [B,256] -> [B,128]."""

    def __init__(self, cfg: EngineerMasterV1Config):
        super().__init__()
        self.project = VectorProjector(
            cfg.mlp_latent_dim,
            cfg.flow2_hidden_dim,
            cfg.flow2_out_dim,
            cfg.dropout,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.project(x)


class CNNBottleneckFlow(nn.Module):
    """
    Flow 3:
        [B,256,8,8]
          -> 1x1 256->128 + GN + GELU
          -> Res128
          -> up 16x16 -> 3x3 128->96
          -> up 32x32 -> 3x3 96->64
          -> up 64x64
        output [B,64,64,64]
    """

    def __init__(self, cfg: EngineerMasterV1Config):
        super().__init__()
        g = cfg.group_norm_groups

        self.entry = ConvNormAct(
            cfg.cnn_bottleneck_channels,
            cfg.flow3_c0,
            kernel_size=1,
            padding=0,
            groups=g,
        )
        self.res = ResidualConvBlock(
            cfg.flow3_c0,
            groups=g,
            dropout=cfg.dropout,
        )
        self.to16 = ConvNormAct(
            cfg.flow3_c0,
            cfg.flow3_c1,
            kernel_size=3,
            padding=1,
            groups=g,
        )
        self.to32 = ConvNormAct(
            cfg.flow3_c1,
            cfg.flow3_out_channels,
            kernel_size=3,
            padding=1,
            groups=g,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.entry(x)
        x = self.res(x)

        x = F.interpolate(
            x,
            scale_factor=2.0,
            mode="bilinear",
            align_corners=False,
        )
        x = self.to16(x)

        x = F.interpolate(
            x,
            scale_factor=2.0,
            mode="bilinear",
            align_corners=False,
        )
        x = self.to32(x)

        x = F.interpolate(
            x,
            scale_factor=2.0,
            mode="bilinear",
            align_corners=False,
        )

        return x


class CNND0Flow(nn.Module):
    """Flow 4: [B,32,64,64] -> [B,48,64,64]."""

    def __init__(self, cfg: EngineerMasterV1Config):
        super().__init__()
        g = cfg.group_norm_groups

        self.entry = ConvNormAct(
            cfg.cnn_d0_channels,
            cfg.flow4_channels,
            kernel_size=3,
            padding=1,
            groups=g,
        )
        self.res = ResidualConvBlock(
            cfg.flow4_channels,
            groups=g,
            dropout=cfg.dropout,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.res(self.entry(x))


class DisagreementFlow(nn.Module):
    """Flow 5: [Dp, Dz_bounded, Valid] -> [B,32,64,64]."""

    def __init__(self, cfg: EngineerMasterV1Config):
        super().__init__()
        g = cfg.group_norm_groups

        self.entry = ConvNormAct(
            cfg.disagreement_input_channels,
            cfg.flow5_c0,
            kernel_size=3,
            padding=1,
            groups=g,
        )
        self.expand = ConvNormAct(
            cfg.flow5_c0,
            cfg.flow5_out_channels,
            kernel_size=3,
            padding=1,
            groups=g,
        )
        self.res = ResidualConvBlock(
            cfg.flow5_out_channels,
            groups=g,
            dropout=cfg.dropout,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.res(self.expand(self.entry(x)))


# =============================================================================
# MASTER NETWORK
# =============================================================================

class EngineerMasterV1(nn.Module):
    """Five-stream frozen-expert knowledge fusion network."""

    def __init__(
        self,
        cfg: EngineerMasterV1Config = EngineerMasterV1Config(),
    ):
        super().__init__()
        self.cfg = cfg
        g = cfg.group_norm_groups

        # Global/vector side --------------------------------------------------
        self.flow1 = MLPWideFlow(cfg)
        self.flow2 = MLPLatentFlow(cfg)

        global_in_dim = (
            cfg.flow1_out_dim
            + cfg.flow2_out_dim
        )

        self.global_fusion = nn.Sequential(
            nn.Linear(
                global_in_dim,
                cfg.global_knowledge_dim,
            ),
            nn.LayerNorm(cfg.global_knowledge_dim),
            nn.GELU(),
        )

        # Spatial side --------------------------------------------------------
        self.flow3 = CNNBottleneckFlow(cfg)
        self.flow4 = CNND0Flow(cfg)
        self.flow5 = DisagreementFlow(cfg)

        spatial_concat_channels = (
            cfg.flow3_out_channels
            + cfg.flow4_channels
            + cfg.flow5_out_channels
        )

        self.spatial_merge = ConvNormAct(
            spatial_concat_channels,
            cfg.spatial_fusion_channels,
            kernel_size=3,
            padding=1,
            groups=g,
        )

        # Global knowledge -> FiLM gamma/beta for spatial feature map.
        self.film = nn.Linear(
            cfg.global_knowledge_dim,
            2 * cfg.spatial_fusion_channels,
        )

        self.post_film = nn.Sequential(
            ResidualConvBlock(
                cfg.spatial_fusion_channels,
                groups=g,
                dropout=cfg.dropout,
            ),
            ConvNormAct(
                cfg.spatial_fusion_channels,
                cfg.master_map_channels,
                kernel_size=3,
                padding=1,
                groups=g,
            ),
            ResidualConvBlock(
                cfg.master_map_channels,
                groups=g,
                dropout=cfg.dropout,
            ),
        )

        # Interpretable final decision heads ---------------------------------
        self.expert_gate_head = nn.Conv2d(
            cfg.master_map_channels,
            2,
            kernel_size=1,
            bias=True,
        )

        self.residual_head = nn.Conv2d(
            cfg.master_map_channels,
            1,
            kernel_size=1,
            bias=True,
        )

        self._initialize_decision_heads()

    def _initialize_decision_heads(self) -> None:
        """
        Start close to a neutral ensemble:
            W_mlp ~= W_cnn ~= 0.5
            DeltaZ ~= 0

        This prevents an untrained Master from immediately producing a large
        correction to the two frozen Engineers.
        """
        # Tiny weights keep the initial decision very close to 50/50 + zero
        # correction, while still allowing gradients to reach the fusion
        # backbone from the very first optimization step.
        nn.init.normal_(self.expert_gate_head.weight, mean=0.0, std=1e-3)
        nn.init.zeros_(self.expert_gate_head.bias)

        nn.init.normal_(self.residual_head.weight, mean=0.0, std=1e-3)
        nn.init.zeros_(self.residual_head.bias)

    def _validate_inputs(
        self,
        mlp_concat: torch.Tensor,
        mlp_latent: torch.Tensor,
        cnn_bottleneck: torch.Tensor,
        cnn_d0: torch.Tensor,
        mlp_logits: torch.Tensor,
        cnn_logits: torch.Tensor,
        valid: torch.Tensor,
    ) -> None:
        c = self.cfg

        if mlp_concat.ndim != 2 or mlp_concat.shape[1] != c.mlp_concat_dim:
            raise ValueError(
                f"mlp_concat must be [B,{c.mlp_concat_dim}], "
                f"got {tuple(mlp_concat.shape)}"
            )

        if mlp_latent.ndim != 2 or mlp_latent.shape[1] != c.mlp_latent_dim:
            raise ValueError(
                f"mlp_latent must be [B,{c.mlp_latent_dim}], "
                f"got {tuple(mlp_latent.shape)}"
            )

        if cnn_bottleneck.ndim != 4 or tuple(cnn_bottleneck.shape[1:]) != (
            c.cnn_bottleneck_channels,
            c.cnn_bottleneck_size,
            c.cnn_bottleneck_size,
        ):
            raise ValueError(
                "cnn_bottleneck must be "
                f"[B,{c.cnn_bottleneck_channels},{c.cnn_bottleneck_size},"
                f"{c.cnn_bottleneck_size}], got {tuple(cnn_bottleneck.shape)}"
            )

        if cnn_d0.ndim != 4 or tuple(cnn_d0.shape[1:]) != (
            c.cnn_d0_channels,
            c.output_size,
            c.output_size,
        ):
            raise ValueError(
                f"cnn_d0 must be [B,{c.cnn_d0_channels},{c.output_size},"
                f"{c.output_size}], got {tuple(cnn_d0.shape)}"
            )

        for name, tensor in (
            ("mlp_logits", mlp_logits),
            ("cnn_logits", cnn_logits),
            ("valid", valid),
        ):
            if tensor.ndim == 3:
                tensor = tensor.unsqueeze(1)
            if tensor.ndim != 4 or tuple(tensor.shape[1:]) != (
                1,
                c.output_size,
                c.output_size,
            ):
                raise ValueError(
                    f"{name} must be [B,1,{c.output_size},{c.output_size}], "
                    f"got {tuple(tensor.shape)}"
                )

    def forward(
        self,
        *,
        mlp_concat: torch.Tensor,
        mlp_latent: torch.Tensor,
        cnn_bottleneck: torch.Tensor,
        cnn_d0: torch.Tensor,
        mlp_logits: torch.Tensor,
        cnn_logits: torch.Tensor,
        valid: torch.Tensor,
        return_intermediates: bool = False,
    ):
        if valid.ndim == 3:
            valid = valid.unsqueeze(1)

        self._validate_inputs(
            mlp_concat,
            mlp_latent,
            cnn_bottleneck,
            cnn_d0,
            mlp_logits,
            cnn_logits,
            valid,
        )

        valid = valid.float()

        # ---------------------------------------------------------------------
        # Flow 1 + Flow 2: global MLP knowledge
        # ---------------------------------------------------------------------
        k1 = self.flow1(mlp_concat)       # [B,256]
        k2 = self.flow2(mlp_latent)       # [B,128]

        global_knowledge = self.global_fusion(
            torch.cat([k1, k2], dim=1)
        )                                  # [B,256]

        # ---------------------------------------------------------------------
        # Flow 3 + Flow 4: CNN internal states
        # ---------------------------------------------------------------------
        s3 = self.flow3(cnn_bottleneck)   # [B,64,64,64]
        s4 = self.flow4(cnn_d0)           # [B,48,64,64]

        # ---------------------------------------------------------------------
        # Flow 5: disagreement state
        # ---------------------------------------------------------------------
        p_mlp = torch.sigmoid(mlp_logits)
        p_cnn = torch.sigmoid(cnn_logits)

        probability_disagreement = (
            torch.abs(p_cnn - p_mlp)
            * valid
        )

        scale = max(float(self.cfg.logit_diff_scale), 1e-6)
        bounded_logit_disagreement = (
            torch.tanh(
                torch.abs(cnn_logits - mlp_logits)
                / scale
            )
            * valid
        )

        disagreement_input = torch.cat(
            [
                probability_disagreement,
                bounded_logit_disagreement,
                valid,
            ],
            dim=1,
        )

        s5 = self.flow5(disagreement_input)  # [B,32,64,64]

        # ---------------------------------------------------------------------
        # Spatial fusion
        # ---------------------------------------------------------------------
        spatial_concat = torch.cat(
            [s3, s4, s5],
            dim=1,
        )

        spatial = self.spatial_merge(
            spatial_concat
        )                                    # [B,96,64,64]

        # FiLM: vector knowledge controls spatial interpretation.
        gamma_beta = self.film(global_knowledge)
        gamma, beta = torch.chunk(gamma_beta, 2, dim=1)

        gamma = gamma.unsqueeze(-1).unsqueeze(-1)
        beta = beta.unsqueeze(-1).unsqueeze(-1)

        spatial_conditioned = (
            (1.0 + gamma) * spatial
            + beta
        )

        master_map = self.post_film(
            spatial_conditioned
        )                                    # [B,64,64,64]

        # ---------------------------------------------------------------------
        # Interpretable final decision
        # ---------------------------------------------------------------------
        gate_logits = self.expert_gate_head(
            master_map
        )                                    # [B,2,64,64]

        expert_weights = torch.softmax(
            gate_logits,
            dim=1,
        )

        w_mlp = expert_weights[:, 0:1]
        w_cnn = expert_weights[:, 1:2]

        raw_residual = self.residual_head(
            master_map
        )

        residual_logits = (
            float(self.cfg.residual_logit_max)
            * torch.tanh(raw_residual)
        )

        mixed_logits = (
            w_mlp * mlp_logits
            + w_cnn * cnn_logits
        )

        logits = (
            mixed_logits
            + residual_logits
        )

        if not return_intermediates:
            return logits

        return {
            "logits": logits,
            "mixed_logits": mixed_logits,
            "mlp_weight": w_mlp,
            "cnn_weight": w_cnn,
            "gate_logits": gate_logits,
            "residual_logits": residual_logits,
            "raw_residual": raw_residual,

            "mlp_probability": p_mlp,
            "cnn_probability": p_cnn,
            "probability_disagreement": probability_disagreement,
            "bounded_logit_disagreement": bounded_logit_disagreement,

            "flow1_embedding": k1,
            "flow2_embedding": k2,
            "global_knowledge": global_knowledge,

            "flow3_spatial": s3,
            "flow4_spatial": s4,
            "flow5_spatial": s5,
            "spatial_pre_film": spatial,
            "spatial_conditioned": spatial_conditioned,
            "master_map": master_map,
        }

    @torch.no_grad()
    def predict_probability(
        self,
        *,
        valid: torch.Tensor | None = None,
        **kwargs,
    ) -> torch.Tensor:
        logits = self.forward(
            valid=valid,
            **kwargs,
        )
        prob = torch.sigmoid(logits)

        if valid is not None:
            if valid.ndim == 3:
                valid = valid.unsqueeze(1)
            prob = prob * valid.float()

        return prob


# =============================================================================
# LOSSES / METRICS HELPERS
# =============================================================================

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

    pixel_loss = F.binary_cross_entropy_with_logits(
        logits,
        target,
        reduction="none",
    )

    return (
        (pixel_loss * valid).sum()
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

    prob = torch.sigmoid(logits) * valid
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


def gate_supervision_loss(
    outputs: Dict[str, torch.Tensor],
    target: torch.Tensor,
    valid: torch.Tensor,
    temperature: float = 0.15,
    eps: float = 1e-6,
) -> torch.Tensor:
    """
    Softly teach the gate which frozen Engineer is closer to GT at each pixel.

        e_m = |P_m - GT|
        e_c = |P_c - GT|
        q   = softmax([-e_m/T, -e_c/T])

    The target is intentionally soft; final segmentation loss is still the
    primary objective and can override the gate proxy where useful.
    """
    target = _b1hw(target, "target").float()
    valid = _b1hw(valid, "valid").float()

    p_m = outputs["mlp_probability"].detach()
    p_c = outputs["cnn_probability"].detach()

    error_m = torch.abs(p_m - target)
    error_c = torch.abs(p_c - target)

    t = max(float(temperature), 1e-4)
    expert_scores = torch.cat(
        [-error_m / t, -error_c / t],
        dim=1,
    )

    soft_target = torch.softmax(
        expert_scores,
        dim=1,
    )

    log_weights = torch.log_softmax(
        outputs["gate_logits"],
        dim=1,
    )

    pixel_ce = -(
        soft_target * log_weights
    ).sum(dim=1, keepdim=True)

    return (
        (pixel_ce * valid).sum()
        / (valid.sum() + eps)
    )


def residual_penalty(
    outputs: Dict[str, torch.Tensor],
    valid: torch.Tensor,
    eps: float = 1e-6,
) -> torch.Tensor:
    valid = _b1hw(valid, "valid").float()
    delta = outputs["residual_logits"]

    return (
        ((delta * delta) * valid).sum()
        / (valid.sum() + eps)
    )


def engineer_master_v1_loss(
    outputs: Dict[str, torch.Tensor],
    gt_mask_64: torch.Tensor,
    valid_mask_64: torch.Tensor,
    *,
    dice_weight: float = 1.0,
    residual_penalty_weight: float = 0.01,
    gate_supervision_weight: float = 0.05,
    gate_target_temperature: float = 0.15,
) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    logits = outputs["logits"]

    gt = _b1hw(gt_mask_64, "gt_mask_64").float()
    valid = _b1hw(valid_mask_64, "valid_mask_64").float()
    gt = gt * valid

    bce = masked_bce_loss(
        logits,
        gt,
        valid,
    )

    dice = masked_dice_loss(
        logits,
        gt,
        valid,
    )

    segmentation = (
        bce
        + float(dice_weight) * dice
    )

    residual = residual_penalty(
        outputs,
        valid,
    )

    gate = gate_supervision_loss(
        outputs,
        gt,
        valid,
        temperature=gate_target_temperature,
    )

    total = (
        segmentation
        + float(residual_penalty_weight) * residual
        + float(gate_supervision_weight) * gate
    )

    parts = {
        "total": total.detach(),
        "segmentation": segmentation.detach(),
        "bce": bce.detach(),
        "dice_loss": dice.detach(),
        "residual_penalty": residual.detach(),
        "gate_loss": gate.detach(),
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


# =============================================================================
# SANITY CHECK
# =============================================================================

@torch.no_grad()
def architecture_sanity_check(batch_size: int = 2) -> None:
    cfg = EngineerMasterV1Config()
    model = EngineerMasterV1(cfg)
    model.eval()

    mlp_concat = torch.randn(
        batch_size,
        cfg.mlp_concat_dim,
    )
    mlp_latent = torch.randn(
        batch_size,
        cfg.mlp_latent_dim,
    )
    cnn_bottleneck = torch.randn(
        batch_size,
        cfg.cnn_bottleneck_channels,
        cfg.cnn_bottleneck_size,
        cfg.cnn_bottleneck_size,
    )
    cnn_d0 = torch.randn(
        batch_size,
        cfg.cnn_d0_channels,
        cfg.output_size,
        cfg.output_size,
    )
    mlp_logits = torch.randn(
        batch_size,
        1,
        cfg.output_size,
        cfg.output_size,
    )
    cnn_logits = torch.randn_like(mlp_logits)
    valid = (
        torch.rand_like(mlp_logits) > 0.1
    ).float()

    out = model(
        mlp_concat=mlp_concat,
        mlp_latent=mlp_latent,
        cnn_bottleneck=cnn_bottleneck,
        cnn_d0=cnn_d0,
        mlp_logits=mlp_logits,
        cnn_logits=cnn_logits,
        valid=valid,
        return_intermediates=True,
    )

    expected = {
        "flow1_embedding": (
            batch_size,
            cfg.flow1_out_dim,
        ),
        "flow2_embedding": (
            batch_size,
            cfg.flow2_out_dim,
        ),
        "global_knowledge": (
            batch_size,
            cfg.global_knowledge_dim,
        ),
        "flow3_spatial": (
            batch_size,
            cfg.flow3_out_channels,
            64,
            64,
        ),
        "flow4_spatial": (
            batch_size,
            cfg.flow4_channels,
            64,
            64,
        ),
        "flow5_spatial": (
            batch_size,
            cfg.flow5_out_channels,
            64,
            64,
        ),
        "master_map": (
            batch_size,
            cfg.master_map_channels,
            64,
            64,
        ),
        "mlp_weight": (
            batch_size,
            1,
            64,
            64,
        ),
        "cnn_weight": (
            batch_size,
            1,
            64,
            64,
        ),
        "residual_logits": (
            batch_size,
            1,
            64,
            64,
        ),
        "logits": (
            batch_size,
            1,
            64,
            64,
        ),
    }

    print("=" * 76)
    print("Engineer Master Fusion V1")
    print("=" * 76)

    for name, shape in expected.items():
        actual = tuple(out[name].shape)
        print(f"{name:28s}: {actual}")
        if actual != shape:
            raise RuntimeError(
                f"{name}: expected {shape}, got {actual}"
            )

    weight_sum_error = torch.max(
        torch.abs(
            out["mlp_weight"]
            + out["cnn_weight"]
            - 1.0
        )
    ).item()

    params = count_parameters(model)

    print()
    print(f"Weight-sum max error : {weight_sum_error:.3e}")
    print(f"Total parameters     : {params['total']:,}")
    print(f"Trainable parameters : {params['trainable']:,}")


if __name__ == "__main__":
    architecture_sanity_check()
