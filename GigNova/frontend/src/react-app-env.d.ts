/// <reference types="react" />
/// <reference types="react-dom" />

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

interface ImportMeta {
  env: {
    VITE_API_URL: string;
    [key: string]: any;
  };
}
