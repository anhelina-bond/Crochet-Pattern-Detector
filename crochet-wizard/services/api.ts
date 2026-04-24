// services/api.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabase } from './supabase';

export interface AnalysisResponse {
  success: boolean;
  graph_json: any;
  svg_data: string; // The symbolic chart
  image_url?: string; // Optional realistic render
  model_url?: string; // Optional 3D GLB
  message: string;
}

export const analyzeCrochetSwatch = async (
  imageUri: string, 
  yarnData: any,
  renderMode: string,
  userId: string
  ):Promise<any> => {
    const baseUrl = await AsyncStorage.getItem('backend_url') || 'http://10.87.157.236:8000';
    
    const formData = new FormData();
    
    // @ts-ignore
    formData.append('file', {
      uri: imageUri,
      name: 'swatch.jpg',
      type: 'image/jpeg',
    });
  
    formData.append('yarn_properties', JSON.stringify(yarnData));
    formData.append('output_mode', renderMode); 
    formData.append('user_id', userId); // <--- 2. Append it here
  
    const response = await fetch(`${baseUrl}/analyze`, {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json',
      },
    });
  
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Server error: ${response.status} - ${errorText}`);
    }
  
    return await response.json();
};

export const modifyPattern = async (
  prompt: string,
  currentGraph: any,
  yarnData: any,
  patternId: string,
  userId: string 
):  Promise<any> => {
  const baseUrl = await AsyncStorage.getItem('backend_url');

  const response = await fetch(`${baseUrl}/modify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: prompt,
      current_graph: currentGraph,
      yarn_properties: yarnData,
      pattern_id: patternId, // Sent to backend to update the correct DB row
      user_id: userId
    }),
  });

  if (!response.ok) throw new Error("Modification failed");
  return await response.json();
};

export const savePatternToLibrary = async (params: {
  patternId?: string; // 1. Added optional ID
  userId: string;
  name: string;
  graphData: any;
  svgData: string;
  imageUrl: string;
  yarnConfig: any;
  renderMode: string;
}) => {
  // 2. Build the payload
  const payload: any = {
    user_id: params.userId,
    name: params.name,
    graph_data: params.graphData,
    svg_data: params.svgData,
    image_url: params.imageUrl,
    yarn_config: params.yarnConfig,
    render_mode: params.renderMode,
  };

  // 3. If patternId exists, add it to the payload so Supabase knows to update
  if (params.patternId) {
    payload.id = params.patternId;
  }

  const { data, error } = await supabase
    .from('patterns')
    .upsert(payload, { onConflict: 'id' }) // 4. Tell Supabase to check 'id' column for conflicts
    .select();

  if (error) throw error;
  return data[0];
};