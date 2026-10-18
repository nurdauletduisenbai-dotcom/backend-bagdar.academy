import { DecodedJwtPayload, JwtTokens, User } from '../types';

function toBase64Url(str: string): string {
  return btoa(unescape(encodeURIComponent(str)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function fromBase64Url(base64url: string): string {
  let base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  while (base64.length % 4) {
    base64 += '=';
  }
  return decodeURIComponent(escape(atob(base64)));
}

function generatePseudoSignature(input: string): string {
  // Simple deterministic hash simulation for UI visual inspection
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    hash = (hash << 5) - hash + input.charCodeAt(i);
    hash |= 0;
  }
  const hex = Math.abs(hash).toString(16).padStart(8, '0');
  return toBase64Url(`sig_${hex}_drf_simplejwt_secret`);
}

export function createJwtToken(
  user: User,
  tokenType: 'access' | 'refresh',
  expirySeconds: number
): { token: string; payload: DecodedJwtPayload; expiresAtMs: number } {
  const nowSec = Math.floor(Date.now() / 1000);
  const expSec = nowSec + expirySeconds;
  const jti = Math.random().toString(36).substring(2, 14);

  const header = {
    alg: 'HS256',
    typ: 'JWT',
  };

  const payload: DecodedJwtPayload = {
    token_type: tokenType,
    exp: expSec,
    iat: nowSec,
    jti: jti,
    user_id: user.id,
    email: user.email,
    username: user.username,
    role: user.role,
    is_verified: user.is_verified,
  };

  const encodedHeader = toBase64Url(JSON.stringify(header));
  const encodedPayload = toBase64Url(JSON.stringify(payload));
  const signature = generatePseudoSignature(`${encodedHeader}.${encodedPayload}`);

  const token = `${encodedHeader}.${encodedPayload}.${signature}`;

  return {
    token,
    payload,
    expiresAtMs: expSec * 1000,
  };
}

export function decodeJwt(tokenString: string): {
  header: any;
  payload: DecodedJwtPayload | null;
  signature: string;
  isExpired: boolean;
  isValidFormat: boolean;
} {
  try {
    const parts = tokenString.split('.');
    if (parts.length !== 3) {
      return { header: null, payload: null, signature: '', isExpired: true, isValidFormat: false };
    }

    const header = JSON.parse(fromBase64Url(parts[0]));
    const payload: DecodedJwtPayload = JSON.parse(fromBase64Url(parts[1]));
    const signature = parts[2];

    const nowSec = Math.floor(Date.now() / 1000);
    const isExpired = payload.exp ? payload.exp < nowSec : false;

    return {
      header,
      payload,
      signature,
      isExpired,
      isValidFormat: true,
    };
  } catch (err) {
    return { header: null, payload: null, signature: '', isExpired: true, isValidFormat: false };
  }
}
