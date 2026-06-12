import { themeQuartz } from 'ag-grid-community';

export const myTheme = themeQuartz.withParams({
    backgroundColor: '#1c1c20',
    browserColorScheme: 'dark',
    chromeBackgroundColor: {
        ref: 'foregroundColor',
        mix: 0.07,
        onto: 'backgroundColor'
    },
    foregroundColor: '#FFF'
});
