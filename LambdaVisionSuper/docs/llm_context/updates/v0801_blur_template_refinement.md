# Computer Vision v0.8.1 — Blur Template Localization Refinement

## Scope

Hotfix for the Computer Vision v0.8 Blur + Template Matching ROI locator. No UI or service-contract changes.

## Problem

A low-texture ROI can become nearly constant after Gaussian blur. In that case template matching has several nearly equivalent positions and the correlation peak can drift by a few pixels even though the object is correctly detected. The v0.8 regression case observed a 3 px Y offset.

## Fix

The locator now uses a coarse-to-fine strategy:

1. Detect whether the master ROI is low texture.
2. For low-texture ROIs, automatically include a context halo around the ROI so the object/background boundary contributes spatial information.
3. Run the configured Gaussian-blur template match for robust coarse localization.
4. Refine only around the coarse result using the original grayscale context for pixel-level edge alignment.
5. Translate the refined context coordinate back to the configured ROI coordinate before applying geometry constraints.

The public locator config remains unchanged. Existing saved programs remain compatible.

## Regression

The original filled-rectangle regression now localizes the shifted ROI at the expected position while a textured-template case verifies the normal matching path.
