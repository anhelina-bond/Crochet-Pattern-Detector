import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  TextInput, 
  TouchableOpacity, 
  KeyboardAvoidingView, 
  Platform,
  ActivityIndicator,
  Alert,
  Modal
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import ChatBubble from '@/components/ui/ChatBubble';
import SVGViewer from '@/components/pattern/SVGViewer';
import { usePattern } from '@/context/PatternContext';
import { modifyPattern, savePatternToLibrary } from '@/services/api';
import { supabase } from '@/services/supabase'; // Import supabase client

export default function ChatScreen() {
  const router = useRouter();
  const { results, setResults, yarnData, renderMode } = usePattern();
  
  const [messages, setMessages] = useState([
    { id: '1', text: "Analysis complete! How can I help you modify this pattern?", isUser: false },
  ]);
  const [inputText, setInputText] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [isNamingModalVisible, setNamingModalVisible] = useState(false);
  const [patternName, setPatternName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  // 1. Fetch the session user on mount
  useEffect(() => {
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        setUserId(session.user.id);
      } else {
        Alert.alert("Session Expired", "Please login again.");
        router.replace('/login' as any);
      }
    };
    getSession();
  }, []);

  const sendMessage = async () => {
    if (!inputText.trim() || isUpdating || !userId) return;

    // Add user message to UI
    const userMsg = { id: Date.now().toString(), text: inputText, isUser: true };
    setMessages(prev => [...prev, userMsg]);
    
    const promptToSend = inputText;
    setInputText('');
    setIsUpdating(true);

    try {
      // 2. Call the API with Pattern ID and User ID
      // We check results.pattern_id which was returned by the /analyze call
      const response = await modifyPattern(
        promptToSend, 
        results?.graph_json || {}, 
        yarnData,
        results?.pattern_id, // Important: unique ID from DB
        userId               // Important: unique User ID from Auth
      );

      if (response.success) {
        // Use a functional update (prev => ...) to merge data safely
        setResults((prev: any) => ({
          ...prev,                  // 1. Keep everything we already have (image_url, pattern_id)
          svg_data: response.svg_data,   // 2. Overwrite with new SVG
          graph_json: response.graph_json // 3. Overwrite with new Graph
        }));
      
        // Add AI response to UI
        const aiMsg = { 
          id: (Date.now() + 1).toString(), 
          text: response.message, 
          isUser: false 
        };
        setMessages(prev => [...prev, aiMsg]);
      }
    } catch (error) {
      Alert.alert("Update Failed", "Could not reach the server.");
    } finally {
      setIsUpdating(false);
    }
  };
  
  
  const handleFinalSave = async () => {
    console.log("Current Results State:", results);

    if (!results?.image_url) {
      Alert.alert("Error", `Missing Image URL. ID is: ${results?.pattern_id}`);
      return;
    }
    
    if (!results?.graph_json) {
      Alert.alert("Error", "Missing Graph Data.");
      return;
    }
  
    setIsSaving(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      // PERFORM THE PERMANENT SAVE
      await savePatternToLibrary({
        patternId: results?.pattern_id,
        userId: session?.user.id!,
        name: patternName,
        graphData: results.graph_json,
        svgData: results.svg_data,
        imageUrl: results.image_url,
        yarnConfig: yarnData,
        renderMode: renderMode
      });
  
      setNamingModalVisible(false);
      // Go to library to see the newly saved item
      router.replace('/(tabs)'); 
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleOpenNamingModal = () => {
    if (results?.name) {
      setPatternName(results.name); // Pre-fill with existing name
    } else {
      setPatternName('New Crochet Design'); // Default for new scans
    }
    setNamingModalVisible(true);
  };


  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : undefined} 
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      style={styles.container}
    >
      {/* 1. Result Preview Header */}
      <View style={styles.resultPreview}>
         <View style={styles.placeholderChart}>
            {results?.svg_data ? (
              <SVGViewer xml={results.svg_data} />
            ) : (
              <ActivityIndicator color={Colors.light.primary} />
            )}
         </View>

         {renderMode === '3D' && (
           <TouchableOpacity 
             style={styles.threeDBtn}
             onPress={() => router.push('/3dview' as any)}
           >
             <Ionicons name="cube-outline" size={16} color="white" />
             <Text style={styles.threeDBtnText}>Open 3D Viewer</Text>
           </TouchableOpacity>
         )}
         
         <Text style={styles.metaText}>
           Pattern ID: {results?.pattern_id?.substring(0,8) || 'Draft'}... | Yarn: {yarnData.fiber}
         </Text>
      </View>

      {/* 2. Chat List */}
      <FlatList
        data={messages}
        keyExtractor={item => item.id}
        renderItem={({ item }) => <ChatBubble text={item.text} isUser={item.isUser} />}
        contentContainerStyle={styles.chatList}
      />

      {/* 3. Consolidated Input & Action Section */}
      <View style={styles.inputWrapper}>
        {isUpdating && (
          <View style={styles.loadingStatus}>
            <ActivityIndicator size="small" color={Colors.light.primary} />
            <Text style={styles.loadingText}>AI is updating topology...</Text>
          </View>
        )}
        
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Type modification..."
            value={inputText}
            onChangeText={setInputText}
            multiline
          />
          <TouchableOpacity 
            style={[styles.sendBtn, { backgroundColor: Colors.light.primary }]} 
            onPress={sendMessage}
          >
            <Ionicons name="send" size={20} color="white" />
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity 
          style={styles.finishBtn} 
          onPress={handleOpenNamingModal} // 2. Change the onPress to use our helper
        >
          <Text style={styles.finishBtnText}>Save & Finish</Text>
        </TouchableOpacity>
      </View>

      {/* 4. Naming Modal (Remains the same) */}
      <Modal visible={isNamingModalVisible} transparent={true} animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Name your Pattern</Text>
            <TextInput
              style={styles.modalInput}
              value={patternName}
              onChangeText={setPatternName}
              placeholder="e.g. Blue Scarf Segment"
              autoFocus
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalBtn, { backgroundColor: '#ddd' }]} 
                onPress={() => setNamingModalVisible(false)}
              >
                <Text style={{ color: '#333' }}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalBtn, { backgroundColor: Colors.light.primary }]} 
                onPress={handleFinalSave}
              >
                {isSaving ? <ActivityIndicator color="#fff" /> : <Text style={{ color: '#fff', fontWeight: 'bold' }}>Save</Text>}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, 
    backgroundColor: '#fff', 
    paddingBottom: 30 
  },
  resultPreview: {
    height: 260,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderColor: Colors.light.border,
    padding: 15,
  },
  placeholderChart: {
    flex: 1,
    backgroundColor: Colors.light.card,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderStyle: 'dashed',
    borderWidth: 1,
    borderColor: Colors.light.primary,
    overflow: 'hidden',
  },
  threeDBtn: {
    backgroundColor: Colors.light.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 20,
    marginTop: 10,
    alignSelf: 'center',
  },
  threeDBtnText: { color: 'white', fontWeight: 'bold', fontSize: 12, marginLeft: 5 },
  metaText: { fontSize: 10, color: Colors.light.text, opacity: 0.5, textAlign: 'center', marginTop: 8 },
  chatList: { padding: 15 },
  inputWrapper: {
    padding: 15,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderColor: Colors.light.border,
  },
  loadingStatus: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginBottom: 10 },
  loadingText: { marginLeft: 10, fontSize: 12, color: Colors.light.primary, fontWeight: '600' },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.light.card,
    borderRadius: 25,
    paddingHorizontal: 15,
    paddingVertical: 7,
  },
  input: { flex: 1, maxHeight: 80, paddingVertical: 10, color: Colors.light.text },
  sendBtn: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center', marginLeft: 10 },
  finishBtn: { marginTop: 10, alignItems: 'center', padding: 5 },
  finishBtnText: { color: Colors.light.primary, fontWeight: '700' },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20
  },
  modalContent: {
    width: '100%',
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 25,
    alignItems: 'center',
    elevation: 5
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
    color: Colors.light.text
  },
  modalInput: {
    width: '100%',
    borderWidth: 1,
    borderColor: Colors.light.border,
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    marginBottom: 25,
    backgroundColor: Colors.light.card
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 15
  },
  modalBtn: {
    flex: 1,
    padding: 15,
    borderRadius: 12,
    alignItems: 'center'
  }
});