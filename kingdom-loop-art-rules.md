# Kingdom Loop — current art rules

Updated 28 September 2026. These rules supersede earlier art-size experiments and conflicting examples in the design and tools guide.

- Use built-in AI image generation to create environment assets, buildings, props, terrain art, and interface graphics.
- Final character artwork will be authored by the user later. The complete-demo request explicitly authorizes matched, animated temporary characters and enemies now. Keep their assets replaceable through stable actor art IDs.
- All new individual runtime artwork uses exact 64×64 pixel PNG canvases. Keep native pixels crisp, use nearest-neighbor filtering, and scale previews by whole-number factors.
- Use transparent backgrounds for isolated props, buildings, icons, and UI skins. A terrain tile may fill its canvas when intended to cover ground.
- Buildings show only their front facade, with readable roofs and height. No visible side wall, side windows, isometric diamond, or three-quarter building rotation.
- Keep the compact, warm fantasy pixel style of the approved cottage and tree. Avoid excessive fine detail.
- Process generated pixel-style art with Pixel Snapper as needed, then finish and export in Aseprite. Hand-authored character art does not need Pixel Snapper.
- UI skins and icons are also 64×64. Panels and buttons may expand using nine-slice rendering; their source PNGs stay 64×64. Text and live values belong in the game rather than being painted into the images.
- Save generated originals, exact prompts, snapped intermediates, editable Aseprite sources, PNG exports, and a verified Godot preview in versioned folders.

The current environment/UI batch is `settlement-ui-64-v1`; the previously approved 64×64 cottage and tree are reused in it. This policy does not change gameplay timing, construction, or family rules.
