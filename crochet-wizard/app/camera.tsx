import React, { useState, useRef } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

// 1. IMPORT YOUR CONTEXT HOOK HERE
import { usePattern } from '@/context/PatternContext';

import CameraGuide from '@/components/camera/CameraGuide';
import CameraButton from '@/components/ui/CameraButton';

export default function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<any>(null);
  const router = useRouter();

  // 2. DESTUCTURE THE SETTER FROM CONTEXT
  const { setImage } = usePattern();

  if (!permission) return <View />;

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <TouchableOpacity style={styles.permissionBtn} onPress={requestPermission}>
          <Text style={styles.btnText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // 3. UPDATED CAPTURE FUNCTION
  const handleCapture = async () => {
    if (cameraRef.current) {
      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.8, 
          base64: false,
        });

        // SAVE THE PHOTO URI GLOBALLY HERE!
        setImage(photo.uri); 
        
        // NAVIGATE TO CONFIGURE SCREEN
        router.push('/output-mode');
      } catch (e) {
        Alert.alert("Error", "Could not capture photo");
      }
    }
  };

  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} facing="back" ref={cameraRef}>
        <CameraGuide />
        
        <TouchableOpacity 
          style={styles.closeBtn} 
          onPress={() => router.back()}
        >
          <Ionicons name="close-circle" size={40} color="white" />
        </TouchableOpacity>

        <View style={styles.buttonContainer}>
          <CameraButton onPress={handleCapture} />
        </View>
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  buttonContainer: {
    position: 'absolute',
    bottom: 40,
    width: '100%',
    alignItems: 'center',
  },
  closeBtn: {
    position: 'absolute',
    top: 50,
    left: 20,
    zIndex: 10,
  },
  message: {
    textAlign: 'center',
    paddingBottom: 10,
    color: 'white',
  },
  permissionBtn: {
    backgroundColor: '#52a4b5ff',
    padding: 15,
    borderRadius: 10,
    alignSelf: 'center',
  },
  btnText: { color: 'white', fontWeight: 'bold' },
});