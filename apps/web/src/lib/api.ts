export type AlertSummary = {
  id: number;
  name: string;
  mode: string;
  active: boolean;
};

export async function listAlerts(apiBaseUrl: string, jwt: string): Promise<AlertSummary[]> {
  const response = await fetch(`${apiBaseUrl}/alerts`, {
    headers: {
      Authorization: `Bearer ${jwt}`
    }
  });
  if (!response.ok) {
    throw new Error("failed to fetch alerts");
  }
  return (await response.json()) as AlertSummary[];
}
