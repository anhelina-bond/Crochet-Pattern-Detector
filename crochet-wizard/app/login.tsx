import React, { useState } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  Alert, 
  KeyboardAvoidingView, 
  Platform,
  ActivityIndicator,
  ScrollView
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { supabase } from '@/services/supabase';
import { Colors } from '@/constants/Colors';
import { Ionicons } from '@expo/vector-icons';

export default function LoginScreen() {
  const [isSignUp, setIsSignUp] = useState(false); // Toggle between Login and Sign Up
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // Authentication Logic
  async function handleAuthentication() {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);

    if (isSignUp) {
      // Sign Up Logic
      if (password !== confirmPassword) {
        Alert.alert('Error', 'Passwords do not match');
        setLoading(false);
        return;
      }

      const { data: { session }, error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) Alert.alert('Registration Failed', error.message);
      else if (!session) Alert.alert('Success', 'Check your inbox for verification!');
    } else {
      // Login Logic
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) Alert.alert('Login Failed', error.message);
    }
    
    setLoading(false);
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.header}>
            <View style={styles.logoCircle}>
              <Ionicons name="infinite" size={50} color={Colors.light.primary} />
            </View>
            <Text style={styles.title}>{isSignUp ? 'Create Account' : 'Welcome Back'}</Text>
            <Text style={styles.subtitle}>
              {isSignUp ? 'Join the Crochet Wizard community' : 'Digitalize your stitches with AI'}
            </Text>
          </View>

          <View style={styles.form}>
            {/* Email Input */}
            <View style={styles.inputGroup}>
              <Ionicons name="mail-outline" size={20} color={Colors.light.text} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Email Address"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
              />
            </View>

            {/* Password Input */}
            <View style={styles.inputGroup}>
              <Ionicons name="lock-closed-outline" size={20} color={Colors.light.text} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoCapitalize="none"
              />
            </View>

            {/* Confirm Password (Only shown in Sign Up mode) */}
            {isSignUp && (
              <View style={styles.inputGroup}>
                <Ionicons name="checkmark-circle-outline" size={20} color={Colors.light.text} style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChangeText={setConfirmPassword}
                  secureTextEntry
                  autoCapitalize="none"
                />
              </View>
            )}

            {/* Main Action Button */}
            <TouchableOpacity 
              style={[styles.button, styles.primaryBtn]} 
              onPress={handleAuthentication}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.primaryBtnText}>
                  {isSignUp ? 'Register' : 'Sign In'}
                </Text>
              )}
            </TouchableOpacity>

            {/* Mode Switcher */}
            <TouchableOpacity 
              style={styles.switchBtn} 
              onPress={() => setIsSignUp(!isSignUp)}
            >
              <Text style={styles.switchText}>
                {isSignUp 
                  ? 'Already have an account? Sign In' 
                  : "Don't have an account? Create one"}
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
        <Text style={styles.footer}>Graduation Project © 2026</Text>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.light.background },
  scrollContent: { padding: 30, justifyContent: 'center', flexGrow: 1 },
  header: { alignItems: 'center', marginBottom: 40 },
  logoCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    elevation: 4,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 10,
  },
  title: { fontSize: 28, fontWeight: 'bold', color: Colors.light.text },
  subtitle: { fontSize: 14, color: '#888', marginTop: 5, textAlign: 'center' },
  form: { width: '100%' },
  inputGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 15,
    paddingHorizontal: 15,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  inputIcon: { marginRight: 10 },
  input: { flex: 1, height: 50, color: Colors.light.text },
  button: {
    height: 55,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 10,
  },
  primaryBtn: {
    backgroundColor: Colors.light.primary,
    elevation: 3,
  },
  primaryBtnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  switchBtn: {
    marginTop: 20,
    alignItems: 'center',
  },
  switchText: { 
    color: Colors.light.primary, 
    fontSize: 14, 
    fontWeight: '600',
    textDecorationLine: 'underline' 
  },
  footer: {
    textAlign: 'center',
    color: '#aaa',
    fontSize: 11,
    paddingBottom: 20
  }
});