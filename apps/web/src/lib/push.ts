export async function registerPushToken(
  apiBaseUrl: string,
  token: string,
  jwt: string
): Promise<{ id: number; fcm_token: string }> {
  const response = await fetch(`${apiBaseUrl}/devices/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${jwt}`
    },
    body: JSON.stringify({ fcm_token: token, platform: "web" })
  });

  if (!response.ok) {
    throw new Error("failed to register push token");
  }

  return (await response.json()) as { id: number; fcm_token: string };
}
