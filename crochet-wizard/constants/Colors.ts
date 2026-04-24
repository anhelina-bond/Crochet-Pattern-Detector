// constants/Colors.ts

// Defining the raw palette as constants for easy reference
const palette = {
    graphite: '#3a3335',      // Main text / Dark background
    powderPetal: '#e5cfc1',   // Light background / Soft text
    pacificBlue: '#52a4b5',   // Primary Action color
    greenYellow: '#a7f063',   // Success / Valid topology
    scarletRush: '#db2b39',   // Error / Broken connection
  };
  
  const tintColorLight = palette.pacificBlue;
  const tintColorDark = palette.powderPetal;
  
  export const Colors = {
    light: {
      primary: palette.pacificBlue,
      secondary: '#7cb9c6',           // Slightly lighter Pacific Blue
      background: palette.powderPetal,
      card: '#f4e9e2',                // Slightly lighter than Powder Petal for depth
      text: palette.graphite,
      border: '#dcc3b4',              // Darker shade of Powder Petal
      error: palette.scarletRush,
      success: palette.greenYellow,
      tint: tintColorLight,
      tabIconDefault: '#9a8e85',
      tabIconSelected: tintColorLight,
    },
    dark: {
      primary: palette.pacificBlue,
      secondary: '#346a75',           // Darker Pacific Blue
      background: palette.graphite,
      card: '#2b2627',                // Slightly lighter than Graphite
      text: palette.powderPetal,
      border: '#4e4547',              // Slightly lighter than Graphite
      error: palette.scarletRush,
      success: palette.greenYellow,
      tint: tintColorDark,
      tabIconDefault: '#6b5e61',
      tabIconSelected: tintColorDark,
    },
  };