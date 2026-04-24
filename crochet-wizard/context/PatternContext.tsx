import React, { createContext, useState, useContext } from 'react';

// 1. Update the Types
export type RenderMode = '2D' | '3D';

export type YarnData = {
  weight: number;
  color: string;
  fiber: 'cotton' | 'wool' | 'acrylic';
};

// Define what the context provides
interface PatternContextType {
  image: string | null;
  setImage: (uri: string | null) => void;
  yarnData: YarnData;
  setYarnData: (data: YarnData) => void;
  renderMode: RenderMode;          
  setRenderMode: (mode: RenderMode) => void; 
  results: any;
  setResults: (data: any) => void;
}

const PatternContext = createContext<PatternContextType | null>(null);

export const PatternProvider = ({ children }: { children: React.ReactNode }) => {
  const [image, setImage] = useState<string | null>(null);
  const [results, setResults] = useState(null);
  
  // 2. Add the state hook for renderMode
  const [renderMode, setRenderMode] = useState<RenderMode>('2D');

  const [yarnData, setYarnData] = useState<YarnData>({ 
    weight: 3, 
    color: '#52a4b5', 
    fiber: 'cotton' 
  });

  return (
    <PatternContext.Provider 
      value={{ 
        image, 
        setImage, 
        yarnData, 
        setYarnData, 
        renderMode,    // 3. EXPOSE THESE TO THE APP
        setRenderMode, // <--- This is what was missing
        results, 
        setResults 
      }}
    >
      {children}
    </PatternContext.Provider>
  );
};

export const usePattern = () => {
  const context = useContext(PatternContext);
  if (!context) {
    throw new Error('usePattern must be used within a PatternProvider');
  }
  return context;
};