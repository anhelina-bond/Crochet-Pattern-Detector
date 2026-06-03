import React from 'react';
import { View, Dimensions, StyleSheet } from 'react-native';
import Svg, { G, Line, Rect } from 'react-native-svg';
import { getStitchPath } from './StitchLibrary';

const { width: WINDOW_WIDTH } = Dimensions.get('window');
const CHART_SIZE = WINDOW_WIDTH - 40;

export default function CrochetChart({ graphData }: { graphData: any }) {
  if (!graphData || !graphData.nodes) return null;

  // 1. Map 0-1 range to 10-90 range to create padding
  const PADDING = 10;
  const RANGE = 80;
  const toViewBox = (val: number) => (val * RANGE) + PADDING;

  return (
    <View style={styles.container}>
      <Svg width={CHART_SIZE} height={CHART_SIZE} viewBox="0 0 100 100">
        {/* Professional Blueprint Background */}
        <Rect width="100" height="100" fill="#f4e9e2" />
        
        {/* Subtle Grid Lines */}
        {[10, 30, 50, 70, 90].map(pos => (
          <React.Fragment key={pos}>
            <Line x1={pos} y1="0" x2={pos} y2="100" stroke="#dcc3b4" strokeWidth="0.1" />
            <Line x1="0" y1={pos} x2="100" y2={pos} stroke="#dcc3b4" strokeWidth="0.1" />
          </React.Fragment>
        ))}

        {/* 2. Render Edges */}
        {graphData.edges.map((edge: any, index: number) => {
          const child = graphData.nodes[edge.child_id];
          const parent = graphData.nodes[edge.parent_id];
          if (!child || !parent) return null;

          return (
            <Line
              key={`edge-${index}`}
              x1={toViewBox(child.x)}
              y1={toViewBox(child.y)}
              x2={toViewBox(parent.x)}
              y2={toViewBox(parent.y)}
              stroke="#52a4b5"
              strokeWidth="0.15"
              strokeDasharray="0.5, 0.5"
              opacity={0.3}
            />
          );
        })}

        {/* 3. Render Nodes */}
        {graphData.nodes.map((node: any) => {
        // SAFETY CHECK: Skip node if coordinates are invalid
        if (isNaN(node.x) || isNaN(node.y)) return null;

        return (
          <G 
            key={`node-${node.id}`}
            transform={`translate(${toViewBox(node.x)}, ${toViewBox(node.y)}) rotate(${node.angle || 0})`}
          >
            {getStitchPath(node.type)}
          </G>
        );
      })}
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: CHART_SIZE,
    height: CHART_SIZE,
    backgroundColor: '#f4e9e2', // Your Powder Petal palette
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#dcc3b4',
    overflow: 'hidden'
  }
});