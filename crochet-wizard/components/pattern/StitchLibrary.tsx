import React from 'react';
import { Path, Ellipse, Circle, G, Line } from 'react-native-svg';

/**
 * Classical crochet chart symbols following standard industry notation
 * (Craft Yarn Council / CrochetParade conventions).
 *
 * All symbols are drawn centered at (0, 0) so they work cleanly with
 * the translate + rotate transform applied in CrochetChart.tsx.
 *
 * Coordinate scale: the parent <G scale={1.8}> in CrochetChart is kept,
 * so all measurements here are in "symbol units" where ~5–8 units = visible height.
 */
export const getStitchPath = (type: string, color: string = '#3a3335') => {
  const stitchKey = type.toLowerCase().trim();

  switch (stitchKey) {

    /**
     * CH – Chain stitch
     * Classical symbol: a small oval / ellipse (like a chain link).
     * Drawn horizontally; the angle in graphData will orient it along the chain.
     */
    case 'ch_stitch':
      return (
        <Ellipse
          cx="0" cy="0"
          rx="3.5" ry="1.8"
          fill="none"
          stroke={color}
          strokeWidth="0.9"
        />
      );

    /**
     * SL ST – Slip stitch
     * Classical symbol: a small filled circle (dot).
     */
    case 'sl_st':
      return (
        <Circle cx="0" cy="0" r="1.8" fill={color} />
      );

    /**
     * SC – Single crochet
     * Classical symbol: a plus sign "+" (or sometimes "×").
     * Two crossing lines, equal length, centered at origin.
     */
    case 'sc_stitch':
      return (
        <G>
          {/* Vertical bar */}
          <Line x1="0" y1="-4" x2="0" y2="4" stroke={color} strokeWidth="1" strokeLinecap="round" />
          {/* Horizontal bar */}
          <Line x1="-3" y1="0" x2="3" y2="0" stroke={color} strokeWidth="1" strokeLinecap="round" />
        </G>
      );

    /**
     * HDC – Half double crochet
     * Classical symbol: a vertical stem with a short horizontal bar at the top
     * AND a single diagonal "yarn-over" tick crossing the stem near the middle.
     *
     * Standard appearance:
     *   ─┬─   ← top cap (cross bar)
     *    │
     *   ╱    ← one yarn-over tick
     *    │
     *    ↓   ← stem extends down to base
     */
    case 'hdc_stitch':
      return (
        <G>
          {/* Main vertical stem */}
          <Line x1="0" y1="-6" x2="0" y2="6" stroke={color} strokeWidth="1" strokeLinecap="round" />
          {/* Top horizontal cap bar */}
          <Line x1="-2.5" y1="-6" x2="2.5" y2="-6" stroke={color} strokeWidth="1" strokeLinecap="round" />
          {/* Single yarn-over tick (diagonal, crossing stem at ~1/3 from top) */}
          <Line x1="-2.5" y1="-2" x2="2.5" y2="0.5" stroke={color} strokeWidth="0.9" strokeLinecap="round" />
        </G>
      );

    /**
     * DC – Double crochet
     * Classical symbol: a vertical stem with a top cap bar
     * AND a single diagonal tick crossing the stem in the middle.
     *
     * Taller than HDC; one tick = one yarn-over.
     */
    case 'dc_stitch':
      return (
        <G>
          {/* Main vertical stem */}
          <Line x1="0" y1="-7" x2="0" y2="7" stroke={color} strokeWidth="1" strokeLinecap="round" />
          {/* Top horizontal cap bar */}
          <Line x1="-2.5" y1="-7" x2="2.5" y2="-7" stroke={color} strokeWidth="1" strokeLinecap="round" />
          {/* One yarn-over tick across middle of stem */}
          <Line x1="-2.5" y1="-1.5" x2="2.5" y2="1" stroke={color} strokeWidth="0.9" strokeLinecap="round" />
        </G>
      );

    /**
     * TR – Treble (triple) crochet
     * Classical symbol: same T-shape but taller,
     * with TWO diagonal yarn-over ticks crossing the stem.
     */
    case 'tr_stitch':
      return (
        <G>
          {/* Main vertical stem (tallest of all) */}
          <Line x1="0" y1="-9" x2="0" y2="9" stroke={color} strokeWidth="1" strokeLinecap="round" />
          {/* Top horizontal cap bar */}
          <Line x1="-2.5" y1="-9" x2="2.5" y2="-9" stroke={color} strokeWidth="1" strokeLinecap="round" />
          {/* First yarn-over tick (upper) */}
          <Line x1="-2.5" y1="-4.5" x2="2.5" y2="-2" stroke={color} strokeWidth="0.9" strokeLinecap="round" />
          {/* Second yarn-over tick (lower) */}
          <Line x1="-2.5" y1="0.5" x2="2.5" y2="3" stroke={color} strokeWidth="0.9" strokeLinecap="round" />
        </G>
      );

    
    

    default:
      // Red dot as a debug marker — check the console for the unrecognised type
      console.warn('StitchLibrary: unknown stitch type:', type);
      return <Circle cx="0" cy="0" r="2" fill="red" />;
  }
};