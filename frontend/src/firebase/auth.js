import {
  confirmPasswordReset,
  createUserWithEmailAndPassword,
  onIdTokenChanged as firebaseOnIdTokenChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
} from 'firebase/auth';
import { auth, firebaseConfigurationError, googleProvider } from './config';

function requireFirebaseAuth() {
  if (!auth) {
    throw new Error(firebaseConfigurationError || 'Firebase authentication is unavailable');
  }
  return auth;
}

export async function signup(email, password) {
  const credential = await createUserWithEmailAndPassword(requireFirebaseAuth(), email, password);
  await sendVerificationEmail(credential.user);
  return credential.user;
}

export async function login(email, password) {
  const credential = await signInWithEmailAndPassword(requireFirebaseAuth(), email, password);
  return credential.user;
}

export function logout() {
  if (!auth) return Promise.resolve();
  return signOut(auth);
}

export function forgotPassword(email) {
  return sendPasswordResetEmail(requireFirebaseAuth(), email);
}

export function resetPassword(oobCode, newPassword) {
  return confirmPasswordReset(requireFirebaseAuth(), oobCode, newPassword);
}

export function sendVerificationEmail(user = auth?.currentUser) {
  if (!user) {
    if (!auth) throw new Error(firebaseConfigurationError || 'Firebase authentication is unavailable');
    throw new Error('No authenticated user found');
  }
  return sendEmailVerification(user);
}

export async function googleLogin() {
  const credential = await signInWithPopup(
    requireFirebaseAuth(),
    googleProvider,
  );
  return credential.user;
}

export function getCurrentUser() {
  return auth?.currentUser || null;
}

export async function getToken(forceRefresh = false) {
  const user = auth?.currentUser;
  if (!user) return null;
  return user.getIdToken(forceRefresh);
}

export const getIdToken = getToken;

export function onIdTokenChanged(authInstance, callback) {
  if (!authInstance) return () => {};
  return firebaseOnIdTokenChanged(authInstance, callback);
}
