// app/processing.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert, useColorScheme } from 'react-native';
import { useRouter } from 'expo-router';
import { usePattern } from '@/context/PatternContext';
import { analyzeCrochetSwatch } from '@/services/api';
import { Colors } from '@/constants/Colors';
import { supabase } from '@/services/supabase';

const LOADING_STEPS = [
  "Uploading swatch...",
  "Running YOLO detection...",
  "Extracting topology with GNN...",
  "Generating 3D mesh...",
  "Finalizing pattern..."
];

export default function ProcessingScreen() {
  const router = useRouter();
  
  // 1. Extract renderMode from context
  const { image, yarnData, renderMode, setResults } = usePattern();
  
  const [stepIndex, setStepIndex] = useState(0);
  const theme = Colors[useColorScheme() ?? 'light'];

  useEffect(() => {
    const runAnalysis = async () => {
      try {
        if (!image) throw new Error("No image found");

        // 3. Get the current user ID from Supabase
        const { data: { session } } = await supabase.auth.getSession();
        if (!session?.user?.id) throw new Error("User not authenticated");

        // 4. Pass the user ID to the API call
        const data = await analyzeCrochetSwatch(
          image, 
          yarnData, 
          renderMode, 
          session.user.id
        );
        
        setResults(data);
        router.replace('/chat');
      } catch (error: any) {
        Alert.alert("Analysis Failed", error.message);
        router.back();
      }
    };

    runAnalysis();
  }, []);

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ActivityIndicator size="large" color={theme.primary} />
      
      <View style={styles.textContainer}>
        <Text style={[styles.status, { color: theme.text }]}>
          {LOADING_STEPS[stepIndex]}
        </Text>
        <Text style={[styles.subText, { color: theme.text, opacity: 0.6 }]}>
          Please keep the app open
        </Text>
      </View>

      {/* A simple progress visual */}
      <View style={styles.progressBarBg}>
        <View 
          style={[
            styles.progressBarFill, 
            { 
              backgroundColor: theme.primary, 
              width: `${((stepIndex + 1) / LOADING_STEPS.length) * 100}%` 
            }
          ]} 
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  textContainer: { marginTop: 30, alignItems: 'center' },
  status: { fontSize: 18, fontWeight: 'bold', textAlign: 'center' },
  subText: { fontSize: 14, marginTop: 8 },
  progressBarBg: {
    width: '100%',
    height: 6,
    backgroundColor: '#ddd',
    borderRadius: 3,
    marginTop: 40,
    overflow: 'hidden'
  },
  progressBarFill: { height: '100%' }
});