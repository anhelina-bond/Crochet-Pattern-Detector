import React from 'react';
import { StyleSheet, Text, Pressable } from 'react-native';
import { Colors } from '@/constants/Colors';

interface Props {
  onPress: () => void;
  title?: string;
}

export default function CameraButton({ onPress, title = "Capture Swatch" }: Props) {
  return (
    <Pressable 
      onPress={onPress}
      style={({ pressed }) => [
        styles.btn, 
        { backgroundColor: Colors.light.primary, opacity: pressed ? 0.8 : 1 }
      ]}
    >
      <Text style={[styles.text, { color: Colors.light.background }]}>
        {title}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btn: {
    paddingVertical: 18,
    paddingHorizontal: 40,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4.65,
  },
  text: { fontSize: 18, fontWeight: 'bold' },
});