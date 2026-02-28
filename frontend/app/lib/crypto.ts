/**
 * Cryptographic utilities for payload generation
 */

export async function generateCryptoHash(
  orderId: string,
  timestamp: number,
  deviceId: string,
  secretSalt: string
): Promise<string> {
  const payload = `${orderId}|${timestamp}|${deviceId}|${secretSalt}`;
  const encoder = new TextEncoder();
  const data = encoder.encode(payload);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
}
