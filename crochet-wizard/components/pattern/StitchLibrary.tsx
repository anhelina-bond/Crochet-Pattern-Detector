import React from 'react';
import { Path, Ellipse, Circle, G, Line } from 'react-native-svg';

/**
 * International Crochet Symbols Library
 * Colors: Graphite (#3a3335) for lines, Scarlet Rush (#db2b39) for errors.
 * Coordinate System: All symbols are centered at 0,0.
 */

export const getStitchPath = (type: string, color: string = '#3a3335') => {
  const stitchKey = type.toLowerCase().trim();

  // MUCH thinner strokes for dense graphs
  const boldStroke = 0.6;  
  const fineStroke = 0.4;  

  switch (stitchKey) {
    case 'ch_stitch':
    case 'ch':
      return <Ellipse cx="0" cy="0" rx="1.5" ry="0.8" fill="none" stroke={color} strokeWidth={boldStroke} />;
    
    case 'sc_stitch':
    case 'sc':
      return (
        <G>
          <Line x1="0" y1="-1.5" x2="0" y2="1.5" stroke={color} strokeWidth={boldStroke} />
          <Line x1="-1.5" y1="0" x2="1.5" y2="0" stroke={color} strokeWidth={boldStroke} />
        </G>
      );

    case 'hdc_stitch':
      return (
        <G>
          <Line x1="0" y1="-3" x2="0" y2="3" stroke={color} strokeWidth="0.8" strokeLinecap="round" />
          <Line x1="-2" y1="-3" x2="2" y2="-3" stroke={color} strokeWidth="0.8" strokeLinecap="round" />
        </G>
      );

    case 'dc_stitch':
      return (
        <G>
          <Line x1="0" y1="-3.5" x2="0" y2="3.5" stroke={color} strokeWidth="0.8" strokeLinecap="round" />
          <Line x1="-2" y1="-3.5" x2="2" y2="-3.5" stroke={color} strokeWidth="0.8" strokeLinecap="round" />
          <Line x1="-1.5" y1="-1" x2="1.5" y2="1" stroke={color} strokeWidth="1.0" strokeLinecap="round" />
        </G>
      );

    case 'tr_stitch':
    case 'tr':
      return (
        <G>
          <Line x1="0" y1="-4" x2="0" y2="4" stroke={color} strokeWidth={boldStroke} />
          <Line x1="-1.5" y1="-4" x2="1.5" y2="-4" stroke={color} strokeWidth={boldStroke} />
          <Line x1="-1" y1="-2" x2="1" y2="-1" stroke={color} strokeWidth={fineStroke} />
          <Line x1="-1" y1="0.5" x2="1" y2="1.5" stroke={color} strokeWidth={fineStroke} />
        </G>
      );

    case 'sl_st':
      return <Circle cx="0" cy="0" r="0.8" fill={color} />;

    default:
      return <Circle cx="0" cy="0" r="1" fill="#db2b39" />;
  }
};