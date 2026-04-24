import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  Alert, 
  useColorScheme 
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Colors } from '@/constants/Colors';

export default function SettingsScreen() {
  const colorScheme = useColorScheme() ?? 'light';
  const theme = Colors[colorScheme];
  
  const [url, setUrl] = useState('http://10.87.157.236:8000');

  // Load the saved URL when the page opens
  useEffect(() => {
    const loadUrl = async () => {
      const savedUrl = await AsyncStorage.getItem('backend_url');
      if (savedUrl) setUrl(savedUrl);
    };
    loadUrl();
  }, []);

  const saveSettings = async () => {
    try {
      if (!url.startsWith('http')) {
        Alert.alert('Invalid URL', 'Please include http:// or https://');
        return;
      }
      await AsyncStorage.setItem('backend_url', url);
      Alert.alert('Success', 'Backend URL updated!');
    } catch (e) {
      Alert.alert('Error', 'Failed to save settings');
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <Text style={[styles.label, { color: theme.text }]}>Backend API URL</Text>
      
      <TextInput
        style={[
          styles.input, 
          { 
            backgroundColor: theme.card, 
            borderColor: theme.border, 
            color: theme.text 
          }
        ]}
        value={url}
        onChangeText={setUrl}
        placeholder="http://192.168.x.x:8000"
        placeholderTextColor={theme.tabIconDefault}
        autoCapitalize="none"
        autoCorrect={false}
      />
      
      <Text style={[styles.hint, { color: theme.text, opacity: 0.6 }]}>
        Tip: Use 'ipconfig' in your Windows terminal to find your IPv4 address.
      </Text>

      <TouchableOpacity 
        style={[styles.button, { backgroundColor: theme.primary }]} 
        onPress={saveSettings}
        activeOpacity={0.8}
      >
        <Text style={[styles.buttonText, { color: theme.background }]}>
          Save Configuration
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    padding: 20, 
    justifyContent: 'center' 
  },
  label: { 
    fontSize: 18, 
    fontWeight: 'bold', 
    marginBottom: 10 
  },
  input: {
    borderWidth: 1,
    padding: 15,
    borderRadius: 12,
    fontSize: 16,
  },
  hint: { 
    fontSize: 12, 
    marginTop: 10, 
    marginBottom: 40 
  },
  button: {
    padding: 18,
    borderRadius: 15,
    alignItems: 'center',
    // Shadow for depth on Pacific Blue
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  buttonText: { 
    fontSize: 16, 
    fontWeight: 'bold',
    letterSpacing: 0.5
  },
});