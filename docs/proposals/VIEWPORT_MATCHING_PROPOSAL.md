# Viewport Matching Proposal - Issue #4

## Problem Statement

**Current State:**
- Figma artboard: 1440×2249 pixels (logical dimensions)
- Figma screenshot: 2880×4498 pixels (2× scale for retina)
- Rendered screenshot: 1440×900 pixels (arbitrary browser window size)

**Result:** Pixel-diff fails due to dimension mismatch, and even when it runs, we're comparing different viewport sizes.

---

## Your Key Insight

> "What if we restrict the size of the browser window (or within an iFrame) to match the outer container in the Figma file? Perhaps that would create a point of reference?"

**This is exactly right.** Professional design QA tools (Percy, Chromatic, etc.) all do this:
1. Extract the design artboard dimensions
2. Set browser viewport to match
3. Capture at matching scale (1× or 2×)
4. Compare apples-to-apples

---

## Proposed Solution

### Option 1: Viewport-Constrained Rendering (Recommended)

**Approach:**
1. Read Figma artboard dimensions from metadata JSON
2. Set Playwright viewport to exact artboard size (1440×2249)
3. Capture screenshot at 2× device pixel ratio to match Figma's export
4. Result: Both screenshots are 2880×4498, truly comparable

**Implementation:**
```python
def render_with_figma_viewport(html_path, figma_metadata_path, output_path):
    # Load Figma metadata
    with open(figma_metadata_path) as f:
        metadata = json.load(f)

    # Extract artboard dimensions
    bounds = metadata['absoluteBoundingBox']
    viewport_width = int(bounds['width'])
    viewport_height = int(bounds['height'])

    # Render at 2x device pixel ratio to match Figma screenshot
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={'width': viewport_width, 'height': viewport_height},
            device_scale_factor=2  # Retina/2x
        )
        page = context.new_page()
        page.goto(f'file://{html_path}')
        page.screenshot(path=output_path)
```

**Pros:**
- Exact apples-to-apples comparison
- Uses design artboard as source of truth
- Handles retina scaling correctly
- No manual dimension wrangling

**Cons:**
- Assumes HTML should render at exact Figma dimensions
- Doesn't test responsive behavior

---

### Option 2: Dual-Mode Evaluation

**Approach:**
Recognize there are TWO legitimate evaluation modes:

1. **Fixed Viewport Mode** (what you suggested)
   - Viewport = Figma artboard dimensions
   - Tests: "Does code match pixel-perfect at design breakpoint?"
   - Use case: Design QA, initial implementation verification

2. **Responsive Testing Mode** (future)
   - Viewport = Various sizes (mobile, tablet, desktop)
   - Tests: "Does code adapt gracefully?"
   - Use case: Cross-device testing, accessibility

**Config Example:**
```yaml
evaluation:
  mode: "fixed_viewport"  # or "responsive"
  viewport_source: "figma_artboard"  # or "custom" or "device_preset"
  device_scale_factor: 2  # Match Figma's retina export
```

---

## Addressing the "Natural Variations" Problem

You raised an important point:
> "There are always going to be fundamental differences... some shifting and scaling... (within some tolerances) be OK."

**Two strategies:**

### Strategy A: Strict Mode (Initial Implementation)
- Viewport locked to Figma dimensions
- HTML expected to render at exact size
- Any scaling/shifting is a defect
- **Trade-off:** Doesn't test responsive behavior

### Strategy B: Tolerance Bands (Future Enhancement)
- Define acceptable variation zones
- Example: "Text can reflow ±2 lines, images can scale ±5%"
- Requires semantic understanding of what's "acceptable"
- **Trade-off:** More complex to implement

**Recommendation:** Start with Strategy A (strict mode), add Strategy B later if needed.

---

## Implementation Plan

### Phase 1: Basic Viewport Matching ✓
1. Modify `render_html.py` to accept viewport dimensions
2. Read dimensions from Figma metadata JSON
3. Set `device_scale_factor=2` to match retina
4. Update evaluation scripts to use metadata-driven rendering

### Phase 2: Config-Driven Evaluation
1. Add `viewport_config.yaml`:
   ```yaml
   frame1:
     width: 390
     height: 844
     scale: 2
     source: "figma_metadata"

   product-page:
     width: 1440
     height: 2249
     scale: 2
     source: "figma_metadata"
   ```

2. Update evaluation pipeline to read config

### Phase 3: Responsive Mode (Optional)
1. Add multi-viewport testing
2. Define breakpoint-specific acceptance criteria

---

## Registration Marks Idea

You mentioned:
> "I was wondering if putting registration marks on the Figma might give guidelines to match the screenshots up better."

**Analysis:**
- **Pros:** Could help with alignment detection, rotational differences
- **Cons:**
  - Adds manual work to Figma files
  - Doesn't solve for scaling differences
  - Viewport matching is cleaner

**Verdict:** Viewport matching solves the root cause; registration marks would be a band-aid.

---

## Recommended Next Steps

1. **Immediate:** Implement viewport matching based on Figma metadata
2. **Short-term:** Add config file for per-design viewport settings
3. **Long-term:** Consider dual-mode evaluation (fixed vs. responsive)

Would you like me to implement Phase 1 (basic viewport matching)?

---

## Technical Details

### Current Files to Modify:
- `scripts/render_html.py` - Add viewport detection from metadata
- `scripts/evaluate_combined.py` - Ensure it uses metadata-driven rendering
- `tools/figma_api.py` - May need to enhance metadata extraction

### New Files to Create:
- `config/viewport_config.yaml` - Per-design viewport settings (optional)
- `scripts/render_with_metadata.py` - Metadata-aware rendering utility
