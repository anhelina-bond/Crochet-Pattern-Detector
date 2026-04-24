// components/pattern/SVGViewer.tsx
import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { SvgXml } from 'react-native-svg';

interface Props {
  xml: string;
}

export default function SVGViewer({ xml }: Props) {
  // If the XML is empty or invalid, don't crash
  if (!xml || !xml.includes('<svg')) return null;

  return (
    <View style={styles.container}>
      <SvgXml 
        xml={xml} 
        width="100%" 
        height="100%" 
        preserveAspectRatio="xMidYMid meet"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    // backgroundColor: 'rgba(255,0,0,0.1)', // UNCOMMENT THIS TO TEST IF CONTAINER IS VISIBLE
  },
});