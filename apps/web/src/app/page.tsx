import { AlertList } from "../components/AlertList";

export default function Home() {
  return (
    <main>
      <h1>StockAlarm</h1>
      <AlertList alerts={[]} />
    </main>
  );
}
