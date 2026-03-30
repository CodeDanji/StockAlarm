import React from "react";

export type AlertItem = {
  id: number;
  name: string;
  mode: string;
  active: boolean;
};

export function AlertList({ alerts }: { alerts: AlertItem[] }) {
  return (
    <ul>
      {alerts.map((alert) => (
        <li key={alert.id}>{alert.name}</li>
      ))}
    </ul>
  );
}
