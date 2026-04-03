# Design System Strategy: The Eldritch Archive

## 1. Overview & Creative North Star
**Creative North Star: The Arcane Ledger**

This design system moves away from the sterile, utilitarian "SaaS" look of the reference image and transforms data management into a high-stakes, atmospheric experience. We are building an "Arcane Ledger"—a digital artifact that feels heavy, intentional, and ancient, yet powered by sharp, crystalline energy. 

By leveraging **0px border-radii (Sharp Edges)** and a **Dark-on-Dark tonal strategy**, we create a sense of "Brutal Fantasy." We break the standard "box-within-a-box" template by using intentional asymmetry and "Energy Accents" that draw the eye to critical data points, mimicking the visual language of a rogue-like deckbuilder where every choice has weight.

## 2. Colors
The palette is rooted in the void, with data surfacing through bioluminescent "Energy" colors.

### The "No-Line" Rule
Explicitly: **Do not use 1px solid borders for sectioning.** 
Structural separation is achieved through background shifts. For example:
- A secondary navigation area uses `surface_container_low` (#131313).
- Content cards use `surface_container` (#191a1a).
- The main background remains `background` (#0e0e0e).
This creates a seamless, "etched" look rather than a wireframe look.

### Surface Hierarchy & Nesting
Treat the UI as physical layers of obsidian and stone:
- **Level 0 (Deepest):** `surface_container_lowest` (#000000) for "void" space or inactive areas.
- **Level 1 (Base):** `surface` (#0e0e0e) for the primary workspace.
- **Level 2 (Elevated):** `surface_container_high` (#1f2020) for interactive elements and data clusters.

### The "Glass & Gradient" Rule
To add "soul" to the darkness, use `backdrop-blur` (8px–16px) on floating menus with a 60% opacity of `surface_container_highest`. 
- **Signature Gradients:** For primary actions, transition from `primary` (#c799ff) to `primary_container` (#bc87fe) at a 45-degree angle. This mimics the "glow" of a rare card.

## 3. Typography
We utilize a high-contrast pairing of **Newsreader** and **Work Sans**.

- **Display & Headlines (Newsreader):** This serif font provides a "Gothic" flavor. It feels editorial and ancient. Use `display-lg` and `headline-md` for page titles and section headers to establish an authoritative, narrative tone.
- **Body & Labels (Work Sans):** To maintain high readability for complex data (APIs, stats, run IDs), we use the clean, geometric Work Sans. 
- **Hierarchy Logic:** Use `on_surface_variant` (#acabaa) for secondary descriptions and `primary` (#c799ff) for interactive labels to ensure the "Energy" colors guide the user's focus.

## 4. Elevation & Depth
In this system, depth is a matter of light, not lines.

- **The Layering Principle:** Stacking is the only way to show priority. A `surface_container_highest` (#262626) card sitting on a `surface` background creates a "monolithic" feel without a single stroke.
- **Ambient Shadows:** Shadows are rare but intentional. When an element must "float" (like a tooltip), use a 24px blur, 10% opacity shadow with a hue tint of `primary` (#c799ff). This simulates a magical light source casting a glow.
- **The "Ghost Border" Fallback:** If a container needs more definition, use `outline_variant` (#484848) at **15% opacity**. It should be felt, not seen.
- **Glassmorphism:** Use for "floating" sidebars. The transparency allows the "dark stone" textures of the background to peek through, maintaining the atmospheric immersion.

## 5. Components

### Buttons
- **Primary:** Sharp edges (0px). Gradient fill (`primary` to `primary_container`). Text in `on_primary`. 
- **Secondary:** Transparent background, `outline` (#767575) at 20% opacity, text in `primary`.
- **Tertiary/Energy:** For destructive actions, use `tertiary_dim` (#e9003a) text with no background.

### Cards & Lists
**Strict Rule:** No divider lines. Separate list items using 8px–12px of vertical white space and a subtle background shift to `surface_container_low` on hover. The content should feel like "scrawlings on a stone slab," organized by alignment rather than cages.

### Input Fields
- **States:** Default state uses `surface_container_highest`. Focus state triggers a 1px "Ghost Border" of `secondary` (#00e475) to represent a "charged" interaction.
- **Error:** Use `error` (#fd6f85) text and a soft `error_container` glow behind the input.

### Energy Accents (Status Chips)
- **Success/Healed:** `secondary` (#00e475) text on `secondary_container`.
- **Warning/Elite:** `tertiary` (#ffb3b3) text on `tertiary_container`.
- **Magic/Mana:** `primary` (#c799ff) text on `on_primary_container`.

## 6. Do's and Don'ts

### Do
- **Use "Worn Texture":** Apply a subtle noise overlay (2-3% opacity) to `surface_container` elements to mimic dark stone or parchment.
- **Embrace Asymmetry:** Align large headlines to the far left, but keep data metrics in rigid, right-aligned columns to create a "manuscript" feel.
- **Use Vibrant Accents Sparingly:** A single `secondary` (#00e475) "Energy" glow is more powerful when surrounded by `charcoal` and `deep purple`.

### Don't
- **Don't use Rounded Corners:** Ever. The system is built on "Sharp & Clean Edges" (0px) to maintain a dangerous, fantasy-edge feel.
- **Don't use Pure White:** Avoid #FFFFFF. All "light" text should be `on_surface` (#e7e5e4), which is slightly warm, feeling more like aged paper or reflected light.
- **Don't use standard Tooltips:** Avoid floating black boxes. Use `surface_container_highest` with a `primary` glow to make tooltips feel like "revealed secrets."