import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const requiredFirebaseKeys = [
  'apiKey',
  'authDomain',
  'projectId',
  'storageBucket',
  'messagingSenderId',
  'appId',
];

const missingFirebaseKeys = requiredFirebaseKeys.filter((key) => !firebaseConfig[key]);

export const isFirebaseConfigured = missingFirebaseKeys.length === 0;
export const firebaseConfigurationError = isFirebaseConfigured
  ? null
  : `Firebase is not configured. Missing ${missingFirebaseKeys
      .map(
        (key) =>
          `VITE_FIREBASE_${key.replace(/[A-Z]/g, (letter) => `_${letter}`).toUpperCase()}`,
      )
      .join(', ')}.`;

// Do not call getAuth with an incomplete config. Firebase throws during module
// initialization in that case, which prevents the entire React app from
// mounting and leaves the page blank.
let app = null;
let auth = null;
let googleProvider = null;

if (isFirebaseConfigured) {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  googleProvider = new GoogleAuthProvider();
}

export { app, auth, googleProvider };
export default app;
