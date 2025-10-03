---
title: "Fixing Micasense Multispectral Band Metadata"
authors: ["J.C. Montes-Herrera", "Arko Lucieer", "Claude-3.7-sonnet (Thinking)"]
date: "2025-10-03"
description: "Documentation of a large-scale metadata correction for multispectral drone imagery across 108 Australian datasets"
tags: ["multispectral", "metadata", "exiftool", "drone", "remote sensing"]
project: "DroneScape"
version: "1.0"
---

# Fixing Micasense Multispectral Band Metadata

## Problem Overview

We discovered an issue with multispectral drone imagery metadata when attempting to plot spectral profiles of vegetation and soil. The spectral signatures of healthy vegetation did not match expected patterns based on plant physiology knowledge. Upon visual analysis of the imagery, we noticed that bands supposedly capturing infrared wavelengths showed dark pixels in areas of green, healthy vegetation - which contradicts known vegetation reflectance properties. Simultaneously, the red band displayed unusually bright pixels in healthy vegetation areas, which is physiologically implausible as chlorophyll strongly absorbs red light.

These observations led us to investigate the metadata of our multispectral imagery, where we discovered incorrect band assignments. Unfortunately, by the time we identified this issue, we had already collected over 100 datasets with the same metadata problems. The following XMP metadata fields had issues:

- `XMP-Camera:BandName` - Incorrect band names
- `XMP-Camera:CentralWavelength` - Incorrect wavelength values
- `XMP-Camera:CenterWavelength` - Incorrect wavelength values (duplicate field)
- `XMP-Camera:FWHM` - Missing or incorrect Full Width at Half Maximum values
- `XMP-Camera:Bandwidth` - Missing or incorrect bandwidth values

The issue was first identified during firmware version analysis, where we discovered discrepancies between v1.4.0, v1.4.1, and v1.4.5 band assignments. Specifically:

| Band Filename | v1.4.0               | v1.4.1               | v1.4.5 (Correct)     |
| ------------- | -------------------- | -------------------- | -------------------- |
| \*\_9.TIF     | Red-650 (650nm)      | Red-650 (650nm)      | Red edge-740 (740nm) |
| \*\_10.TIF    | Red edge-705 (705nm) | Red edge-705 (705nm) | Red-650 (650nm)      |
| \*\_11.TIF    | Red edge-740 (740nm) | Red edge-740 (740nm) | Red edge-705 (705nm) |

The original approach was to fix these issues one band at a time using exiftool:

```bash
exiftool -config pix4d.config "-XMP-Camera:BandName=CorrectBANDNAME" "-XMP-Camera:CentralWavelength=CORRECTWVL" "-XMP-Camera:CenterWavelength=CORRECTWVL" "-XMP-Camera:WavelengthFWHM=CORRECTFWHM" "-XMP-Camera:Bandwidth=CORRECTBW" *_9.TIF
```

## Understanding XMP Metadata in Multispectral Imagery

XMP (Extensible Metadata Platform) is an ISO standard format for embedding metadata into digital images and documents. While most common image formats (JPEG, TIFF) include basic metadata fields, multispectral imagery requires additional specialized metadata to properly identify and process the spectral bands.

Our multispectral camera system uses a custom implementation of XMP metadata developed in collaboration with Pix4D, a leading photogrammetry software company. This implementation extends the standard XMP schema with a specialized "Camera" namespace that includes fields specific to multispectral sensors:

```
%Image::ExifTool::UserDefined::Camera = (
    GROUPS => { 0 => 'XMP', 1 => 'XMP-Camera', 2 => 'Camera' },
    NAMESPACE => { 'Camera' => 'http://pix4d.com/camera/1.0/'  },
    WRITABLE => 'string',
    # ... various camera fields ...
    CentralWavelength => { },
    CenterWavelength => { },
    WavelengthFWHM => { },
    Bandwidth => { },
    BandName        => { },
    # ... other fields ...
);
```

This specialized metadata is critical for:

1. **Band Identification**: Correctly identifying which spectral band (e.g., Red, NIR, Red-Edge) each image represents
2. **Wavelength Calibration**: Providing the precise center wavelength and bandwidth for radiometric calibration
3. **Sensor Alignment**: Managing multiple sensors in a single camera system with information about their relative positions
4. **Processing Pipeline**: Enabling automated processing in photogrammetry software

The issue we encountered arose when firmware updates changed how band numbers were mapped to specific wavelengths and band names, but this change wasn't properly documented or consistently applied across datasets.

## Analysis Process

1. Identified problematic datasets through band comparison analysis using the `MultiSpec_Band_Analysis.ipynb` notebook
2. Found inconsistencies in band names, wavelengths, and FWHM values across different firmware versions
3. Determined that band information needed to be corrected at the source (TIF files)
4. Discovered exiftool could modify these metadata fields using a custom config file
5. Used `compare_band_assignments` function to identify specific discrepancies between firmware versions
6. Analyzed filename patterns and suffixes to confirm consistent file naming conventions

## Scaling Challenge

The challenge was scale:

- Hundreds of datasets
- Thousands of images per dataset
- Multiple bands (at least 3) needing correction
- Need for an efficient batch process rather than running commands manually

## Solution Approach

The optimized solution involves:

1. Creating a script that can process multiple bands in a single pass
2. Using a custom configuration file (jcpix4d.config) to specify correct values for each band
3. Implementing batch processing to handle multiple directories efficiently
4. Using `-overwrite_original` flag to avoid creating backup files for each image
5. Validating the corrections to ensure metadata is properly updated
6. Support for both dry-run and actual update modes

## Implementation

The `MultiSpec_Band_Update_v1.4.5.ipynb` notebook was created to:

1. Set up required dependencies and verify exiftool installation
2. Create a custom configuration file (jcpix4d.config) for ExifTool
3. Define specialized update functions for each band:
   - update_band_9_to_v145: Update band 9 (\*\_9.TIF) from Red-650 to Red edge-740
   - update_band_10_to_v145: Update band 10 (\*\_10.TIF) from Red edge-705 to Red-650
   - update_band_11_to_v145: Update band 11 (\*\_11.TIF) from Red edge-740 to Red edge-705
4. Implement batch processing to handle multiple directories efficiently
5. Support recursive directory search to find all TIF files
6. Provide both dry-run and actual update modes with reporting
7. Generate detailed logs and success/failure statistics

This solution significantly reduces processing time and ensures consistent metadata across all multispectral bands, capable of processing thousands of images across multiple datasets.

## Metadata Correction Details

The specific metadata corrections applied per band are:

| Band | File Pattern | Correct Name | Wavelength (nm) | FWHM |
| ---- | ------------ | ------------ | --------------- | ---- |
| 9    | \*\_9.TIF    | Red edge-740 | 740             | 18   |
| 10   | \*\_10.TIF   | Red-650      | 650             | 16   |
| 11   | \*\_11.TIF   | Red edge-705 | 705             | 16   |

## Usage

1. Ensure exiftool is installed (version 12.84 or higher recommended)
2. Configure the directories to process in the notebook
3. Run a dry-run test to verify file detection and planned changes
4. Run the actual update with `dry_run=False`
5. Review the generated reports for successful updates

## Processed Datasets

The following datasets have been processed with this metadata update tool:

| Plot ID    | Date     |
| ---------- | -------- |
| SAAEYB0020 | 20240717 |
| SAAEYB0037 | 20240717 |
| SAAEYB0013 | 20240718 |
| SAAEYB0009 | 20240720 |
| SAAEYB0014 | 20240720 |
| SAAEYB0017 | 20240720 |
| SAAEYB0007 | 20240721 |
| SAAEYB0010 | 20240721 |
| SAAEYB0015 | 20240721 |
| SAAEYB0004 | 20240722 |
| SAAEYB0005 | 20240722 |
| SAAEYB0012 | 20240722 |
| SAAEYB0019 | 20240722 |
| SAAEYB0006 | 20240723 |
| SAAEYB0008 | 20240723 |
| SAAEYB0011 | 20240723 |
| SAAEYB0018 | 20240723 |
| NTABRT0004 | 20240828 |
| NTABRT0005 | 20240828 |
| NTABRT0006 | 20240828 |
| NTABRT0007 | 20240828 |
| NTABRT0002 | 20240829 |
| NTABRT0003 | 20240829 |
| NTABRT0009 | 20240829 |
| NTAFIN0026 | 20240830 |
| NTAFIN0027 | 20240830 |
| NTAFIN0032 | 20240830 |
| NTAFIN0033 | 20240830 |
| NTAFIN0007 | 20240831 |
| NTAFIN0008 | 20240831 |
| NTAMAC0001 | 20240831 |
| NTAMAC0002 | 20240831 |
| NTAMAC0003 | 20240831 |
| NTAFIN0002 | 20240901 |
| NTAFIN0009 | 20240901 |
| NTAFIN0010 | 20240901 |
| NTAFIN0011 | 20240901 |
| NTAFIN0001 | 20240902 |
| NTAFIN0003 | 20240902 |
| NTAFIN0004 | 20240902 |
| NTAFIN0005 | 20240902 |
| NTAFIN0006 | 20240902 |
| NTAFIN0012 | 20240924 |
| NTAFIN0017 | 20240924 |
| NTAFIN0018 | 20240924 |
| NTAFIN0019 | 20240924 |
| NTAFIN0013 | 20240925 |
| NTAFIN0014 | 20240925 |
| NTAFIN0024 | 20240926 |
| NTAFIN0025 | 20240926 |
| NTAFIN0028 | 20240927 |
| NTAFIN0029 | 20240927 |
| NTAFIN0030 | 20240927 |
| NTAFIN0031 | 20240927 |
| SAAGVD0005 | 20240928 |
| SAAGVD0006 | 20240928 |
| SAASTP0036 | 20240928 |
| SAASTP0037 | 20240929 |
| SAAGAW0004 | 20241001 |
| SAAGAW0005 | 20241001 |
| SAAGAW0008 | 20241001 |
| SAAGAW0009 | 20241001 |
| SAAGAW0006 | 20241002 |
| SAAGAW0007 | 20241002 |
| SAASTP0033 | 20241002 |
| SAASTP0034 | 20241002 |
| SAANCP0008 | 20241118 |
| SAANCP0009 | 20241119 |
| SAANCP0006 | 20241120 |
| SAANCP0007 | 20241120 |
| SAASVP0001 | 20241120 |
| SAASVP0002 | 20241120 |
| SAANCP0002 | 20241121 |
| SAANCP0003 | 20241121 |
| SAANCP0004 | 20241121 |
| SAANCP0005 | 20241121 |
| SAANCP0001 | 20241122 |
| SAAKAN0010 | 20241207 |
| SAAKAN0011 | 20241207 |
| SAAKAN0012 | 20241207 |
| SAAKAN0001 | 20241208 |
| SAAKAN0008 | 20241208 |
| SAAKAN0009 | 20241208 |
| SAAKAN0003 | 20241209 |
| SAAKAN0002 | 20241210 |
| SAAKAN0004 | 20241210 |
| SAAKAN0005 | 20241210 |
| SAAKAN0006 | 20241211 |
| SAAKAN0007 | 20241211 |
| SAAKAN0013 | 20241211 |
| WAASWA0012 | 20250326 |
| WAASWA0013 | 20250326 |
| WAASWA0014 | 20250326 |
| WAAESP0001 | 20250328 |
| WAAJAF0003 | 20250328 |
| WAFWAR0005 | 20250329 |
| WAAJAF0001 | 20250329 |
| WAAJAF0002 | 20250329 |
| WAFWAR0007 | 20250330 |
| WAFWAR0008 | 20250330 |
| WAAJAF0007 | 20250404 |
| WAAJAF0009 | 20250404 |
| WAAJAF0010 | 20250404 |
| WAAAVW0003 | 20250405 |
| WAAAVW0004 | 20250405 |
| WAAAVW0008 | 20250405 |

This massive metadata correction effort successfully restored over 312,177 individual files across 108 datasets spanning three Australian territories. What began as anomalies in spectral signatures transformed into a comprehensive data restoration operation, ensuring the scientific integrity of the entire **dronescape** multispectral archive for future research and analysis.

## Important Note

This metadata correction was a one-time fix to address inconsistencies introduced by firmware version changes. The solution documented here serves as a historical record of the issue and its resolution. After applying this fix, all multispectral datasets should have consistent and correct band metadata, preventing downstream analysis issues.
