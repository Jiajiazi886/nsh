# Career tree design QA

## Evidence

- Source visual truth:
  - `C:\Users\ASUS\.codex\visualizations\2026\08\26\01a03d21-4792-7323-af53-fab25f10bfe6\career-tree-reference-player-list.png`
  - `C:\Users\ASUS\.codex\visualizations\2026\08\26\01a03d21-4792-7323-af53-fab25f10bfe6\career-tree-reference-file-tree.png`
- Implementation screenshot: `C:\Users\ASUS\.codex\visualizations\2026\08\26\01a03d21-4792-7323-af53-fab25f10bfe6\career-tree-implementation-collapsed.png`
- Combined focused comparison: `C:\Users\ASUS\.codex\visualizations\2026\08\26\01a03d21-4792-7323-af53-fab25f10bfe6\career-tree-design-comparison.png`
- Viewport: WeChat DevTools iPhone 15 Pro simulator in a 1758 x 1340 logical-pixel window.
- Source dimensions: player-list reference 507 x 444 px; file-tree reference 274 x 187 px.
- Implementation dimensions: full capture 1758 x 1340 px; focused career-tree crop 518 x 540 px.
- Density normalization: the references describe structure rather than an identical full screen, so the QA uses an unscaled focused-region comparison instead of pixel-for-pixel density matching.
- State: `神相` collapsed, `铁衣` expanded, selected and unselected player rows both visible.

## Full-view comparison

The original flat two-column player list is replaced by a single-column hierarchy. Career rows provide the same parent level as the reference file folders, and indented player rows provide the child level. The surrounding search, reset, bulk selection, and sticky save controls remain intact.

## Focused-region comparison

The combined comparison shows a clear folder-to-child relationship, independent open/closed states, left indentation, selected-row highlighting, and a compact density appropriate for the existing dark mini-program UI. A separate focused region is sufficient because the source screenshots specify only the player-list and file-tree areas, not the complete page.

## Required fidelity surfaces

- Fonts and typography: career names use the page's existing bold hierarchy; player names retain readable body sizing and do not wrap.
- Spacing and layout rhythm: career rows, indented children, separators, and the sticky save button remain within the mobile viewport without horizontal overflow.
- Colors and visual tokens: existing navy surfaces, purple selection states, muted counters, and border colors are preserved.
- Image quality and asset fidelity: no reference raster asset is part of the product UI; the folder relationship is conveyed with native layout, text labels, indentation, and borders.
- Copy and content: career names, `已选 x / y`, `展开/收起`, player names, and `已选/选择` accurately describe the current state.

## Interaction verification

- Opened Boxes, entered `编辑队伍与玩家`, and rendered career groups in WeChat DevTools.
- Clicked `收起` on `神相`; only that career's players disappeared while `铁衣` stayed open.
- Player selection remained independent from folder open/closed state.
- Search grouping and role/name filtering are covered by automated tests.
- WeChat DevTools reported 0 errors; remaining messages were development-tool/base-library warnings.

## Findings

No actionable P0, P1, or P2 mismatch remains for the requested career-folder hierarchy.

## Comparison history

- Pass 1: no P0/P1/P2 issue found; no visual correction loop was required.

## Follow-up polish

- P3: a dedicated folder icon set could be added later if the project adopts a shared mini-program icon library; the current text action avoids adding an inconsistent one-off asset.

final result: passed
