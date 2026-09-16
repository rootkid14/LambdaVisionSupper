"""
Engineer MLP V2 - e5204
=======================

Input: [B, 5204]
    engineered: first 1108D
    spatial:    final 4096D normalized 64x64 Lab-L map

Output logits: [B, 1, 64, 64]

Architecture:
    engineered 1108 -> Specialized -> 576D
    engineered 1108 -> Holistic    -> 576D
    spatial    4096 -> 1024 -> 768 -> 576D
    concat           -> 1728D
    residual fusion  -> 512D
    residual reasoning x2 -> 512D
    latent           -> 256D
    coarse + fine decoder -> 64x64 logits

Specialized and Holistic keep their original 1108D input contract.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class EngineerMLPConfig:
    # Input feature families
    global_dim: int = 48
    grid_dim: int = 128
    profile_dim: int = 384
    radial_dim: int = 384
    edge_dim: int = 64
    valid_dim: int = 100

    # Specialized path output sizes
    global_embed_dim: int = 48
    grid_embed_dim: int = 96
    profile_embed_dim: int = 160
    radial_embed_dim: int = 160
    edge_embed_dim: int = 48
    valid_embed_dim: int = 64

    # Holistic path over engineered 1108D only
    holistic_hidden_dim: int = 768
    holistic_embed_dim: int = 576

    # Spatial branch over normalized 64x64 L-map
    spatial_dim: int = 4096
    spatial_hidden_dim1: int = 1024
    spatial_hidden_dim2: int = 768
    spatial_embed_dim: int = 576

    # Fusion / reasoning
    fusion_hidden_dim: int = 768
    fusion_dim: int = 512
    num_residual_blocks: int = 2
    residual_hidden_dim: int = 512

    # Latent
    latent_dim: int = 256

    # Decoder
    coarse_size: int = 16
    output_size: int = 64
    fine_hidden_dim: int = 512

    # Regularization
    dropout: float = 0.08

    @property
    def engineered_dim(self) -> int:
        return (
            self.global_dim
            + self.grid_dim
            + self.profile_dim
            + self.radial_dim
            + self.edge_dim
            + self.valid_dim
        )

    @property
    def input_dim(self) -> int:
        return self.engineered_dim + self.spatial_dim

    @property
    def specialized_dim(self) -> int:
        return (
            self.global_embed_dim
            + self.grid_embed_dim
            + self.profile_embed_dim
            + self.radial_embed_dim
            + self.edge_embed_dim
            + self.valid_embed_dim
        )


class FeatureEncoder(nn.Module):
    """Encoder for one handcrafted feature family."""

    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
            nn.LayerNorm(output_dim),
            nn.GELU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ResidualMLPBlock(nn.Module):
    """y = LayerNorm(x + F(x))."""

    def __init__(self, dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.norm_in = nn.LayerNorm(dim)
        self.residual = nn.Sequential(
            nn.Linear(dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, dim),
            nn.Dropout(dropout),
        )
        self.norm_out = nn.LayerNorm(dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        correction = self.residual(self.norm_in(x))
        return self.norm_out(x + correction)


class ResidualFusion(nn.Module):
    """
    Inspired by Add & Norm:

        u = concat(specialized, holistic, spatial)  # 1728D
        main = MLP(u)                          # 512D
        shortcut = Linear(u)                   # 512D
        fused = LayerNorm(shortcut + main)
    """

    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, dropout: float):
        super().__init__()
        self.norm_in = nn.LayerNorm(input_dim)
        self.main = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
            nn.Dropout(dropout),
        )
        self.shortcut = nn.Linear(input_dim, output_dim)
        self.norm_out = nn.LayerNorm(output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        u = self.norm_in(x)
        return self.norm_out(self.shortcut(u) + self.main(u))


class EngineerMLP(nn.Module):
    def __init__(self, cfg: EngineerMLPConfig = EngineerMLPConfig()):
        super().__init__()
        self.cfg = cfg

        if cfg.engineered_dim != 1108:
            raise ValueError(
                f"Expected 1108D engineered input, got {cfg.engineered_dim}D"
            )
        if cfg.spatial_dim != 4096:
            raise ValueError(
                f"Expected 4096D spatial input, got {cfg.spatial_dim}D"
            )
        if cfg.input_dim != 5204:
            raise ValueError(
                f"Expected 5204D total input, got {cfg.input_dim}D"
            )
        if cfg.specialized_dim != 576:
            raise ValueError(f"Expected 576D specialized embedding, got {cfg.specialized_dim}D")

        # Specialized / family path
        self.global_encoder = FeatureEncoder(cfg.global_dim, 64, cfg.global_embed_dim, cfg.dropout)
        self.grid_encoder = FeatureEncoder(cfg.grid_dim, 128, cfg.grid_embed_dim, cfg.dropout)
        self.profile_encoder = FeatureEncoder(cfg.profile_dim, 256, cfg.profile_embed_dim, cfg.dropout)
        self.radial_encoder = FeatureEncoder(cfg.radial_dim, 256, cfg.radial_embed_dim, cfg.dropout)
        self.edge_encoder = FeatureEncoder(cfg.edge_dim, 64, cfg.edge_embed_dim, cfg.dropout)
        self.valid_encoder = FeatureEncoder(cfg.valid_dim, 96, cfg.valid_embed_dim, cfg.dropout)

        # Holistic path: still sees ONLY the original engineered 1108D.
        self.holistic_encoder = nn.Sequential(
            nn.Linear(cfg.engineered_dim, cfg.holistic_hidden_dim),
            nn.LayerNorm(cfg.holistic_hidden_dim),
            nn.GELU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.holistic_hidden_dim, cfg.holistic_embed_dim),
            nn.LayerNorm(cfg.holistic_embed_dim),
            nn.GELU(),
        )

        # Third path: exact normalized spatial arrangement.
        self.spatial_encoder = nn.Sequential(
            nn.Linear(cfg.spatial_dim, cfg.spatial_hidden_dim1),
            nn.LayerNorm(cfg.spatial_hidden_dim1),
            nn.GELU(),
            nn.Dropout(cfg.dropout),

            nn.Linear(cfg.spatial_hidden_dim1, cfg.spatial_hidden_dim2),
            nn.LayerNorm(cfg.spatial_hidden_dim2),
            nn.GELU(),
            nn.Dropout(cfg.dropout),

            nn.Linear(cfg.spatial_hidden_dim2, cfg.spatial_embed_dim),
            nn.LayerNorm(cfg.spatial_embed_dim),
            nn.GELU(),
        )

        # Triple-path fusion: 576 + 576 + 576 = 1728.
        tri_dim = (
            cfg.specialized_dim
            + cfg.holistic_embed_dim
            + cfg.spatial_embed_dim
        )
        self.fusion = ResidualFusion(
            input_dim=tri_dim,
            hidden_dim=cfg.fusion_hidden_dim,
            output_dim=cfg.fusion_dim,
            dropout=cfg.dropout,
        )

        # Residual reasoning
        self.reasoning = nn.Sequential(*[
            ResidualMLPBlock(
                dim=cfg.fusion_dim,
                hidden_dim=cfg.residual_hidden_dim,
                dropout=cfg.dropout,
            )
            for _ in range(cfg.num_residual_blocks)
        ])

        # Latent station representation
        self.latent_head = nn.Sequential(
            nn.Linear(cfg.fusion_dim, cfg.latent_dim),
            nn.LayerNorm(cfg.latent_dim),
            nn.GELU(),
        )

        # Coarse mask head: 256 -> 16x16
        self.coarse_head = nn.Linear(cfg.latent_dim, cfg.coarse_size * cfg.coarse_size)

        # Fine residual head: 256 -> 512 -> 64x64
        self.fine_head = nn.Sequential(
            nn.Linear(cfg.latent_dim, cfg.fine_hidden_dim),
            nn.LayerNorm(cfg.fine_hidden_dim),
            nn.GELU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.fine_hidden_dim, cfg.output_size * cfg.output_size),
        )

    def split_features(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        if x.ndim != 2:
            raise ValueError(f"Input must be [B, 5204], got {tuple(x.shape)}")
        if x.shape[1] != self.cfg.input_dim:
            raise ValueError(f"Expected {self.cfg.input_dim} features, got {x.shape[1]}")

        c = self.cfg
        p = 0
        out = {}

        out["global"] = x[:, p:p + c.global_dim]; p += c.global_dim
        out["grid"] = x[:, p:p + c.grid_dim]; p += c.grid_dim
        out["profile"] = x[:, p:p + c.profile_dim]; p += c.profile_dim
        out["radial"] = x[:, p:p + c.radial_dim]; p += c.radial_dim
        out["edge"] = x[:, p:p + c.edge_dim]; p += c.edge_dim
        out["valid"] = x[:, p:p + c.valid_dim]; p += c.valid_dim
        out["spatial"] = x[:, p:p + c.spatial_dim]; p += c.spatial_dim

        if p != c.input_dim:
            raise RuntimeError(f"Feature split ended at {p}, expected {c.input_dim}")

        return out

    def forward(self, x: torch.Tensor, return_intermediates: bool = False):
        f = self.split_features(x)

        # Path A: specialized encoders
        specialized = torch.cat([
            self.global_encoder(f["global"]),
            self.grid_encoder(f["grid"]),
            self.profile_encoder(f["profile"]),
            self.radial_encoder(f["radial"]),
            self.edge_encoder(f["edge"]),
            self.valid_encoder(f["valid"]),
        ], dim=1)  # [B, 576]

        # Path B: holistic encoder over original engineered 1108D.
        engineered = x[:, :self.cfg.engineered_dim]
        holistic = self.holistic_encoder(engineered)  # [B, 576]

        # Path C: spatial encoder over normalized 64x64 L-map.
        spatial = self.spatial_encoder(f["spatial"])  # [B, 576]

        # Triple-path fusion.
        tri = torch.cat([specialized, holistic, spatial], dim=1)  # [B, 1728]
        fused = self.fusion(tri)                                  # [B, 512]
        refined = self.reasoning(fused)                   # [B, 512]

        # Latent
        latent = self.latent_head(refined)                # [B, 256]

        # Coarse logits
        coarse_logits = self.coarse_head(latent).view(
            -1, 1, self.cfg.coarse_size, self.cfg.coarse_size
        )

        # Fine residual logits
        fine_residual_logits = self.fine_head(latent).view(
            -1, 1, self.cfg.output_size, self.cfg.output_size
        )

        # Coarse-to-fine reconstruction
        coarse_up = F.interpolate(
            coarse_logits,
            size=(self.cfg.output_size, self.cfg.output_size),
            mode="bilinear",
            align_corners=False,
        )
        logits = coarse_up + fine_residual_logits

        if not return_intermediates:
            return logits

        return {
            "logits": logits,
            "coarse_logits": coarse_logits,
            "fine_residual_logits": fine_residual_logits,
            "latent": latent,
            "specialized": specialized,
            "holistic": holistic,
            "spatial": spatial,
            "fused": fused,
            "refined": refined,
        }

    @torch.no_grad()
    def predict_probability(self, x: torch.Tensor, valid_mask: Optional[torch.Tensor] = None):
        prob = torch.sigmoid(self.forward(x))
        if valid_mask is not None:
            prob = prob * valid_mask.float()
        return prob

    @torch.no_grad()
    def predict_mask(
        self,
        x: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
        threshold: float = 0.5,
    ):
        prob = self.predict_probability(x, valid_mask=valid_mask)
        return (prob >= threshold).to(torch.uint8)


# ---------------------------------------------------------------------
# Losses
# ---------------------------------------------------------------------

def masked_bce_loss(logits, target, valid_mask, eps: float = 1e-6):
    target = target.float()
    valid_mask = valid_mask.float()
    pixel_loss = F.binary_cross_entropy_with_logits(logits, target, reduction="none")
    return (pixel_loss * valid_mask).sum() / (valid_mask.sum() + eps)


def masked_dice_loss(logits, target, valid_mask, eps: float = 1e-6):
    prob = torch.sigmoid(logits)
    target = target.float()
    valid_mask = valid_mask.float()

    prob = prob * valid_mask
    target = target * valid_mask

    dims = (1, 2, 3)
    intersection = (prob * target).sum(dim=dims)
    denominator = prob.sum(dim=dims) + target.sum(dim=dims)
    dice = (2.0 * intersection + eps) / (denominator + eps)
    return 1.0 - dice.mean()


def engineer_loss(
    outputs: Dict[str, torch.Tensor],
    gt_mask_64: torch.Tensor,
    valid_mask_64: torch.Tensor,
    dice_weight: float = 1.0,
    coarse_weight: float = 0.20,
) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    logits = outputs["logits"]
    coarse_logits = outputs["coarse_logits"]

    gt_mask_64 = gt_mask_64.float()
    valid_mask_64 = valid_mask_64.float()

    fine_bce = masked_bce_loss(logits, gt_mask_64, valid_mask_64)
    fine_dice = masked_dice_loss(logits, gt_mask_64, valid_mask_64)
    fine_loss = fine_bce + dice_weight * fine_dice

    coarse_size = coarse_logits.shape[-2:]
    coarse_gt = F.interpolate(gt_mask_64, size=coarse_size, mode="nearest")
    coarse_valid = F.interpolate(valid_mask_64, size=coarse_size, mode="area")

    coarse_bce = masked_bce_loss(coarse_logits, coarse_gt, coarse_valid)
    coarse_dice = masked_dice_loss(coarse_logits, coarse_gt, coarse_valid)
    coarse_loss = coarse_bce + dice_weight * coarse_dice

    total = fine_loss + coarse_weight * coarse_loss

    parts = {
        "total": total.detach(),
        "fine_bce": fine_bce.detach(),
        "fine_dice": fine_dice.detach(),
        "coarse_bce": coarse_bce.detach(),
        "coarse_dice": coarse_dice.detach(),
    }
    return total, parts


def count_parameters(model: nn.Module) -> Dict[str, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total": total, "trainable": trainable}


def sanity_check():
    cfg = EngineerMLPConfig()
    model = EngineerMLP(cfg)

    B = 4
    x = torch.randn(B, cfg.input_dim)
    gt = torch.randint(0, 2, (B, 1, 64, 64)).float()
    valid = torch.ones_like(gt)

    outputs = model(x, return_intermediates=True)
    loss, parts = engineer_loss(outputs, gt, valid)
    params = count_parameters(model)

    print("Input:           ", tuple(x.shape))
    print("Specialized:     ", tuple(outputs["specialized"].shape))
    print("Holistic:        ", tuple(outputs["holistic"].shape))
    print("Fused:           ", tuple(outputs["fused"].shape))
    print("Latent:          ", tuple(outputs["latent"].shape))
    print("Coarse logits:   ", tuple(outputs["coarse_logits"].shape))
    print("Final logits:    ", tuple(outputs["logits"].shape))
    print(f"Total parameters: {params['total']:,}")
    print(f"Loss:             {float(loss):.6f}")
    for k, v in parts.items():
        print(f"{k:16s}: {float(v):.6f}")


if __name__ == "__main__":
    sanity_check()