#!/usr/bin/env node
/**
 * Day 4: Pixel-Diff Comparison using pixelmatch
 *
 * This script compares two PNG images pixel-by-pixel and returns:
 * - Number of different pixels
 * - Similarity percentage
 * - Diff visualization image (optional)
 */

const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');
const pixelmatch = require('pixelmatch');

/**
 * Compare two images and return similarity metrics
 */
function compareImages(img1Path, img2Path, diffOutputPath = null) {
  try {
    // Read both images
    const img1 = PNG.sync.read(fs.readFileSync(img1Path));
    const img2 = PNG.sync.read(fs.readFileSync(img2Path));

    // Verify dimensions match
    const { width, height } = img1;
    if (img2.width !== width || img2.height !== height) {
      throw new Error(
        `Image dimensions don't match: ${width}x${height} vs ${img2.width}x${img2.height}`
      );
    }

    // Create diff image
    const diff = new PNG({ width, height });

    // Run pixelmatch
    const numDiffPixels = pixelmatch(
      img1.data,
      img2.data,
      diff.data,
      width,
      height,
      {
        threshold: 0.1,        // Matching threshold (0-1), lower = more sensitive
        alpha: 0.1,            // Opacity of diff output
        diffColor: [255, 0, 0] // Red color for differences
      }
    );

    // Calculate metrics
    const totalPixels = width * height;
    const similarityPercentage = 100 - ((numDiffPixels / totalPixels) * 100);

    // Save diff image if path provided
    if (diffOutputPath) {
      fs.writeFileSync(diffOutputPath, PNG.sync.write(diff));
    }

    // Return results
    return {
      success: true,
      similarity: parseFloat(similarityPercentage.toFixed(2)),
      diffPixels: numDiffPixels,
      totalPixels: totalPixels,
      width: width,
      height: height,
      diffImagePath: diffOutputPath
    };

  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: node pixel_compare.js <image1> <image2> [diff-output]');
    console.error('Example: node pixel_compare.js img1.png img2.png diff.png');
    process.exit(1);
  }

  const [img1Path, img2Path, diffOutputPath] = args;

  // Verify files exist
  if (!fs.existsSync(img1Path)) {
    console.error(`Error: Image 1 not found: ${img1Path}`);
    process.exit(1);
  }

  if (!fs.existsSync(img2Path)) {
    console.error(`Error: Image 2 not found: ${img2Path}`);
    process.exit(1);
  }

  // Run comparison
  const result = compareImages(img1Path, img2Path, diffOutputPath);

  // Output JSON result
  console.log(JSON.stringify(result, null, 2));

  process.exit(result.success ? 0 : 1);
}

module.exports = compareImages;
