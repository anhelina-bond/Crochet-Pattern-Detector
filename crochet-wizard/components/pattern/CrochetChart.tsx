import React, { useMemo } from 'react';
import { View, Dimensions, StyleSheet } from 'react-native';
import Svg, { G, Line, Rect } from 'react-native-svg';
import { getStitchPath } from './StitchLibrary';

const { width: WINDOW_WIDTH } = Dimensions.get('window');
const DEFAULT_CHART_SIZE = WINDOW_WIDTH - 40;

export default function CrochetChart({ graphData, size = DEFAULT_CHART_SIZE }: { graphData: any; size?: number }) {
  if (!graphData || !graphData.nodes) return null;

  const bounds = useMemo(() => {
    const validNodes = graphData.nodes.filter((node: any) => !isNaN(node.x) && !isNaN(node.y));
    if (validNodes.length === 0) {
      return { minX: 0, minY: 0, width: 100, height: 100 };
    }

    const xs = validNodes.map((node: any) => node.x);
    const ys = validNodes.map((node: any) => node.y);
    const nodeWidths = validNodes.map((node: any) => node.w || 0.08);
    const nodeHeights = validNodes.map((node: any) => node.h || 0.08);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const paddingX = Math.max(0.06, Math.max(...nodeWidths) * 1.4);
    const paddingY = Math.max(0.06, Math.max(...nodeHeights) * 1.4);
    const paddedMinX = minX - paddingX;
    const paddedMaxX = maxX + paddingX;
    const paddedMinY = minY - paddingY;
    const paddedMaxY = maxY + paddingY;

    return {
      minX: paddedMinX * 100,
      minY: paddedMinY * 100,
      width: Math.max((paddedMaxX - paddedMinX) * 100, 20),
      height: Math.max((paddedMaxY - paddedMinY) * 100, 20),
    };
  }, [graphData]);

  const toViewBox = (val: number) => val * 100;

  return (
    <View style={styles.container}>
      <Svg width={size} height={size} viewBox={`${bounds.minX} ${bounds.minY} ${bounds.width} ${bounds.height}`}>
        {/* Professional Blueprint Background */}
        <Rect x={bounds.minX} y={bounds.minY} width={bounds.width} height={bounds.height} fill="#f4e9e2" />
        
        {/* Dynamic Grid Lines based on bounds */}
        {Array.from({ length: Math.ceil(bounds.width / 20) + 1 }).map((_, i) => {
          const xPos = Math.floor(bounds.minX / 20) * 20 + (i * 20);
          return (
            <Line key={`v-${xPos}`} x1={xPos} y1={bounds.minY} x2={xPos} y2={bounds.minY + bounds.height} stroke="#dcc3b4" strokeWidth="0.1" />
          );
        })}
        {Array.from({ length: Math.ceil(bounds.height / 20) + 1 }).map((_, i) => {
          const yPos = Math.floor(bounds.minY / 20) * 20 + (i * 20);
          return (
            <Line key={`h-${yPos}`} x1={bounds.minX} y1={yPos} x2={bounds.minX + bounds.width} y2={yPos} stroke="#dcc3b4" strokeWidth="0.1" />
          );
        })}

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
    width: '100%',
    height: '100%',
    backgroundColor: '#f4e9e2', // Your Powder Petal palette
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#dcc3b4',
    overflow: 'hidden'
  }
});
