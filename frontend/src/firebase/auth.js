import {
  confirmPasswordReset,
  createUserWithEmailAndPassword,
  onIdTokenChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
} from 'firebase/auth';
import { auth, googleProvider } from './config';

export async function signup(email, password) {
  const credential = await createUserWithEmailAndPassword(auth, email, password);
  await sendVerificationEmail(credential.user);
  return credential.user;
}

export async function login(email, password) {
  const credential = await signInWithEmailAndPassword(auth, email, password);
  return credential.user;
}

export function logout() {
  return signOut(auth);
}

export function forgotPassword(email) {
  return sendPasswordResetEmail(auth, email);
}

export function resetPassword(oobCode, newPassword) {
  return confirmPasswordReset(auth, oobCode, newPassword);
}

export function sendVerificationEmail(user = auth.currentUser) {
  if (!user) throw new Error('No authenticated user found');
  return sendEmailVerification(user);
}

export async function googleLogin() {
  const credential = await signInWithPopup(auth, googleProvider);
  return credential.user;
}

export function getCurrentUser() {
  return auth.currentUser;
}

export async function getToken(forceRefresh = false) {
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken(forceRefresh);
}

export const getIdToken = getToken;

export { onIdTokenChanged };