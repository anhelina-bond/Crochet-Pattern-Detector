import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  TouchableOpacity, 
  Image, 
  StatusBar 
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import { usePattern, YarnData } from '@/context/PatternContext'; // Corrected Import
import { supabase } from '@/services/supabase';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export interface Pattern {
  id: string;
  user_id: string;
  name: string;
  image_url: string;
  model_url?: string;
  svg_data: string;
  graph_data: {
    nodes: Array<{ id: number; type: string; x: number; y: number }>;
    edges: Array<[number, number]>;
  };
  yarn_config: YarnData;
  stitch_type: string;
  render_mode: '2D' | '3D';
  created_at: string;
}

export default function HomeScreen() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { setResults, setYarnData, setRenderMode } = usePattern();

  const fetchSavedPatterns = async () => {
    // 1. Get the current user
    const { data: { user } } = await supabase.auth.getUser();
    
    if (!user) return;
  
    // 2. Filter by user_id
    const { data, error } = await supabase
      .from('patterns')
      .select('*')
      .eq('user_id', user.id) // <--- CRITICAL FILTER
      .order('created_at', { ascending: false });
  
    if (error) {
      console.error("Supabase Error:", error.message);
      return;
    }
  
    if (data) setPatterns(data as Pattern[]);
  };

  useEffect(() => {
    fetchSavedPatterns();
  }, []);

  const startNewProject = () => {
    router.push('/camera');
  };

  const renderPatternCard = ({ item }: { item: Pattern }) => (
    <TouchableOpacity 
        style={styles.patternCard}
        onPress={() => {
          setResults({
            name: item.name,  
            pattern_id: item.id,
            svg_data: item.svg_data,
            graph_json: item.graph_data,
            image_url: item.image_url, // <--- MAKE SURE THIS LINE IS HERE
            success: true
          });
          setYarnData(item.yarn_config);
          setRenderMode(item.render_mode);
          router.push('/chat');
       }}
      >
      <Image source={{ uri: item.image_url }} style={styles.cardImage} />
      
      <View style={styles.cardInfo}>
        <Text style={styles.cardName}>{item.name}</Text>
        <View style={styles.cardMeta}>
          <View style={[styles.badge, { backgroundColor: Colors.light.primary }]}>
            <Text style={styles.badgeText}>{item.stitch_type}</Text>
          </View>
          
          <View style={[styles.badge, { backgroundColor: Colors.light.secondary }]}>
            <Text style={styles.badgeText}>{item.render_mode}</Text>
          </View>
          
          <Text style={styles.cardDate}>
             {new Date(item.created_at).toLocaleDateString()}
          </Text>
        </View>
      </View>
      <Ionicons name="chevron-forward" size={20} color={Colors.light.text} />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.container}>
        
        <View style={styles.header}>
          <View>
            <Text style={styles.welcomeText}>Crochet Lab</Text>
            <Text style={styles.subWelcome}>Topology Reconstruction</Text>
          </View>
          <TouchableOpacity style={styles.profileBtn}>
            <Ionicons name="person-circle" size={32} color={Colors.light.primary} />
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.actionCard} onPress={startNewProject}>
          <View style={styles.actionIconContainer}>
            <Ionicons name="camera" size={30} color="white" />
          </View>
          <View style={styles.actionTextContainer}>
            <Text style={styles.actionTitle}>Analyze New Piece</Text>
            <Text style={styles.actionSubtitle}>Identify stitches & connections</Text>
          </View>
          <Ionicons name="add-circle" size={28} color="white" />
        </TouchableOpacity>

        <View style={styles.libraryHeader}>
          <Text style={styles.sectionTitle}>Saved Patterns</Text>
          <TouchableOpacity onPress={fetchSavedPatterns}>
            <Text style={[styles.seeAll, { color: Colors.light.primary }]}>Refresh</Text>
          </TouchableOpacity>
        </View>

        {patterns.length > 0 ? (
          <FlatList
            data={patterns}
            renderItem={renderPatternCard}
            keyExtractor={(item) => item.id}
            // THIS IS THE FIX FOR THE BOTTOM BUTTONS
            contentContainerStyle={[
              styles.listContent, 
              { paddingBottom: insets.bottom + 20 } 
            ]}
            showsVerticalScrollIndicator={false}
          />
        ) : (
          <View style={styles.emptyState}>
            <Ionicons name="document-text-outline" size={60} color="#ccc" />
            <Text style={styles.emptyText}>No patterns saved yet.</Text>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: Colors.light.background },
  container: { flex: 1, paddingHorizontal: 20 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 25,
  },
  welcomeText: { fontSize: 28, fontWeight: 'bold', color: Colors.light.text },
  subWelcome: { fontSize: 14, color: '#666' },
  profileBtn: { padding: 5 },
  
  actionCard: {
    backgroundColor: Colors.light.primary,
    borderRadius: 20,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 30,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  actionIconContainer: {
    width: 50,
    height: 50,
    borderRadius: 15,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionTextContainer: { flex: 1, marginLeft: 15 },
  actionTitle: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  actionSubtitle: { color: 'rgba(255,255,255,0.8)', fontSize: 13 },

  libraryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginBottom: 15,
  },
  sectionTitle: { fontSize: 20, fontWeight: 'bold', color: Colors.light.text },
  seeAll: { fontWeight: '600' },

  listContent: { paddingBottom: 20 },
  patternCard: {
    backgroundColor: Colors.light.card,
    borderRadius: 15,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  cardImage: { width: 60, height: 60, borderRadius: 10, backgroundColor: '#ddd' },
  cardInfo: { flex: 1, marginLeft: 15 },
  cardName: { fontSize: 16, fontWeight: '600', color: Colors.light.text },
  cardMeta: { flexDirection: 'row', marginTop: 4, alignItems: 'center' },
  
  badge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    marginRight: 8,
  },
  badgeText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },

  cardDate: { fontSize: 12, color: '#888' },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', marginTop: 50 },
  emptyText: { marginTop: 10, color: '#999', fontSize: 16 },
});