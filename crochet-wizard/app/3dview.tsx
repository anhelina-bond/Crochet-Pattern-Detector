import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, SafeAreaView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import ModelViewer from '@/components/pattern/ModelViewer';

export default function ThreeDViewScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="close" size={30} color={Colors.light.text} />
        </TouchableOpacity>
        <Text style={styles.title}>3D Simulation</Text>
        <View style={{ width: 30 }} /> 
      </View>

      <View style={styles.viewerContainer}>
        <ModelViewer />
      </View>

      <View style={styles.footer}>
        <Text style={styles.hint}>Drag to rotate • Pinch to zoom</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    padding: 20 
  },
  title: { fontSize: 18, fontWeight: 'bold' },
  viewerContainer: { flex: 1, backgroundColor: '#f0f0f0' },
  footer: { padding: 20, alignItems: 'center' },
  hint: { color: '#888', fontSize: 12 }
});