# v0.3.0 — Contour Extractor / Sampling LAB architectural split

## Decision

The previous Sampling / Geometry LAB is split into two user-facing LABs:

- **Contour Extractor LAB** owns contour candidate generation, early junk rejection, filtering, selection and final meaningful `ContourSet` output.
- **Sampling LAB** owns Spatial Sampling Units plus Spectral / Statistics feature extraction. The new editor does not build geometry/contours.

Legacy Sampling Geometry backend operators remain loadable so previously deployed v0.2 service snapshots continue to run.

## Contour memory model

Contour extraction can create tens of thousands of OpenCV candidates. v0.3 applies the default `EarlyContourFilter` immediately after candidate extraction. Rejected coordinates are not retained in the session.

Surviving coordinates are stored exactly once in `ContourStore`. Filter stages store only contour IDs/selections rather than cloning `ContourSet` coordinates. The UI retrieves contour metrics in pages and contour geometry lazily for inspection.

The editor exposes a memory funnel:

`candidate count -> rejected before store -> retained geometry -> stage selections -> final selection`

For BinaryMask upstream data, `auto` candidate mode uses direct mask boundaries; raster images default to Canny.

## Sampling Unit model

Spatial Sampling is no longer presented as one linear stack. Every unit is a compound tool:

`Housing (WHERE) + Data Extractor (WHAT/HOW) + Data Layout Composer`

Housing geometry is inspectable and can be hidden/shown with an eye toggle, but it is not exposed as the service result. Data extraction creates semantic `DataBlockSet` artifacts. The Layout Composer arranges those blocks into `ComposedData` by vector concatenation or matrix stacking, with element-major, channel-major or custom block order.

`ComposedData` is the public output normally exposed by a Spatial Sampling Unit.

## Pedagogy / inspection

Data extractor parameters include explanations for channel selection, histogram bins, standard deviation, sampling density and layout. The inspector renders Data Blocks, histograms, feature graphs and spectral graphs rather than falling back to the raw image.

FFT inspection supports inverse-FFT demonstrations for a radial frequency band, an angular sector, or a conjugate frequency pair. Global FFT is documented as answering **what frequencies exist**, not **where they occur**; local FFT / STFT / Gabor are future localization tools.

## Service lifecycle

Lab Service now exposes a delete endpoint and `/labs` includes a remove control. Contour Extractor pipelines can deploy as `lab_type=contour_extractor`; Sampling remains `lab_type=sampling_geometry` for compatibility, with new UI scope `spatial` or `spectral`.
