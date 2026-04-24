import React, { useState } from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, ScrollView} from 'react-native';
import { SafeAreaView, useSafeAreaInsets  } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { usePattern, YarnData } from '@/context/PatternContext';
import { Colors } from '@/constants/Colors';
import { Ionicons } from '@expo/vector-icons';

const WEIGHTS = [
  { id: 0, label: 'Lace' },
  { id: 1, label: 'Super Fine' },
  { id: 2, label: 'Fine (Sport)' },
  { id: 3, label: 'Light (DK)' },
  { id: 4, label: 'Medium (Worsted)' },
  { id: 5, label: 'Bulky' },
];

const FIBERS: YarnData['fiber'][] = ['cotton', 'wool', 'acrylic'];
const PRESET_COLORS = ['#52a4b5', '#db2b39', '#a7f063', '#3a3335', '#ffffff', '#f4e9e2', '#8e7ae6'];

export default function ConfigureScreen() {
  const router = useRouter();
  const { image, setYarnData } = usePattern();
  const insets = useSafeAreaInsets();
  
  // Local state for the form
  const [weight, setWeight] = useState(3);
  const [color, setColor] = useState(PRESET_COLORS[0]);
  const [fiber, setFiber] = useState<YarnData['fiber']>('cotton');

  const handleStartAnalysis = () => {
    // Create the yarn.json structure
    const yarnJson: YarnData = {
      weight,
      color,
      fiber,
    };
    
    setYarnData(yarnJson);
    router.push('/processing');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 20 }}>
        
        {/* 1. Image Preview Card */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Captured Swatch</Text>
          <Image source={{ uri: image }} style={styles.previewImage} />
        </View>

        {/* 2. Yarn Weight Selection */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Yarn Weight (Thickness)</Text>
          <View style={styles.weightGrid}>
            {WEIGHTS.map((w) => (
              <TouchableOpacity
                key={w.id}
                style={[
                  styles.weightBtn,
                  weight === w.id && { backgroundColor: Colors.light.primary, borderColor: Colors.light.primary }
                ]}
                onPress={() => setWeight(w.id)}
              >
                <Text style={[styles.weightText, weight === w.id && { color: '#fff' }]}>
                  {w.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* 3. Color Selection */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Simulation Color</Text>
          <View style={styles.colorRow}>
            {PRESET_COLORS.map((c) => (
              <TouchableOpacity
                key={c}
                style={[
                  styles.colorCircle,
                  { backgroundColor: c },
                  color === c && styles.selectedCircle
                ]}
                onPress={() => setColor(c)}
              />
            ))}
          </View>
        </View>

        {/* 4. Fiber Type */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Fiber Texture</Text>
          <View style={styles.fiberRow}>
            {FIBERS.map((f) => (
              <TouchableOpacity
                key={f}
                style={[styles.fiberBtn, fiber === f && styles.fiberBtnActive]}
                onPress={() => setFiber(f)}
              >
                <Text style={[styles.fiberText, fiber === f && styles.fiberTextActive]}>
                  {f.toUpperCase()}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>
      {/* Action Button */}
      <TouchableOpacity style={styles.mainBtn} onPress={handleStartAnalysis}>
          <Text style={styles.mainBtnText}>Run GNN Analysis</Text>
          <Ionicons name="analytics" size={20} color="white" style={{ marginLeft: 10 }} />
        </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: Colors.light.background },
  container: { 
    flex: 1, 
    backgroundColor: Colors.light.background 
  },
  card: {
    backgroundColor: Colors.light.card,
    borderRadius: 15,
    padding: 15,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.light.text,
    marginBottom: 12,
  },
  previewImage: {
    width: '100%',
    height: 150,
    borderRadius: 10,
    backgroundColor: '#000',
  },
  weightGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  weightBtn: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.light.border,
    backgroundColor: '#fff',
  },
  weightText: { fontSize: 13, color: Colors.light.text },
  colorRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 5 },
  colorCircle: {
    width: 35,
    height: 35,
    borderRadius: 17.5,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  selectedCircle: { borderColor: Colors.light.text, transform: [{ scale: 1.1 }] },
  fiberRow: { flexDirection: 'row', gap: 10 },
  fiberBtn: {
    flex: 1,
    padding: 10,
    borderRadius: 10,
    alignItems: 'center',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  fiberBtnActive: { backgroundColor: Colors.light.success, borderColor: Colors.light.success },
  fiberText: { fontWeight: '600', color: Colors.light.text },
  fiberTextActive: { color: Colors.light.text },
  mainBtn: {
    backgroundColor: Colors.light.primary,
    flexDirection: 'row',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  mainBtnText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
});