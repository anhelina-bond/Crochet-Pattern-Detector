import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { usePattern } from '@/context/PatternContext';
import { Colors } from '@/constants/Colors';
import { Ionicons } from '@expo/vector-icons';

export default function OutputModeScreen() {
  const router = useRouter();
  const { setRenderMode } = usePattern();

  const handleSelection = (mode: '2D' | '3D') => {
    setRenderMode(mode);
    if (mode === '3D') {
      router.push('/configure'); // Go to Yarn setup
    } else {
      router.push('/processing'); // Skip to Analysis
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Choose Output Format</Text>
        <Text style={styles.subtitle}>How would you like to visualize your crochet pattern?</Text>

        {/* 2D Option */}
        <TouchableOpacity 
          style={styles.modeCard} 
          onPress={() => handleSelection('2D')}
        >
          <View style={[styles.iconCircle, { backgroundColor: Colors.light.secondary }]}>
            <Ionicons name="document-text" size={32} color="white" />
          </View>
          <View style={styles.modeText}>
            <Text style={styles.modeTitle}>2D Schematic Only</Text>
            <Text style={styles.modeDesc}>Generate a technical symbol chart (SVG).</Text>
          </View>
          <Ionicons name="arrow-forward" size={24} color={Colors.light.primary} />
        </TouchableOpacity>

        {/* 3D Option */}
        <TouchableOpacity 
          style={[styles.modeCard, { borderColor: Colors.light.primary, borderWidth: 2 }]} 
          onPress={() => handleSelection('3D')}
        >
          <View style={[styles.iconCircle, { backgroundColor: Colors.light.primary }]}>
            <Ionicons name="cube" size={32} color="white" />
          </View>
          <View style={styles.modeText}>
            <Text style={styles.modeTitle}>2D Chart + 3D Model</Text>
            <Text style={styles.modeDesc}>Includes realistic simulation with yarn properties.</Text>
          </View>
          <Ionicons name="arrow-forward" size={24} color={Colors.light.primary} />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.light.background },
  content: { flex: 1, padding: 25, justifyContent: 'center' },
  title: { fontSize: 26, fontWeight: 'bold', color: Colors.light.text, marginBottom: 10 },
  subtitle: { fontSize: 16, color: '#666', marginBottom: 40 },
  modeCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  iconCircle: { width: 60, height: 60, borderRadius: 30, justifyContent: 'center', alignItems: 'center' },
  modeText: { flex: 1, marginLeft: 15 },
  modeTitle: { fontSize: 18, fontWeight: 'bold', color: Colors.light.text },
  modeDesc: { fontSize: 13, color: '#888', marginTop: 4 },
});