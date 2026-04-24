// app/_layout.tsx
import { Stack } from 'expo-router';
import { PatternProvider } from '@/context/PatternContext'; // Adjust path if needed
import { supabase } from '@/services/supabase';
import { useEffect, useState } from 'react';
import LoginScreen from './login'; 
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function RootLayout() {
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    // Check current session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    // Listen for auth changes (Login/Logout)
    supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });
  }, []);

  // If no session, show a Login Screen instead of the main Stack
  if (!session) {
    return <LoginScreen />; // Create a simple component for this
  }

  return (
    // The Provider must be at the very top level
    <SafeAreaProvider>
      <PatternProvider>
        <Stack screenOptions={{ headerShown: false }}>
          {/* Your navigation screens */}
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="camera" />
          <Stack.Screen name="output-mode" options={{ title: 'Output Mode', headerShown: true }} />
          <Stack.Screen name="configure" options={{ headerShown: true, title: 'Yarn Setup' }} />
          <Stack.Screen name="processing" />
          <Stack.Screen name="chat" options={{ headerShown: true, title: 'AI Assistant' }} />
          <Stack.Screen name="3dview" options={{ presentation: 'modal', headerShown: false }} />
          
        </Stack>
      </PatternProvider>
    </SafeAreaProvider>
    
  );
}