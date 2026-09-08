# FAANG-Level Code Quality & Feature Roadmap for PostBuilder

## 1. Architecture & Code Structure (Clean Code)
- **Component Decomposition:**
  - The `PostBuilder` component is becoming a "God Component" (>1000 lines).
  - **Action:** Extract sub-components into their own files:
    - `src/components/admin/builder/canvas/canvas-area.jsx`
    - `src/components/admin/builder/toolbar/builder-toolbar.jsx`
    - `src/components/admin/builder/panels/left-panel.jsx`
    - `src/components/admin/builder/panels/right-panel.jsx`
    - `src/components/admin/builder/overlays/marquee-overlay.jsx`
    - `src/components/admin/builder/overlays/distance-indicators.jsx`
- **State Management (Context API):**
  - **Problem:** Massive prop drilling (`sections`, `setSections`, `selection`, `zoom` passed 3-4 levels deep).
  - **Solution:** Create a `BuilderContext` provider.
    - `useBuilderState()`: Access `sections`, `zoom`, `viewMode`.
    - `useBuilderDispatch()`: Access actions like `selectSection`, `updateSection`, `undo`, `redo`.
  - This drastically reduces boilerplate props and simple re-renders.
- **Custom Hooks Logic Extraction:**
  - Extract logic into testable hooks:
    - `useShortcuts`: Handle all keyboard listeners.
    - `useCanvasZoom`: Handle wheel, pinch, and zoom limit logic.
    - `useSelection`: Handle single click, multi-click (shift), and marquee logic.

## 2. Performance Engineering
- **Render Optimization:**
  - **Problem:** Updating one input in a section likely re-renders the entire Canvas and all other Sections.
  - **Solution:** Wrap `SectionItem` and major UI blocks in `React.memo`. Ensure callback functions (like `handleSelect`) are stable using `useCallback`.
- **Virtualization (If needed):**
  - If users build pages with >50 sections, standard rendering will lag.
  - **Solution:** Implement a virtual list for the Canvas if section counts get high (though tricky with variable heights).

## 3. High-Value User Features (Missing)
- **Advanced Drag & Drop (DnD):**
  - Current implementation seems native/basic.
  - **Upgrade:** Use `@dnd-kit/core` or `react-beautiful-dnd` for:
    - smooth animations during reorder.
    - "Ghost" previews while dragging.
    - Auto-scrolling when dragging near edge of screen.
- **Infinite Canvas / Panning:**
  - **Feature:** Spacebar + Drag to pan around the canvas (Figma style).
- **Snap-to-Grid / Alignment Guides:**
  - **Feature:** Visual lines appearing when an element aligns with another (currently you have distance indicators, but snapping is next level).
- **Context Menus:**
  - Enhance the right-click menu to include: "Copy Style", "Paste Style", "Lock", "Hide", "Rename".

## 4. Robustness & Accessibility (A11y)
- **Accessibility:**
  - Ensure all tooltips have standard delays.
  - Ensure all icon-only buttons have `aria-label`.
  - Keyboard navigation for the canvas (Arrow keys to move selection).
- **Type Safety (JSDoc):**
  - Since we aren't using TypeScript, adding comprehensive JSDoc comments to components and hooks is crucial for maintainability.

## 5. UI Polish
- **Empty States:** Make them educational (shortcuts cheat sheet).
- **Loading States:** Smooth skeletons if saving/loading takes time.
- **Cursors:** Context-aware cursors (hand for panning, crosshair for marquee, default for pointer).
