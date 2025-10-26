#!/usr/bin/env node

/**
 * Simple DOM Measurement Tool (Phase 1 - Manual Mapping)
 *
 * Extracts bounding box measurements for specific elements
 * using Playwright to execute measurement code in browser context.
 */

const { chromium } = require('playwright');
const path = require('path');

/**
 * Measure specific DOM elements
 * @param {string} htmlPath - Path to HTML file
 * @param {Object} elementSelectors - Map of element names to CSS selectors
 * @returns {Promise<Object>} Measurements for each element
 */
async function measureDOM(htmlPath, elementSelectors) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Set viewport to desktop size (matching Figma artboard)
  await page.setViewportSize({ width: 1440, height: 1170 });

  // Load the HTML file
  const fileUrl = `file://${path.resolve(htmlPath)}`;
  await page.goto(fileUrl, { waitUntil: 'networkidle' });

  // Execute measurement script in browser context
  const measurements = await page.evaluate((selectors) => {
    const results = {};

    for (const [name, selector] of Object.entries(selectors)) {
      const element = document.querySelector(selector);

      if (element) {
        const rect = element.getBoundingClientRect();
        const styles = window.getComputedStyle(element);

        results[name] = {
          found: true,
          selector: selector,
          dimensions: {
            width: Math.round(rect.width * 100) / 100,
            height: Math.round(rect.height * 100) / 100,
            x: Math.round(rect.x * 100) / 100,
            y: Math.round(rect.y * 100) / 100
          },
          styles: {
            fontSize: styles.fontSize,
            fontFamily: styles.fontFamily,
            fontWeight: styles.fontWeight
          }
        };
      } else {
        results[name] = {
          found: false,
          selector: selector,
          error: 'Element not found'
        };
      }
    }

    return results;
  }, elementSelectors);

  await browser.close();
  return measurements;
}

/**
 * CLI interface
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage: node measure_dom_simple.js <html_file>');
    console.error('Example: node measure_dom_simple.js output/code/pdp-trimmed.html');
    process.exit(1);
  }

  const htmlPath = args[0];

  // Define element selectors for manual mapping
  // These map to the 5 key elements we identified in Figma
  const elementSelectors = {
    'main_product_image': 'img:first-of-type',  // First image = main product photo
    'product_title': 'h1',                       // Product name headline
    'product_description': 'p:first-of-type',   // First paragraph = romance copy
    'selection_bar': '.selection-bar, [class*="selection"], [class*="bar"]',  // Try common class patterns
    'left_column': '.left-column, [class*="left"], .product-info'  // Try common patterns
  };

  try {
    console.error('Measuring DOM elements...');
    const measurements = await measureDOM(htmlPath, elementSelectors);

    // Output JSON to stdout
    console.log(JSON.stringify(measurements, null, 2));

    // Summary to stderr
    console.error('\n✅ Measurements complete!');
    const foundCount = Object.values(measurements).filter(m => m.found).length;
    console.error(`Found: ${foundCount}/${Object.keys(measurements).length} elements`);

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { measureDOM };
