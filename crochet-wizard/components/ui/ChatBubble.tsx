import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { Colors } from '@/constants/Colors';

const { width } = Dimensions.get('window');

interface ChatBubbleProps {
  text: string;
  isUser: boolean;
  type?: 'text' | 'system' | 'result';
}

export default function ChatBubble({ text, isUser, type = 'text' }: ChatBubbleProps) {
  const bubbleStyle = isUser ? styles.userBubble : styles.aiBubble;
  const textStyle = isUser ? styles.userText : styles.aiText;

  return (
    <View style={[styles.container, isUser ? styles.userContainer : styles.aiContainer]}>
      <View style={[styles.bubble, bubbleStyle]}>
        <Text style={textStyle}>{text}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
    flexDirection: 'row',
    width: '100%',
  },
  userContainer: { justifyContent: 'flex-end' },
  aiContainer: { justifyContent: 'flex-start' },
  bubble: {
    padding: 12,
    borderRadius: 18,
    maxWidth: width * 0.75,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
  },
  userBubble: {
    backgroundColor: Colors.light.primary, // Pacific Blue
    borderBottomRightRadius: 2,
  },
  aiBubble: {
    backgroundColor: '#fff',
    borderBottomLeftRadius: 2,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  userText: {
    color: '#fff',
    fontSize: 15,
  },
  aiText: {
    color: Colors.light.text, // Graphite
    fontSize: 15,
  },
});