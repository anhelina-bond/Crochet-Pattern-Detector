import React from 'react';
import { View, Dimensions, StyleSheet } from 'react-native';
import Svg, { G, Line } from 'react-native-svg';
import { getStitchPath } from './StitchLibrary';

const { width: WINDOW_WIDTH } = Dimensions.get('window');
const CHART_SIZE = WINDOW_WIDTH - 40;

export default function CrochetChart({ graphData }: { graphData: any }) {
  if (!graphData || !graphData.nodes) return null;

  return (
    <View style={styles.container}>
      <Svg width={CHART_SIZE} height={CHART_SIZE} viewBox="0 0 100 100">
        {/* 1. Render Edges (Topology Lines) */}
        {graphData.edges.map((edge: any, index: number) => {
          const child = graphData.nodes[edge.child_id];
          const parent = graphData.nodes[edge.parent_id];
          if (!child || !parent) return null;

          return (
            <Line
              key={`edge-${index}`}
              x1={child.x * 100}
              y1={child.y * 100}
              x2={parent.x * 100}
              y2={parent.y * 100}
              stroke="#52a4b5"
              strokeWidth="0.2"
              strokeDasharray="1, 1"
              opacity={0.4}
            />
          );
        })}

        {/* 2. Render Nodes (Stitch Symbols) */}
        {graphData.nodes.map((node: any) => (
          <G 
            key={`node-${node.id}`}
            // Use the JSON coordinates (x, y) and the calculated angle
            transform={`translate(${node.x * 100}, ${node.y * 100}) rotate(${node.angle || 0})`}
          >
            {/* 
               Scaling logic:
               Since we want the symbols to be visible, we scale them. 
               We can use node.w * 100 as a guide for the scale factor!
            */}
            <G scale={1.8}> 
              {getStitchPath(node.type)}
            </G>
          </G>
        ))}
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