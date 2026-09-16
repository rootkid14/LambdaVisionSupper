import type {
  OperatorManifest,
  ParameterManifest,
} from './types';

export interface OperatorGuide {
  overview: string;
  howItWorks: string;
  tuningTips: string[];
  notes: string[];
  parameterTips: Record<string, string>;
}

const categoryGuides: Record<string, Omit<OperatorGuide, 'parameterTips'>> = {
  'Color & Channels': {
    overview: 'Color/channel operators change how pixel values are represented without trying to decide whether an object is OK or NG.',
    howItWorks: 'The operator converts color space, extracts one channel, or remaps intensity values. These transforms are often used to expose contrast that is weak in the original representation.',
    tuningTips: [
      'Compare the result against the original image; color-space transforms can make one defect easier to isolate while hiding another.',
      'When extracting a channel, choose the channel that maximizes separation between foreground and background rather than the one that merely looks visually pleasing.',
    ],
    notes: [
      'Be aware of channel ordering: OpenCV commonly uses BGR while many display systems use RGB.',
      'HSV hue becomes unstable in very dark or weakly saturated regions.',
    ],
  },
  Enhancement: {
    overview: 'Enhancement operators reshape brightness or local/global contrast so downstream filters receive a cleaner intensity distribution.',
    howItWorks: 'They apply point transforms or histogram-based remapping. They do not create new image information; they redistribute the information already present.',
    tuningTips: [
      'Tune while watching both the defect and the background. Too much enhancement amplifies noise and texture.',
      'Prefer local enhancement such as CLAHE when illumination varies spatially; prefer global transforms when lighting is already uniform.',
    ],
    notes: [
      'Aggressive contrast enhancement can make thresholding easier but can also create false edges.',
    ],
  },
  'Smooth / Denoise': {
    overview: 'Smoothing filters suppress pixel-level noise and small texture before thresholding, edge extraction, or segmentation.',
    howItWorks: 'A neighborhood around each pixel contributes to the output. Different filters use different weighting rules and differ in how strongly they preserve edges.',
    tuningTips: [
      'Increase kernel/radius only until nuisance noise is removed; larger neighborhoods erase small defects.',
      'Median filtering is strong against impulse noise; Gaussian filtering is a good general-purpose low-pass filter; bilateral filtering preserves edges better but costs more.',
    ],
    notes: [
      'Kernel size is effectively a spatial scale. Pick it relative to the smallest feature you must preserve.',
    ],
  },
  'Edge-preserving Filter': {
    overview: 'Edge-preserving filters smooth flat regions while trying to avoid mixing pixels across strong boundaries.',
    howItWorks: 'They adapt the amount of smoothing to local structure, using a guide image, intensity difference, or diffusion coefficient.',
    tuningTips: [
      'Start with conservative smoothing and increase radius/iterations gradually.',
      'If thin structures disappear, reduce radius, iteration count, or the diffusion strength.',
    ],
    notes: [
      'These filters are usually slower than Gaussian/box blur but can preserve metrology-relevant boundaries much better.',
    ],
  },
  'Sharpen / Detail': {
    overview: 'Sharpening boosts local high-frequency detail and edge contrast.',
    howItWorks: 'The operator estimates a high-frequency component and adds it back to the image, or uses derivatives such as Laplacian.',
    tuningTips: [
      'Increase strength slowly. Halo artifacts are a sign that sharpening is too aggressive.',
      'Denoise first if the image contains strong sensor noise, because sharpening also amplifies noise.',
    ],
    notes: [
      'Sharpening improves visibility but does not recover detail that was never captured.',
    ],
  },
  'Threshold / Binarize': {
    overview: 'Threshold operators convert intensity information into a foreground/background mask.',
    howItWorks: 'Pixels are classified according to a global or local threshold. Adaptive variants estimate a threshold from the neighborhood around each pixel.',
    tuningTips: [
      'Check whether the foreground should be bright or dark and use invert accordingly.',
      'If illumination varies across the image, use an adaptive method or correct illumination first.',
    ],
    notes: [
      'A good threshold mask usually benefits from morphology afterward, but morphology should not be used to hide a fundamentally poor threshold.',
    ],
  },
  'Advanced Binarization': {
    overview: 'Advanced local threshold methods handle uneven background and changing local contrast better than one global threshold.',
    howItWorks: 'A local mean and often local standard deviation are computed for each neighborhood, then combined into a pixel-wise threshold surface.',
    tuningTips: [
      'Window size should be larger than the local feature width but smaller than the scale of illumination drift.',
      'Tune the sensitivity/k term after the window size. Reversing that order often leads to unstable settings.',
    ],
    notes: [
      'Large windows increase computation and can behave almost like a global threshold.',
    ],
  },
  'Edge / Gradient': {
    overview: 'Gradient operators measure how quickly intensity changes and are commonly used to reveal object boundaries.',
    howItWorks: 'Spatial derivatives are estimated in X/Y directions or combined into magnitude. Canny additionally performs suppression and hysteresis thresholding.',
    tuningTips: [
      'Smooth noisy images before derivative filters.',
      'For Canny, lower threshold admits more weak edges; upper threshold controls strong edge seeds.',
    ],
    notes: [
      'Edges describe boundaries, not filled regions. Use a mask/segmentation operator if downstream logic needs object area.',
    ],
  },
  'Ridge / Structure': {
    overview: 'Ridge filters enhance long line-like or tube-like structures rather than simple boundaries.',
    howItWorks: 'Second-order derivatives (Hessian eigenvalues) describe local curvature. Multi-scale methods repeat the measurement across several spatial scales and keep the strongest ridge response.',
    tuningTips: [
      'Match sigma to approximately half the structure width you want to enhance.',
      'For multi-scale filters, keep the sigma range as narrow as practical; a very broad range increases runtime and may highlight unrelated structures.',
      'Choose bright/dark polarity based on whether the target ridge is lighter or darker than its surroundings.',
    ],
    notes: [
      'Ridge response is usually a confidence-like grayscale image, not a final binary mask.',
    ],
  },
  'Morphology / Mask': {
    overview: 'Morphology changes binary shapes using a structuring element.',
    howItWorks: 'Erosion shrinks foreground, dilation grows it, and compound operations combine both to remove small structures or close gaps.',
    tuningTips: [
      'Kernel size should correspond to the defect/gap scale you intend to remove or bridge.',
      'Prefer the smallest kernel that solves the topology problem; morphology can distort geometry.',
    ],
    notes: [
      'Apply morphology to a meaningful mask. It cannot recover a badly segmented foreground reliably.',
    ],
  },
  'Morphological Reconstruction': {
    overview: 'Morphological reconstruction removes or fills structures while preserving the geometry of surviving regions better than ordinary opening/closing.',
    howItWorks: 'A marker image is repeatedly dilated under the constraint of a mask image until the result becomes stable.',
    tuningTips: [
      'Use reconstruction when normal opening/closing changes contour shape too much.',
      'Kernel size controls which structures survive the initial erosion/dilation.',
    ],
    notes: [
      'Reconstruction can require multiple internal iterations, so very large images may take longer than simple morphology.',
    ],
  },
  'Distance / Skeleton': {
    overview: 'Distance and thinning operators convert a binary region into structural raster representations such as thickness fields or one-pixel skeletons.',
    howItWorks: 'Distance transform measures distance to the nearest background boundary. Skeleton/thinning repeatedly removes boundary pixels while preserving topology.',
    tuningTips: [
      'Clean the binary mask before skeletonization; small branches and holes become skeleton artifacts.',
      'For Zhang-Suen, runtime grows with image size and foreground thickness because thinning is iterative.',
    ],
    notes: [
      'The output is still raster data. Ordered curves, graph cleanup, arc length, and sampling belong in the Geometry/Sampling LAB.',
    ],
  },
  'Frequency Domain': {
    overview: 'Frequency-domain filters represent the image as spatial frequencies so periodic patterns and scale-specific content can be isolated.',
    howItWorks: 'FFT converts the image into a complex spectrum. Frequency masks attenuate selected regions of that spectrum before inverse transformation.',
    tuningTips: [
      'Use FFT Magnitude Spectrum first to locate periodic peaks before configuring a notch filter.',
      'High-pass filters emphasize detail and noise; low-pass filters suppress both.',
    ],
    notes: [
      'Sharp ideal frequency masks can create ringing. Treat them as diagnostic/experimental tools unless the result is validated on production images.',
    ],
  },
  'Texture / Local Statistics': {
    overview: 'Texture operators measure local variation, orientation, entropy, or frequency content rather than only absolute brightness.',
    howItWorks: 'A neighborhood statistic or oriented filter is evaluated around each pixel to produce a texture-response image.',
    tuningTips: [
      'Select window size/wavelength near the physical scale of the texture or defect of interest.',
      'For Gabor filters, orientation and wavelength are usually more important than raw response gain.',
    ],
    notes: [
      'Texture responses often work best as an intermediate representation followed by thresholding or measurement.',
    ],
  },
  'Multiscale / Scale-space': {
    overview: 'Scale-space operators analyze structures at different spatial sizes.',
    howItWorks: 'Gaussian smoothing creates progressively coarser representations; DoG/LoG highlight structures that respond strongly at a selected scale.',
    tuningTips: [
      'Choose sigma based on feature diameter; a mismatch in scale suppresses the target.',
      'Use pyramid downsampling before expensive filters when full resolution is unnecessary.',
    ],
    notes: [
      'Pyramid operations change image dimensions, so remember that coordinates must be transformed if later reused.',
    ],
  },
  'Classical Segmentation': {
    overview: 'Classical segmentation groups pixels into coherent regions using connectivity, color similarity, or foreground/background models.',
    howItWorks: 'The exact mechanism depends on the operator: flood fill grows from a seed, GrabCut estimates foreground/background distributions, and K-Means clusters pixel colors.',
    tuningTips: [
      'Segmentation quality depends heavily on initialization and image representation.',
      'Use a cropped ROI when possible; smaller search regions improve both speed and robustness.',
    ],
    notes: [
      'These methods do not understand object semantics in the way a trained AI model does.',
    ],
  },
  Transform: {
    overview: 'Geometric raster transforms change image size, orientation, position, or crop.',
    howItWorks: 'Pixel coordinates are remapped to a new coordinate system and resampled.',
    tuningTips: [
      'Avoid repeated resize/rotate chains when one transform can do the job; every resampling step can blur the image.',
      'Use normalized crop coordinates when a pipeline must remain resolution-independent.',
    ],
    notes: [
      'Transforms can change coordinate meaning. Preserve transform metadata when downstream geometry depends on original image coordinates.',
    ],
  },
  Restoration: {
    overview: 'Restoration operators attempt to reverse a known or assumed image degradation process.',
    howItWorks: 'For Wiener deconvolution, an estimated point-spread function and noise level are used in the frequency domain to suppress blur while controlling noise amplification.',
    tuningTips: [
      'Start with a realistic blur kernel/PSF size rather than maximizing sharpness.',
      'If ringing/noise explodes, increase the assumed noise power or reduce the PSF size.',
    ],
    notes: [
      'Restoration is only as good as the degradation model. Wrong PSF assumptions can make the result worse.',
    ],
  },
  Arithmetic: {
    overview: 'Arithmetic operators apply direct numerical transforms to pixel values.',
    howItWorks: 'Each pixel is modified by a scalar or another raster according to the selected arithmetic rule.',
    tuningTips: [
      'Watch for clipping at 0 and 255.',
      'Use these operators for normalization or controlled intensity shifts, not as a substitute for illumination correction.',
    ],
    notes: [
      'Multi-image comparison semantics belong outside the pure Image Processing LAB.',
    ],
  },
};

const parameterTip = (
  name: string,
  spec: ParameterManifest,
): string => {
  const key = name.toLowerCase();

  if (key.includes('kernel')) {
    return 'Spatial neighborhood size. Larger values produce stronger/coarser effects and cost more computation.';
  }

  if (key === 'sigma' || key.includes('sigma_')) {
    return 'Spatial scale. Increase it to respond to wider structures or broader illumination/noise variation.';
  }

  if (key.includes('threshold')) {
    return 'Decision level. Lower values generally admit more pixels/edges; higher values are more selective.';
  }

  if (key === 'window_size') {
    return 'Local neighborhood size. It should be larger than the feature but smaller than the illumination/background variation scale.';
  }

  if (key === 'iterations' || key.endsWith('_iterations') || key === 'max_iterations') {
    return 'Number of repeated refinement steps. More iterations can strengthen the effect but increase runtime.';
  }

  if (key === 'k' || key === 'sensitivity') {
    return 'Controls how aggressively local statistics shift the decision threshold. Tune after choosing a reasonable window size.';
  }

  if (key === 'gamma') {
    return 'Nonlinearity/response control. Around 1 is neutral for gamma correction; interpretation may differ for other operators.';
  }

  if (key.includes('radius')) {
    return 'Neighborhood or rejection radius. Larger values affect a wider spatial/frequency region.';
  }

  if (key.includes('cutoff')) {
    return 'Normalized frequency boundary. Smaller values focus on slower spatial variation; larger values admit finer detail.';
  }

  if (key.includes('theta') || key.includes('angle')) {
    return 'Orientation in degrees. Match this to the dominant direction of the target structure.';
  }

  if (key.includes('wavelength')) {
    return 'Preferred texture period. Set it near the spacing of the repeated pattern you want the filter to respond to.';
  }

  if (key === 'clip_limit') {
    return 'Limits local contrast amplification. Higher values enhance more strongly but can amplify noise.';
  }

  if (key === 'tile_grid') {
    return 'Number/size of local CLAHE regions. More/smaller regions adapt more locally but may create uneven contrast.';
  }

  if (key === 'kappa') {
    return 'Edge sensitivity for anisotropic diffusion. Larger values allow diffusion across stronger intensity differences.';
  }

  if (key === 'connectivity') {
    return 'Defines which neighboring pixels belong to the same region: 4-connectivity excludes diagonals; 8-connectivity includes them.';
  }

  if (key.startsWith('seed_')) {
    return 'Normalized seed location used to start region growing. Place it well inside the intended region.';
  }

  if (['x', 'y', 'width', 'height'].includes(key)) {
    return 'Normalized geometry parameter in the 0..1 image coordinate system.';
  }

  if (key.includes('psf')) {
    return 'Parameter of the assumed blur point-spread function used by the restoration model.';
  }

  if (key === 'invert') {
    return 'Swap foreground/background interpretation.';
  }

  if (spec.choices?.length) {
    return `Select one of the supported modes: ${spec.choices.map(String).join(', ')}.`;
  }

  return spec.description || 'Adjust this parameter and compare the standalone result against the original input.';
};

const specialGuides: Record<string, Partial<OperatorGuide>> = {
  'image.threshold.bradley': {
    howItWorks: 'Bradley compares each pixel against a fraction of its local mean. This makes it fast and useful when the background intensity changes gradually across the image.',
    tuningTips: [
      'Choose window size first. It should be comfortably larger than the foreground stroke/feature width.',
      'Increase sensitivity when foreground is not being captured; reduce it when background becomes foreground.',
      'If local lighting changes are very slow, try illumination correction before Bradley rather than using an excessively large window.',
    ],
  },
  'image.skeleton.zhang_suen': {
    howItWorks: 'Zhang-Suen thinning removes eligible foreground boundary pixels in two alternating sub-steps while preserving connectivity until the mask reaches an approximately one-pixel-wide skeleton.',
    tuningTips: [
      'Clean isolated blobs and fill unwanted holes before thinning.',
      'Crop to the smallest useful ROI before running; this algorithm is iterative and full-frame masks can be expensive.',
      'If many spurs appear, the problem is usually in the input mask rather than the thinning parameter.',
    ],
    notes: [
      'This operator extracts a raster skeleton only. Main-path selection and branch pruning should be handled later in Geometry/Sampling.',
    ],
  },
  'image.structure.frangi_ridge': {
    howItWorks: 'Frangi evaluates Hessian eigenvalues across multiple Gaussian scales and keeps responses that resemble elongated ridge/tube structures.',
    tuningTips: [
      'Estimate target line half-width and center sigma_min/sigma_max around that scale.',
      'Use as few scales as necessary for production speed.',
      'Wrong polarity can suppress the target almost completely.',
    ],
  },
  'image.frequency.notch_reject': {
    tuningTips: [
      'Run FFT Magnitude Spectrum first and locate the symmetric pair of unwanted frequency peaks.',
      'Keep the notch radius as small as possible to avoid removing useful neighboring frequencies.',
    ],
  },
  'image.filter.guided': {
    tuningTips: [
      'Radius sets the spatial support; epsilon controls how strongly edges are preserved.',
      'If edges become blurred, reduce radius or epsilon.',
    ],
  },
  'image.illumination.shading_correction': {
    tuningTips: [
      'Background sigma must be much larger than the defect/feature size so the estimated background does not absorb the target.',
      'Use strength below 1 when full correction makes the image look over-normalized.',
    ],
  },
};

export const buildOperatorGuide = (
  operator: OperatorManifest,
): OperatorGuide => {
  const base = categoryGuides[operator.category] ?? {
    overview: operator.description || 'This operator transforms an image or mask into another raster representation.',
    howItWorks: operator.description || 'The operator applies its algorithm to the input raster using the parameters shown on the right.',
    tuningTips: [
      'Change one parameter at a time and compare the result against the same input image.',
      'Use the smallest amount of processing that makes the downstream task robust.',
    ],
    notes: [
      'Validate settings across multiple representative production images before deployment.',
    ],
  };

  const special = specialGuides[operator.id] ?? {};
  const parameterTips = Object.fromEntries(
    Object.entries(operator.parameters ?? {}).map(
      ([name, spec]) => [name, parameterTip(name, spec)],
    ),
  );

  return {
    overview: special.overview ?? operator.description ?? base.overview,
    howItWorks: special.howItWorks ?? base.howItWorks,
    tuningTips: special.tuningTips ?? base.tuningTips,
    notes: special.notes ?? base.notes,
    parameterTips,
  };
};
